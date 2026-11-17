from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "LectureAI – Multimodal Lecture Intelligence Platform"
    APP_ENV: str = "development"
    SECRET_KEY: str = "lectureai-dev-secret-key-2026-multimodal"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    DATABASE_URL: str = "sqlite:///./lectureai.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 500

    # AI Mode: "simulated" | "external_api" | "local_model"
    AI_PIPELINE_MODE: str = "simulated"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    WHISPER_MODEL: str = "base"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
