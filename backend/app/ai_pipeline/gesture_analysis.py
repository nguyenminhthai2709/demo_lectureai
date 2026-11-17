from typing import Any, Dict
from app.ai_pipeline.base import AIMode


def build_gesture_analysis_payload(duration_seconds: int, ai_mode: str = AIMode.SIMULATED.value) -> Dict[str, Any]:
    """
    Extensible module for posture, movement, slide-interaction, and optional consent-based facial analysis.
    Includes explicit scientific & legal limitations per Section 6.4.
    """
    return {
        "ai_mode": ai_mode,
        "consent_verified": False,
        "facial_expression_enabled": False,
        "posture_and_movement": {
            "standing_ratio": 0.74,
            "movement_activity_level": "Trung bình - ổn định",
            "hand_gesture_frequency_per_min": 6.4,
            "slide_pointing_events": [
                {"timestamp_seconds": 145, "slide_number": 2, "note": "Chỉ tay nhấn mạnh sơ đồ kiến trúc"},
                {"timestamp_seconds": 420, "slide_number": 4, "note": "Tương tác bảng/slide giải thích ví dụ"},
                {"timestamp_seconds": 780, "slide_number": 6, "note": "Nhấn mạnh công thức trọng tâm"},
            ],
        },
        "facial_expression_summary": {
            "status": "disabled_pending_consent",
            "message": "Phân tích biểu cảm khuôn mặt đang tắt vì chưa có xác nhận đồng ý (consent) và khung pháp lý cụ thể cho lớp học này.",
        },
        "scientific_disclaimer": (
            "LƯU Ý KHOA HỌC & PHÁP LÝ: AI không thể xác định chính xác cảm xúc, mức độ tập trung hay chất lượng giảng dạy "
            "chỉ từ biểu cảm khuôn mặt hoặc tư thế. Các chỉ số chuyển động và tương tác slide chỉ mang tính tham khảo hỗ trợ "
            "giảng viên tự quan sát, không dùng để đánh giá xếp loại giảng viên."
        ),
        "data_source": "Video khung hình bài giảng (OpenCV/MediaPipe interface - dữ liệu mô phỏng)" if ai_mode == AIMode.SIMULATED.value else "Video khung hình bài giảng",
    }
