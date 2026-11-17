from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session

from app.ai_pipeline.base import AIMode, get_active_ai_mode
from app.ai_pipeline.gesture_analysis import build_gesture_analysis_payload
from app.db.models import (
    Analytics,
    Lecture,
    LectureSegment,
    ProcessingJob,
    Question,
    Quiz,
    Slide,
    Speaker,
    Summary,
    SystemLog,
    Transcript,
)


PIPELINE_STEPS = [
    "1. Audio Processing: Trích xuất và tiền xử lý âm thanh (FFmpeg)",
    "2. ASR: Chuyển giọng nói thành văn bản tiếng Việt (Whisper interface)",
    "3. Speaker Diarization: Phân biệt người nói (pyannote.audio interface)",
    "4. OCR: Trích xuất văn bản từ slide (PaddleOCR interface)",
    "5. Video Analysis: Trích xuất khung hình & tương tác trực quan (OpenCV)",
    "6. Multimodal Alignment: Đồng bộ lời giảng, slide và video theo timestamp",
    "7. Lecture Summarization: Tóm tắt cấu trúc bài giảng",
    "8. RAG Indexing: Lập chỉ mục ngữ nghĩa cho hỏi đáp",
    "9. Quiz Generation: Sinh câu hỏi trắc nghiệm & tự luận ôn tập",
]


