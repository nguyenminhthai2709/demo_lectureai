from enum import Enum
from typing import Any, Dict
from app.core.config import settings


class AIMode(str, Enum):
    LOCAL_MODEL = "local_model"      # Đã tích hợp mô hình AI thực tế
    EXTERNAL_API = "external_api"    # Đang sử dụng API hoặc dịch vụ AI bên ngoài
    SIMULATED = "simulated"          # Đang sử dụng dữ liệu mẫu hoặc mô phỏng


AI_MODE_LABELS: Dict[str, Dict[str, str]] = {
    AIMode.LOCAL_MODEL.value: {
        "label": "Mô hình AI nội bộ",
        "description": "Đang chạy mô hình AI thực tế (Whisper / PaddleOCR / LLM local).",
        "badge_color": "green",
    },
    AIMode.EXTERNAL_API.value: {
        "label": "Dịch vụ AI bên ngoài",
        "description": "Đang sử dụng API AI bên ngoài thông qua biến môi trường.",
        "badge_color": "blue",
    },
    AIMode.SIMULATED.value: {
        "label": "Mô phỏng / Dữ liệu mẫu",
        "description": "Chưa cấu hình API key hoặc model weights thực tế; hệ thống đang sử dụng pipeline mô phỏng có cấu trúc để kiểm thử kiến trúc.",
        "badge_color": "amber",
    },
}


def get_active_ai_mode() -> AIMode:
    mode = (settings.AI_PIPELINE_MODE or "simulated").lower()
    if mode == AIMode.EXTERNAL_API.value and (settings.OPENAI_API_KEY or settings.GEMINI_API_KEY):
        return AIMode.EXTERNAL_API
    if mode == AIMode.LOCAL_MODEL.value:
        return AIMode.LOCAL_MODEL
    return AIMode.SIMULATED


def get_pipeline_status_report() -> Dict[str, Any]:
    active_mode = get_active_ai_mode()
    return {
        "active_mode": active_mode.value,
        "mode_info": AI_MODE_LABELS[active_mode.value],
        "modules": [
            {
                "id": "audio_asr",
                "name": "Audio Processing & ASR (Whisper)",
                "target_tech": f"FFmpeg + Whisper ({settings.WHISPER_MODEL})",
                "status": active_mode.value,
                "ready_for_integration": True,
            },
            {
                "id": "diarization",
                "name": "Speaker Diarization",
                "target_tech": "pyannote.audio",
                "status": active_mode.value,
                "ready_for_integration": True,
            },
            {
                "id": "ocr_video",
                "name": "Slide OCR & Video Frame Analysis",
                "target_tech": "PaddleOCR + OpenCV",
                "status": active_mode.value,
                "ready_for_integration": True,
            },
            {
                "id": "alignment",
                "name": "Multimodal Alignment",
                "target_tech": "Timestamp & Semantic Cross-Modal Alignment",
                "status": active_mode.value,
                "ready_for_integration": True,
            },
            {
                "id": "summarization_rag",
                "name": "Summarization, RAG & Quiz Generation",
                "target_tech": "LLM + Embedding Model + Vector DB",
                "status": active_mode.value,
                "ready_for_integration": True,
            },
            {
                "id": "gesture",
                "name": "Phân tích tư thế, cử chỉ & tương tác slide",
                "target_tech": "MediaPipe / OpenPose (tùy chọn & có đồng ý pháp lý)",
                "status": AIMode.SIMULATED.value,
                "ready_for_integration": True,
            },
        ],
    }
