from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.ai_pipeline.gesture_analysis import build_gesture_analysis_payload
from app.core.security import hash_password
from app.db.models import (
    Analytics,
    Course,
    CourseClass,
    Department,
    Enrollment,
    LearningProgress,
    Lecture,
    LectureSegment,
    ProcessingJob,
    Question,
    Quiz,
    QuizAttempt,
    Role,
    Slide,
    Speaker,
    Summary,
    SystemLog,
    Transcript,
    User,
)


def seed_database(db: Session) -> None:
    if db.query(Role).first():
        return  # Already seeded

    now = datetime.now(timezone.utc)

    # 1. Roles
    r_student = Role(name="student", display_name="Sinh viên", description="Học tập, xem bài giảng, hỏi đáp AI và làm bài ôn tập")
    r_lecturer = Role(name="lecturer", display_name="Giảng viên", description="Tải lên, quản lý bài giảng và xem phân tích giảng dạy")
    r_admin = Role(name="admin", display_name="Nhà trường / Quản trị", description="Quản lý người dùng, đào tạo và giám sát toàn hệ thống")
    db.add_all([r_student, r_lecturer, r_admin])
    db.flush()

    # 2. Departments
    dept_cntt = Department(code="CNTT", name="Khoa Công nghệ Thông tin", description="Đào tạo Kỹ thuật phần mềm, Hệ thống phân tán và Kiến trúc hệ thống")
    dept_ai = Department(code="AI-DS", name="Khoa Trí tuệ Nhân tạo & Khoa học Dữ liệu", description="Đào tạo Học máy, Xử lý ngôn ngữ tự nhiên và Thị giác máy tính")
    db.add_all([dept_cntt, dept_ai])
    db.flush()

    # 3. Users
    u_student1 = User(
        email="student@lectureai.edu.vn",
        full_name="Nguyễn Minh Anh",
        hashed_password=hash_password("Student@123"),
        role_id=r_student.id,
        department_id=dept_ai.id,
        student_code="SV2026001",
        is_active=True,
        last_login_at=now - timedelta(hours=2),
    )
    u_student2 = User(
        email="student2@lectureai.edu.vn",
        full_name="Trần Quốc Bảo",
        hashed_password=hash_password("Student@123"),
        role_id=r_student.id,
        department_id=dept_cntt.id,
        student_code="SV2026002",
        is_active=True,
        last_login_at=now - timedelta(days=1),
    )
    u_lecturer1 = User(
        email="lecturer@lectureai.edu.vn",
        full_name="TS. Lê Hoàng Nam",
        hashed_password=hash_password("Lecturer@123"),
        role_id=r_lecturer.id,
        department_id=dept_ai.id,
        is_active=True,
        last_login_at=now - timedelta(hours=1),
    )
    u_lecturer2 = User(
        email="lecturer2@lectureai.edu.vn",
        full_name="ThS. Phạm Thu Hà",
        hashed_password=hash_password("Lecturer@123"),
        role_id=r_lecturer.id,
        department_id=dept_cntt.id,
        is_active=True,
        last_login_at=now - timedelta(hours=5),
    )
    u_admin = User(
        email="admin@lectureai.edu.vn",
        full_name="Quản trị viên Nhà trường",
        hashed_password=hash_password("Admin@123"),
        role_id=r_admin.id,
        department_id=dept_cntt.id,
        is_active=True,
        last_login_at=now,
    )
    db.add_all([u_student1, u_student2, u_lecturer1, u_lecturer2, u_admin])
    db.flush()

    # 4. Courses & Classes
    c_nlp = Course(
        code="AI301",
        title="Xử lý Ngôn ngữ Tự nhiên & LLM",
        description="Kiến trúc Transformer, Attention, mô hình ngôn ngữ lớn và ứng dụng RAG.",
        credits=3,
        semester="HK1 2026-2027",
        department_id=dept_ai.id,
        lecturer_id=u_lecturer1.id,
    )
    c_speech = Course(
        code="AI305",
        title="Xử lý Tiếng nói & Tín hiệu Đa phương thức",
        description="ASR tiếng Việt, tách người nói (Diarization) và đồng bộ đa phương thức.",
        credits=3,
        semester="HK1 2026-2027",
        department_id=dept_ai.id,
        lecturer_id=u_lecturer1.id,
    )
    c_dist = Course(
        code="IT402",
        title="Hệ thống Phân tán & Kiến trúc Microservices",
        description="Thiết kế hệ thống chịu lỗi, nhất quán dữ liệu và hàng đợi bất đồng bộ.",
        credits=4,
        semester="HK1 2026-2027",
        department_id=dept_cntt.id,
        lecturer_id=u_lecturer2.id,
    )
    db.add_all([c_nlp, c_speech, c_dist])
    db.flush()

    cls_nlp = CourseClass(name="AI301.01 - K68", code="AI301-01", semester="HK1 2026-2027", schedule="Thứ 2, 08:00 - 10:30", course_id=c_nlp.id)
    cls_speech = CourseClass(name="AI305.01 - K68", code="AI305-01", semester="HK1 2026-2027", schedule="Thứ 4, 13:30 - 16:00", course_id=c_speech.id)
    cls_dist = CourseClass(name="IT402.01 - K68", code="IT402-01", semester="HK1 2026-2027", schedule="Thứ 6, 09:00 - 11:30", course_id=c_dist.id)
    db.add_all([cls_nlp, cls_speech, cls_dist])
    db.flush()

    # Enrollments: student1 in all 3 courses, student2 in IT402 & AI301
    db.add_all([
        Enrollment(student_id=u_student1.id, class_id=cls_nlp.id),
        Enrollment(student_id=u_student1.id, class_id=cls_speech.id),
        Enrollment(student_id=u_student1.id, class_id=cls_dist.id),
        Enrollment(student_id=u_student2.id, class_id=cls_nlp.id),
        Enrollment(student_id=u_student2.id, class_id=cls_dist.id),
    ])
    db.flush()

    # 5. Detailed Seed Lectures
    lectures_spec = [
        {
            "title": "Bài 1: Kiến trúc Transformer & Cơ chế Self-Attention",
            "description": "Phân tích chi tiết cơ chế Scaled Dot-Product Attention, Multi-Head Attention và Positional Encoding.",
            "topic": "Transformer & Attention",
            "course": c_nlp,
            "lecturer": u_lecturer1,
            "duration": 1800,
            "views": 42,
            "slides": [
                (1, "Hạn chế của RNN/LSTM & Động lực ra đời Transformer", "Xử lý tuần tự khó song song hóa; suy giảm thông tin với chuỗi dài (long-range dependency).", ["RNN xử lý tuần tự O(n)", "Khó tận dụng GPU song song", "Mất ngữ cảnh xa"], 0, 360),
                (2, "Cơ chế Scaled Dot-Product Attention", "Công thức Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V giúp mô hình tập trung vào token liên quan.", ["Query, Key, Value vectors", "Chia cho sqrt(d_k) tránh bão hòa softmax", "Trọng số chú ý theo ngữ cảnh"], 360, 840),
                (3, "Multi-Head Attention & Positional Encoding", "Kết hợp nhiều không gian biểu diễn song song và mã hóa vị trí bằng hàm sin/cos.", ["Nhiều head học nhiều quan hệ ngữ nghĩa", "Positional Encoding bù đắp thiếu thứ tự", "Residual Connection & LayerNorm"], 840, 1380),
                (4, "Ứng dụng thực tế & Tổng kết bài học", "Encoder-only (BERT), Decoder-only (GPT) và Encoder-Decoder (T5).", ["Phân loại kiến trúc LLM", "Bài tập tự luận & trắc nghiệm"], 1380, 1800),
            ],
            "transcripts": [
                (0, "lecturer", 10, 120, "Chào các bạn. Hôm nay chúng ta bắt đầu chương quan trọng nhất của môn học: Kiến trúc Transformer. Trước khi đi vào chi tiết, hãy nhìn lên slide 1 để thấy vì sao RNN và LSTM gặp giới hạn khi xử lý văn bản dài.", False),
                (0, "lecturer", 125, 340, "Với RNN, từ thứ 100 phải chờ 99 từ trước tính xong mới xử lý được. Điều này làm mất khả năng song song hóa trên GPU.", True),
                (1, "lecturer", 365, 590, "Trên slide 2 là công thức cốt lõi: Scaled Dot-Product Attention. Mỗi từ được ánh xạ thành ba vector Query, Key và Value.", False),
                (1, "student", 595, 650, "Thưa thầy, tại sao mình phải chia cho căn bậc hai của d_k trước khi đưa qua hàm softmax ạ?", False),
                (1, "lecturer", 655, 830, "Câu hỏi rất hay! Khi chiều d_k lớn, tích vô hướng QK^T có phương sai lớn, khiến softmax rơi vào vùng gradient cực nhỏ. Chia cho căn bậc hai của d_k giúp ổn định quá trình lan truyền ngược.", True),
                (2, "lecturer", 845, 1180, "Sang slide 3, Multi-Head Attention cho phép mô hình đồng thời chú ý đến nhiều khía cạnh: head 1 theo dõi chủ ngữ, head 2 theo dõi quan hệ thời gian.", False),
                (2, "lecturer", 1190, 1370, "Vì Transformer không có vòng lặp tuần tự, chúng ta bắt buộc phải cộng thêm Positional Encoding để mô hình biết vị trí tương đối giữa các từ.", True),
                (3, "lecturer", 1390, 1780, "Cuối cùng trên slide 4, các bạn nhớ phân biệt 3 nhánh: BERT dùng Encoder, GPT dùng Decoder. Hãy làm quiz ôn tập ngay sau buổi học nhé.", False),
            ],
            "terms": [
                {"term": "Self-Attention", "definition": "Cơ chế cho phép mỗi token trong chuỗi tính mức độ liên quan với tất cả token khác trong cùng chuỗi.", "slide_number": 2, "timestamp": 365},
                {"term": "Scaled Dot-Product", "definition": "Phép nhân tích vô hướng QK^T chia cho sqrt(d_k) để tránh bão hòa hàm softmax.", "slide_number": 2, "timestamp": 655},
                {"term": "Positional Encoding", "definition": "Vector mã hóa vị trí của token được cộng vào embedding đầu vào.", "slide_number": 3, "timestamp": 1190},
            ],
            "quiz_questions": [
                ("mcq", "Mục đích của việc chia tích vô hướng QK^T cho sqrt(d_k) trong Scaled Dot-Product Attention là gì?", ["Tăng tốc độ đọc file", "Tránh hàm softmax rơi vào vùng bão hòa gradient nhỏ", "Giảm số lượng tham số xuống 0", "Thay thế Positional Encoding"], "Tránh hàm softmax rơi vào vùng bão hòa gradient nhỏ", "Khi d_k lớn, tích vô hướng có phương sai lớn làm softmax bão hòa; chia cho sqrt(d_k) giúp ổn định gradient.", 2, 655),
                ("mcq", "Thành phần nào giúp Transformer nhận biết thứ tự các từ trong câu khi không dùng mạng hồi quy?", ["LayerNorm", "Dropout", "Positional Encoding", "Softmax"], "Positional Encoding", "Positional Encoding bổ sung thông tin vị trí vào embedding đầu vào (Slide 3).", 3, 1190),
                ("essay", "Giải thích ngắn gọn lý do Transformer song song hóa tốt hơn RNN/LSTM.", [], "Transformer tính toán attention cho toàn bộ chuỗi đồng thời qua phép nhân ma trận thay vì xử lý tuần tự từng bước thời gian như RNN.", "Dựa trên Slide 1 và phần giảng mở đầu.", 1, 125),
            ],
        },
        {
            "title": "Bài 2: Hệ thống RAG & Tìm kiếm Ngữ nghĩa cho Giáo dục",
            "description": "Xây dựng pipeline Retrieval-Augmented Generation, Chunking, Embedding và trích dẫn nguồn slide/timestamp.",
            "topic": "RAG & Vector Search",
            "course": c_nlp,
            "lecturer": u_lecturer1,
            "duration": 1500,
            "views": 35,
            "slides": [
                (1, "Vấn đề ảo giác (Hallucination) của LLM thuần túy", "LLM có thể tự tin trả lời sai khi thiếu tri thức chuyên ngành hoặc tài liệu nội bộ.", ["Giới hạn tri thức đóng", "Không có nguồn trích dẫn", "Rủi ro sai lệch trong giáo dục"], 0, 350),
                (2, "Kiến trúc RAG: Indexing, Retrieval & Generation", "Chia nhỏ tài liệu (Chunking), tạo Embedding, lưu Vector DB và truy xuất top-k đoạn liên quan.", ["Chunking theo ngữ nghĩa & timestamp", "Embedding đa ngôn ngữ", "Cosine Similarity"], 350, 900),
                (3, "Trích dẫn nguồn đa phương thức (Slide & Timestamp)", "Gắn metadata số slide và mốc thời gian video vào từng vector chunk.", ["Metadata filtering", "Liên kết câu trả lời với slide", "Tăng độ tin cậy học tập"], 900, 1500),
            ],
            "transcripts": [
                (0, "lecturer", 15, 320, "Trong bài học hôm nay, chúng ta giải quyết bài toán cốt lõi của AI trong giáo dục: làm sao để trợ lý ảo trả lời đúng nội dung bài giảng và không bịa đặt thông tin.", False),
                (1, "lecturer", 360, 720, "Slide 2 minh họa kiến trúc RAG gồm hai pha: pha lập chỉ mục ngoại tuyến và pha truy xuất trực tuyến khi sinh viên đặt câu hỏi.", True),
                (1, "student", 730, 790, "Thưa thầy, kích thước chunk bao nhiêu là hợp lý cho transcript bài giảng ạ?", False),
                (1, "lecturer", 795, 890, "Thông thường khoảng 250 đến 400 token có overlap 15%, và quan trọng nhất là giữ nguyên metadata start_time và slide_number.", True),
                (2, "lecturer", 910, 1450, "Ở slide 3, nhờ lưu kèm metadata slide và timestamp, hệ thống có thể hiển thị nút bấm nhảy thẳng tới đúng giây giảng viên giải thích.", False),
            ],
            "terms": [
                {"term": "RAG (Retrieval-Augmented Generation)", "definition": "Kỹ thuật kết hợp truy xuất tài liệu liên quan trước khi đưa vào LLM sinh câu trả lời.", "slide_number": 2, "timestamp": 360},
                {"term": "Hallucination", "definition": "Hiện tượng mô hình ngôn ngữ sinh ra thông tin sai sự thật nhưng diễn đạt tự tin.", "slide_number": 1, "timestamp": 15},
            ],
            "quiz_questions": [
                ("mcq", "Metadata nào quan trọng nhất khi lập chỉ mục transcript bài giảng cho RAG đa phương thức?", ["Màu nền của trình duyệt", "start_time và slide_number", "Kích thước màn hình", "Tên hệ điều hành"], "start_time và slide_number", "Giúp liên kết câu trả lời của AI tới đúng slide và mốc thời gian video (Slide 2-3).", 3, 910),
                ("mcq", "RAG giúp giảm thiểu vấn đề nào của LLM thuần túy?", ["Ảo giác thông tin (Hallucination)", "Tốc độ gõ phím", "Độ phân giải màn hình", "Dung lượng ổ cứng"], "Ảo giác thông tin (Hallucination)", "RAG neo câu trả lời vào ngữ cảnh tài liệu được truy xuất thực tế (Slide 1).", 1, 15),
            ],
        },
        {
            "title": "Bài 3: Nhận dạng Giọng nói Tiếng Việt (ASR) & Speaker Diarization",
            "description": "Quy trình tiền xử lý âm thanh, mô hình Whisper, tách người nói pyannote.audio và đánh giá WER.",
            "topic": "ASR & Diarization",
            "course": c_speech,
            "lecturer": u_lecturer1,
            "duration": 1620,
            "views": 24,
            "slides": [
                (1, "Tiền xử lý âm thanh với FFmpeg", "Chuẩn hóa tần số lấy mẫu 16kHz mono, lọc nhiễu nền và chuẩn hóa âm lượng.", ["16kHz Mono PCM", "Voice Activity Detection (VAD)", "Giảm nhiễu phòng học"], 0, 500),
                (2, "Mô hình Whisper & Đặc thù Tiếng Việt", "Kiến trúc Encoder-Decoder đa ngôn ngữ, xử lý thanh điệu và thuật ngữ chuyên ngành.", ["6 thanh điệu tiếng Việt", "Word Error Rate (WER)", "Prompting thuật ngữ"], 500, 1100),
                (3, "Speaker Diarization với pyannote.audio", "Phân biệt ai nói lúc nào (SPEAKER_00 vs SPEAKER_01) phục vụ thống kê tương tác.", ["Speaker Embeddings", "Clustering theo thời gian", "Tính tỷ lệ tương tác lớp học"], 1100, 1620),
            ],
            "transcripts": [
                (0, "lecturer", 20, 480, "Để ASR đạt độ chính xác cao, bước đầu tiên ở slide 1 là chuẩn hóa âm thanh đầu vào về 16kHz đơn kênh bằng FFmpeg.", False),
                (1, "lecturer", 510, 1050, "Tiếng Việt có 6 thanh điệu và nhiều từ mượn tiếng Anh trong môn CNTT, nên chỉ số WER cần được đo cẩn thận trên tập dữ liệu giảng đường.", True),
                (2, "lecturer", 1110, 1580, "Speaker Diarization trên slide 3 giúp tách lời giảng viên và câu hỏi của sinh viên, từ đó đo được tỷ lệ trao đổi trong buổi học.", False),
            ],
            "terms": [
                {"term": "WER (Word Error Rate)", "definition": "Tỷ lệ lỗi từ dùng để đánh giá độ chính xác của hệ thống nhận dạng giọng nói.", "slide_number": 2, "timestamp": 510},
                {"term": "Speaker Diarization", "definition": "Bài toán xác định 'ai đang nói tại thời điểm nào' trong đoạn âm thanh.", "slide_number": 3, "timestamp": 1110},
            ],
            "quiz_questions": [
                ("mcq", "Chỉ số tiêu chuẩn thường dùng để đánh giá độ chính xác của hệ thống ASR là gì?", ["FPS", "WER (Word Error Rate)", "DPI", "RAM"], "WER (Word Error Rate)", "WER đo tỷ lệ lỗi thay thế, chèn và xóa từ so với bản chuẩn (Slide 2).", 2, 510),
            ],
        },
        {
            "title": "Bài 4: Hàng đợi Bất đồng bộ & Xử lý Tác vụ Nặng trong Microservices",
            "description": "Thiết kế kiến trúc xử lý video/AI bất đồng bộ với Message Queue, Worker Pool và Retry.",
            "topic": "Async Processing & Microservices",
            "course": c_dist,
            "lecturer": u_lecturer2,
            "duration": 1440,
            "views": 29,
            "slides": [
                (1, "Tại sao không xử lý AI đồng bộ trong HTTP Request?", "Video bài giảng mất nhiều phút xử lý; request đồng bộ gây timeout và nghẽn API.", ["HTTP Timeout", "Tách API Gateway và Worker", "Trải nghiệm người dùng"], 0, 480),
                (2, "Kiến trúc Producer - Queue - Worker", "API nhận file, đẩy job vào hàng đợi, worker xử lý và cập nhật trạng thái vào DB.", ["ProcessingJob state machine", "Idempotency & Retry", "Theo dõi tiến độ realtime"], 480, 1440),
            ],
            "transcripts": [
                (0, "lecturer", 10, 450, "Khi giảng viên tải lên video dài 60 phút, hệ thống tuyệt đối không thể bắt trình duyệt chờ HTTP trả về kết quả ASR ngay lập tức.", True),
                (1, "lecturer", 490, 1400, "Giải pháp chuẩn ở slide 2 là tạo bản ghi ProcessingJob với trạng thái queued, rồi worker độc lập xử lý từng bước và cập nhật tiến độ.", False),
            ],
            "terms": [
                {"term": "Idempotency", "definition": "Tính chất đảm bảo thực thi lại một tác vụ nhiều lần không gây sai lệch dữ liệu.", "slide_number": 2, "timestamp": 490},
            ],
            "quiz_questions": [
                ("mcq", "Lý do chính cần tách pipeline xử lý video AI ra khỏi HTTP request đồng bộ là gì?", ["Để giảm dung lượng ảnh", "Tránh timeout HTTP và không làm nghẽn API server", "Để tắt cơ sở dữ liệu", "Vì trình duyệt không hỗ trợ JSON"], "Tránh timeout HTTP và không làm nghẽn API server", "Tác vụ AI đa phương thức tốn nhiều thời gian nên cần hàng đợi bất đồng bộ (Slide 1-2).", 1, 10),
            ],
        },
    ]

    created_lectures = []
    for idx, spec in enumerate(lectures_spec):
        lec = Lecture(
            title=spec["title"],
            description=spec["description"],
            topic=spec["topic"],
            course_id=spec["course"].id,
            lecturer_id=spec["lecturer"].id,
            duration_seconds=spec["duration"],
            ai_status="completed",
            ai_mode="simulated",
            is_published=True,
            view_count=spec["views"],
            created_at=now - timedelta(days=10 - idx * 2),
        )
        db.add(lec)
        db.flush()
        created_lectures.append(lec)

        sp_lec = Speaker(
            lecture_id=lec.id,
            speaker_label="SPEAKER_00",
            display_name=spec["lecturer"].full_name,
            speaking_duration_seconds=round(spec["duration"] * 0.84, 1),
        )
        sp_stu = Speaker(
            lecture_id=lec.id,
            speaker_label="SPEAKER_01",
            display_name="Sinh viên lớp học",
            speaking_duration_seconds=round(spec["duration"] * 0.16, 1),
        )
        db.add_all([sp_lec, sp_stu])
        db.flush()

        slides_objs = []
        for s_num, s_title, s_ocr, s_bullets, s_start, s_end in spec["slides"]:
            sl = Slide(
                lecture_id=lec.id,
                slide_number=s_num,
                title=s_title,
                ocr_text=s_ocr,
                bullet_points=s_bullets,
                start_time=float(s_start),
                end_time=float(s_end),
            )
            db.add(sl)
            slides_objs.append(sl)

            seg = LectureSegment(
                lecture_id=lec.id,
                title=s_title,
                description=s_ocr,
                start_time=float(s_start),
                end_time=float(s_end),
                slide_number=s_num,
                keywords=[spec["topic"], f"Slide {s_num}"],
            )
            db.add(seg)
        db.flush()

        for sl_idx, who, t_start, t_end, txt, emph in spec["transcripts"]:
            db.add(
                Transcript(
                    lecture_id=lec.id,
                    speaker_id=sp_lec.id if who == "lecturer" else sp_stu.id,
                    slide_id=slides_objs[sl_idx].id,
                    start_time=float(t_start),
                    end_time=float(t_end),
                    text=txt,
                    confidence=0.95,
                    is_repeated_emphasis=emph,
                )
            )

        db.add(
            Summary(
                lecture_id=lec.id,
                overview=spec["description"],
                key_points=[sl[1] for sl in spec["slides"]],
                important_concepts=[t["term"] for t in spec["terms"]],
                technical_terms=spec["terms"],
                examples=[f"Minh họa thực tiễn trong {spec['slides'][1][1]}"],
                conclusion=f"Bài giảng '{spec['title']}' cung cấp nền tảng vững chắc để sinh viên tiếp tục làm bài ôn tập và hỏi đáp với trợ lý AI.",
                takeaways=[
                    f"Nắm chắc các thuật ngữ trọng tâm: {', '.join(t['term'] for t in spec['terms'])}.",
                    "Xem lại các đoạn được đánh dấu nhấn mạnh trong transcript.",
                ],
                ai_mode="simulated",
            )
        )

        qz = Quiz(
            lecture_id=lec.id,
            title=f"Bài ôn tập: {spec['title']}",
            description="Câu hỏi trắc nghiệm và tự luận tổng hợp từ slide & transcript.",
            ai_mode="simulated",
        )
        db.add(qz)
        db.flush()

        for q_type, prompt, opts, correct, expl, sl_num, ts in spec["quiz_questions"]:
            db.add(
                Question(
                    quiz_id=qz.id,
                    question_type=q_type,
                    prompt=prompt,
                    options=opts,
                    correct_answer=correct,
                    explanation=expl,
                    slide_number=sl_num,
                    timestamp_seconds=float(ts),
                )
            )

        db.add(
            ProcessingJob(
                lecture_id=lec.id,
                status="completed",
                current_step="Hoàn tất 9/9 bước",
                progress_percent=100,
                ai_mode="simulated",
                steps_log=["[OK] Audio & ASR", "[OK] Diarization", "[OK] OCR & Video", "[OK] Alignment", "[OK] Summary & RAG & Quiz"],
                started_at=now - timedelta(days=9 - idx),
                completed_at=now - timedelta(days=9 - idx) + timedelta(minutes=3),
            )
        )

        db.add(
            Analytics(
                lecture_id=lec.id,
                speaking_rate_wpm=132.0 + idx * 4,
                lecturer_talk_ratio=0.84,
                interaction_ratio=0.16,
                topic_time_distribution=[
                    {
                        "topic": sl[1],
                        "seconds": sl[5] - sl[4],
                        "percent": round(((sl[5] - sl[4]) / spec["duration"]) * 100, 1),
                    }
                    for sl in spec["slides"]
                ],
                repeated_concepts=[t["term"] for t in spec["terms"]],
                student_engagement_score=82.5 - idx * 3,
                gesture_analysis=build_gesture_analysis_payload(spec["duration"], "simulated"),
                improvement_suggestions=[
                    "Tăng thêm câu hỏi kiểm tra nhanh giữa buổi để giữ nhịp tương tác.",
                    "Bổ sung ví dụ trực quan ở phần chuyển tiếp giữa Slide 2 và Slide 3.",
                ],
                ai_mode="simulated",
            )
        )

    db.flush()

    # 6. Student Learning Progress & Quiz Attempt
    db.add_all([
        LearningProgress(
            student_id=u_student1.id,
            lecture_id=created_lectures[0].id,
            progress_percent=100.0,
            watched_seconds=1800,
            last_position_seconds=1800.0,
            is_completed=True,
            needs_review=False,
            saved_summary=True,
        ),
        LearningProgress(
            student_id=u_student1.id,
            lecture_id=created_lectures[1].id,
            progress_percent=65.0,
            watched_seconds=975,
            last_position_seconds=975.0,
            is_completed=False,
            needs_review=True,
            saved_summary=True,
        ),
        LearningProgress(
            student_id=u_student1.id,
            lecture_id=created_lectures[2].id,
            progress_percent=30.0,
            watched_seconds=486,
            last_position_seconds=486.0,
            is_completed=False,
            needs_review=True,
            saved_summary=False,
        ),
    ])

    first_quiz = db.query(Quiz).filter(Quiz.lecture_id == created_lectures[0].id).first()
    if first_quiz:
        db.add(
            QuizAttempt(
                quiz_id=first_quiz.id,
                student_id=u_student1.id,
                answers={},
                score=2.0,
                max_score=2.0,
                submitted_at=now - timedelta(days=1),
            )
        )

    db.add_all([
        SystemLog(level="INFO", module="startup", message="Hệ thống LectureAI khởi tạo dữ liệu mẫu thành công."),
        SystemLog(level="INFO", module="ai_pipeline", message="Pipeline AI đang chạy ở chế độ mô phỏng (simulated) — sẵn sàng tích hợp Whisper/PaddleOCR/LLM."),
    ])

    db.commit()