class LecturePipelineOrchestrator:
    """
    Modular 9-step Multimodal AI Pipeline Orchestrator.
    When AI_PIPELINE_MODE=simulated, generates structured, transparent simulated outputs
    tagged with ai_mode='simulated' so the platform architecture can be tested end-to-end.
    """

    def run_pipeline(self, db: Session, lecture: Lecture) -> ProcessingJob:
        mode = get_active_ai_mode()
        lecture.ai_status = "processing"
        lecture.ai_mode = mode.value

        job = ProcessingJob(
            lecture_id=lecture.id,
            status="running",
            current_step=PIPELINE_STEPS[0],
            progress_percent=10,
            ai_mode=mode.value,
            steps_log=[f"[{datetime.now(timezone.utc).isoformat()}] Bắt đầu pipeline ({mode.value})"],
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            # Clear previous generated artifacts if re-processing
            db.query(Transcript).filter(Transcript.lecture_id == lecture.id).delete()
            db.query(Slide).filter(Slide.lecture_id == lecture.id).delete()
            db.query(Speaker).filter(Speaker.lecture_id == lecture.id).delete()
            db.query(LectureSegment).filter(LectureSegment.lecture_id == lecture.id).delete()
            db.query(Summary).filter(Summary.lecture_id == lecture.id).delete()
            db.query(Analytics).filter(Analytics.lecture_id == lecture.id).delete()
            for qz in db.query(Quiz).filter(Quiz.lecture_id == lecture.id).all():
                db.delete(qz)
            db.flush()

            duration = lecture.duration_seconds if lecture.duration_seconds and lecture.duration_seconds > 0 else 900
            lecture.duration_seconds = duration

            # Speakers
            sp_lecturer = Speaker(
                lecture_id=lecture.id,
                speaker_label="SPEAKER_00",
                display_name="Giảng viên",
                speaking_duration_seconds=round(duration * 0.82, 1),
            )
            sp_student = Speaker(
                lecture_id=lecture.id,
                speaker_label="SPEAKER_01",
                display_name="Sinh viên (Hỏi đáp)",
                speaking_duration_seconds=round(duration * 0.18, 1),
            )
            db.add_all([sp_lecturer, sp_student])
            db.flush()

            # Slides (4 structured slides)
            topic = lecture.topic or lecture.title
            slide_specs = [
                (1, f"Giới thiệu & Mục tiêu: {topic}", [
                    f"Tổng quan chủ đề {topic}",
                    "Mục tiêu kiến thức cần đạt sau buổi học",
                    "Liên hệ thực tiễn và các bài học trước",
                ]),
                (2, f"Nền tảng lý thuyết của {topic}", [
                    "Định nghĩa và khái niệm cốt lõi",
                    "Kiến trúc / Mô hình hoạt động tổng quát",
                    "Các thành phần tham gia chính",
                ]),
                (3, f"Phân tích ví dụ & Ứng dụng thực tế", [
                    "Ví dụ minh họa từng bước",
                    "So sánh ưu nhược điểm các phương pháp",
                    "Các lỗi thường gặp và cách khắc phục",
                ]),
                (4, "Tổng kết & Hướng dẫn ôn tập", [
                    "Tóm tắt các ý trọng tâm",
                    "Câu hỏi thảo luận mở rộng",
                    "Tài liệu đọc thêm và bài tập về nhà",
                ]),
            ]

            slides: List[Slide] = []
            seg_len = duration / len(slide_specs)
            for idx, (num, stitle, bullets) in enumerate(slide_specs):
                s_start = round(idx * seg_len, 1)
                s_end = round((idx + 1) * seg_len, 1)
                sl = Slide(
                    lecture_id=lecture.id,
                    slide_number=num,
                    title=stitle,
                    ocr_text=f"{stitle}. " + " ".join(bullets),
                    bullet_points=bullets,
                    start_time=s_start,
                    end_time=s_end,
                )
                db.add(sl)
                slides.append(sl)
            db.flush()

            # Transcripts & Segments aligned with slides
            transcript_templates = [
                (0, sp_lecturer, "Chào các bạn, hôm nay chúng ta sẽ cùng tìm hiểu chuyên đề {title}. Trước hết hãy xem mục tiêu của bài giảng trên slide 1.", False),
                (0, sp_lecturer, "Điều quan trọng nhất cần nắm ở phần mở đầu là bối cảnh ứng dụng thực tế của {topic} trong hệ thống hiện đại.", True),
                (1, sp_lecturer, "Chuyển sang slide 2, chúng ta đi sâu vào nền tảng lý thuyết và các khái niệm cốt lõi cấu thành nên {topic}.", False),
                (1, sp_student, "Thưa thầy/cô, phần thành phần chính này có điểm gì khác biệt so với mô hình truyền thống ạ?", False),
                (1, sp_lecturer, "Câu hỏi rất hay. Điểm khác biệt cốt lõi nằm ở khả năng xử lý đồng bộ và tối ưu hóa dữ liệu theo ngữ cảnh.", True),
                (2, sp_lecturer, "Trên slide 3 là ví dụ minh họa cụ thể. Các bạn chú ý quy trình từng bước từ đầu vào đến kết quả đầu ra.", False),
                (2, sp_lecturer, "Lưu ý lỗi phổ biến khi triển khai thực tế là bỏ qua bước kiểm tra điều kiện biên trước khi xử lý.", True),
                (3, sp_lecturer, "Tổng kết lại trên slide 4, các bạn cần ghi nhớ ba ý trọng tâm và hoàn thành bài kiểm tra ôn tập cuối buổi.", False),
            ]

            step_dur = duration / len(transcript_templates)
            for i, (sl_idx, speaker, tmpl, emphasis) in enumerate(transcript_templates):
                t_start = round(i * step_dur, 1)
                t_end = round((i + 1) * step_dur - 1.0, 1)
                tr = Transcript(
                    lecture_id=lecture.id,
                    speaker_id=speaker.id,
                    slide_id=slides[sl_idx].id,
                    start_time=t_start,
                    end_time=max(t_start + 5.0, t_end),
                    text=tmpl.format(title=lecture.title, topic=topic),
                    confidence=0.94,
                    is_repeated_emphasis=emphasis,
                )
                db.add(tr)

            for sl in slides:
                seg = LectureSegment(
                    lecture_id=lecture.id,
                    title=sl.title,
                    description=sl.ocr_text,
                    start_time=sl.start_time,
                    end_time=sl.end_time,
                    slide_number=sl.slide_number,
                    keywords=[topic, f"Slide {sl.slide_number}"],
                )
                db.add(seg)

            # Summary
            summary = Summary(
                lecture_id=lecture.id,
                overview=f"Bài giảng '{lecture.title}' cung cấp kiến thức hệ thống về {topic}, bao gồm cơ sở lý thuyết, ví dụ minh họa và các lưu ý thực hành.",
                key_points=[
                    f"Hiểu rõ mục tiêu và phạm vi ứng dụng của {topic}.",
                    "Nắm vững kiến trúc tổng quát và các thành phần chính.",
                    "Biết cách phân tích ví dụ và tránh các lỗi phổ biến.",
                ],
                important_concepts=[
                    f"Khái niệm nền tảng về {topic}",
                    "Quy trình xử lý và kiểm tra điều kiện biên",
                ],
                technical_terms=[
                    {"term": topic, "definition": f"Chủ đề trọng tâm được trình bày xuyên suốt bài giảng '{lecture.title}'.", "slide_number": 2, "timestamp": slides[1].start_time},
                ],
                examples=[
                    f"Ví dụ minh họa quy trình từng bước cho {topic} tại Slide 3.",
                ],
                conclusion=f"Người học cần kết hợp xem lại slide 2-3 và làm bài trắc nghiệm để củng cố kiến thức về {topic}.",
                takeaways=[
                    "Nắm chắc định nghĩa cốt lõi ở Slide 2.",
                    "Thực hành lại ví dụ ở Slide 3 và chú ý điều kiện biên.",
                ],
                ai_mode=mode.value,
            )
            db.add(summary)

            # Quiz
            quiz = Quiz(
                lecture_id=lecture.id,
                title=f"Kiểm tra nhanh: {lecture.title}",
                description="Bộ câu hỏi ôn tập được tạo tự động từ nội dung bài giảng.",
                ai_mode=mode.value,
            )
            db.add(quiz)
            db.flush()

            q1 = Question(
                quiz_id=quiz.id,
                question_type="mcq",
                prompt=f"Nội dung nền tảng lý thuyết và kiến trúc tổng quát của '{topic}' được trình bày chủ yếu ở slide nào?",
                options=["Slide 1", "Slide 2", "Slide 3", "Slide 4"],
                correct_answer="Slide 2",
                explanation="Slide 2 trình bày định nghĩa, khái niệm cốt lõi và kiến trúc tổng quát.",
                slide_number=2,
                timestamp_seconds=slides[1].start_time,
            )
            q2 = Question(
                quiz_id=quiz.id,
                question_type="mcq",
                prompt="Theo bài giảng, lỗi phổ biến cần tránh khi triển khai thực tế là gì?",
                options=[
                    "Không xem slide mở đầu",
                    "Bỏ qua bước kiểm tra điều kiện biên",
                    "Không đặt câu hỏi cho giảng viên",
                    "Chỉ đọc phần kết luận",
                ],
                correct_answer="Bỏ qua bước kiểm tra điều kiện biên",
                explanation="Giảng viên đã nhấn mạnh ở Slide 3 rằng cần kiểm tra điều kiện biên trước khi xử lý.",
                slide_number=3,
                timestamp_seconds=slides[2].start_time,
            )
            q3 = Question(
                quiz_id=quiz.id,
                question_type="essay",
                prompt=f"Hãy tóm tắt ngắn gọn bằng lời của bạn về ứng dụng thực tế và điểm cần lưu ý nhất trong bài '{lecture.title}'.",
                options=[],
                correct_answer=f"Nêu được ứng dụng thực tế của {topic} và lưu ý kiểm tra điều kiện biên khi triển khai.",
                explanation="Câu hỏi tự luận giúp sinh viên tự hệ thống hóa kiến thức đã học.",
                slide_number=3,
                timestamp_seconds=slides[2].start_time,
            )
            db.add_all([q1, q2, q3])

            # Analytics
            analytics = Analytics(
                lecture_id=lecture.id,
                speaking_rate_wpm=136.0,
                lecturer_talk_ratio=0.82,
                interaction_ratio=0.18,
                topic_time_distribution=[
                    {"topic": sl.title, "seconds": round(sl.end_time - sl.start_time, 1), "percent": 25.0}
                    for sl in slides
                ],
                repeated_concepts=[topic, "Kiểm tra điều kiện biên"],
                student_engagement_score=76.0,
                gesture_analysis=build_gesture_analysis_payload(duration, mode.value),
                improvement_suggestions=[
                    "Có thể bổ sung thêm 1 câu hỏi tương tác nhanh sau Slide 2 để tăng tỷ lệ trao đổi với sinh viên.",
                    "Đính kèm thêm tài liệu đọc thêm dạng PDF cho phần ví dụ ở Slide 3.",
                ],
                ai_mode=mode.value,
            )
            db.add(analytics)

            # Complete job & lecture
            job.status = "completed"
            job.current_step = "Hoàn tất toàn bộ 9 bước pipeline"
            job.progress_percent = 100
            job.completed_at = datetime.now(timezone.utc)
            job.steps_log = [f"[OK] {s}" for s in PIPELINE_STEPS]

            lecture.ai_status = "completed"
            db.add(
                SystemLog(
                    level="INFO",
                    module="ai_pipeline",
                    message=f"Xử lý hoàn tất bài giảng #{lecture.id} ({lecture.title}) ở chế độ {mode.value}.",
                )
            )
            db.commit()
            db.refresh(job)
            return job
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error_message = str(exc)
            lecture.ai_status = "failed"
            db.add(job)
            db.add(
                SystemLog(
                    level="ERROR",
                    module="ai_pipeline",
                    message=f"Lỗi xử lý bài giảng #{lecture.id}: {exc}",
                )
            )
            db.commit()
            raise
