import re
from typing import Any, Dict, List
from app.ai_pipeline.base import AI_MODE_LABELS, get_active_ai_mode


def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^\w\sÀ-ỹ]", " ", text.lower())
    return [tok for tok in cleaned.split() if len(tok) > 1]


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class RAGEngine:
    """
    Retrieval-Augmented Generation interface over lecture transcripts, slides, and summary.
    Designed to swap in Vector DB + Embedding Model + LLM without changing API contracts.
    """

    def answer_question(
        self,
        question: str,
        lecture_title: str,
        slides: List[Any],
        transcripts: List[Any],
        summary: Any = None,
        simplify: bool = False,
    ) -> Dict[str, Any]:
        mode = get_active_ai_mode()
        query_tokens = set(_tokenize(question))

        # Score transcript segments
        scored_transcripts = []
        for tr in transcripts:
            text_tokens = set(_tokenize(tr.text))
            overlap = len(query_tokens & text_tokens)
            # Boost exact phrase or substring match
            q_lower = question.lower().strip()
            if len(q_lower) >= 4 and q_lower in tr.text.lower():
                overlap += 5
            if overlap > 0:
                scored_transcripts.append((overlap, tr))

        scored_transcripts.sort(key=lambda x: x[0], reverse=True)

        # Score slides
        scored_slides = []
        for sl in slides:
            slide_text = f"{sl.title} {sl.ocr_text} {' '.join(sl.bullet_points or [])}"
            slide_tokens = set(_tokenize(slide_text))
            overlap = len(query_tokens & slide_tokens)
            if overlap > 0:
                scored_slides.append((overlap, sl))

        scored_slides.sort(key=lambda x: x[0], reverse=True)

        citations: List[Dict[str, Any]] = []
        seen_keys = set()

        for _, tr in scored_transcripts[:3]:
            slide_num = tr.slide.slide_number if tr.slide else None
            key = ("tr", tr.id)
            if key not in seen_keys:
                seen_keys.add(key)
                citations.append(
                    {
                        "source_type": "transcript",
                        "slide_number": slide_num,
                        "timestamp_seconds": tr.start_time,
                        "timestamp_formatted": _format_timestamp(tr.start_time),
                        "excerpt": tr.text,
                        "speaker": tr.speaker.display_name if tr.speaker else "Giảng viên",
                    }
                )

        for _, sl in scored_slides[:2]:
            key = ("sl", sl.slide_number)
            if key not in seen_keys:
                seen_keys.add(key)
                citations.append(
                    {
                        "source_type": "slide",
                        "slide_number": sl.slide_number,
                        "timestamp_seconds": sl.start_time,
                        "timestamp_formatted": _format_timestamp(sl.start_time),
                        "excerpt": f"Slide {sl.slide_number}: {sl.title} — {sl.ocr_text[:180]}",
                        "speaker": "Nội dung Slide",
                    }
                )

        # Build grounded answer
        if not citations and transcripts:
            # Fallback to first relevant context or summary
            first_tr = transcripts[0]
            citations.append(
                {
                    "source_type": "transcript",
                    "slide_number": first_tr.slide.slide_number if first_tr.slide else 1,
                    "timestamp_seconds": first_tr.start_time,
                    "timestamp_formatted": _format_timestamp(first_tr.start_time),
                    "excerpt": first_tr.text,
                    "speaker": first_tr.speaker.display_name if first_tr.speaker else "Giảng viên",
                }
            )

        if scored_transcripts or scored_slides:
            top_snippets = [c["excerpt"] for c in citations[:2]]
            if simplify:
                answer = (
                    f"**Giải thích đơn giản hơn về bài giảng \"{lecture_title}\":**\n\n"
                    f"Nói một cách dễ hiểu, phần bạn đang hỏi liên quan trực tiếp đến: {top_snippets[0]} "
                )
                if len(top_snippets) > 1:
                    answer += f"Bên cạnh đó, slide bài giảng cũng nhấn mạnh: {top_snippets[1]}"
                answer += "\n\nBạn có thể bấm vào các mốc thời gian và số slide trích dẫn bên dưới để xem lại đúng đoạn giảng viên trình bày."
            else:
                answer = (
                    f"Dựa trên nội dung bài giảng **\"{lecture_title}\"**, hệ thống tìm thấy thông tin liên quan như sau:\n\n"
                    f"- **Nội dung chính:** {top_snippets[0]}\n"
                )
                if len(top_snippets) > 1:
                    answer += f"- **Thông tin bổ sung từ bài giảng:** {top_snippets[1]}\n"
                if summary and summary.takeaways:
                    answer += f"\n**Ghi nhớ liên quan:** {summary.takeaways[0]}"
        else:
            overview_text = summary.overview if summary else "Chưa có tóm tắt chi tiết."
            answer = (
                f"Trong bài giảng **\"{lecture_title}\"**, câu hỏi của bạn chưa khớp trực tiếp với từ khóa cụ thể nào trong transcript hoặc slide. "
                f"Tuy nhiên, tổng quan bài học đề cập: {overview_text}\n\n"
                f"Hãy thử hỏi cụ thể hơn về thuật ngữ hoặc chủ đề xuất hiện trong các slide của bài giảng."
            )

        return {
            "answer": answer,
            "citations": citations,
            "ai_mode": mode.value,
            "ai_mode_label": AI_MODE_LABELS[mode.value]["label"],
            "disclaimer": (
                "Câu trả lời được tổng hợp từ dữ liệu transcript & slide của bài giảng qua RAG retrieval."
                if mode == mode.SIMULATED
                else "Câu trả lời được sinh bởi mô hình AI kết hợp RAG."
            ),
        }
