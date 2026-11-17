from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai_pipeline.base import get_pipeline_status_report
from app.api import admin, auth, lecturer, lectures, student
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Nền tảng phân tích, tóm tắt và khai thác nội dung bài giảng đa phương thức (Multimodal Lecture Intelligence Platform).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(lecturer.router)
app.include_router(admin.router)
app.include_router(lectures.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "ai_status": get_pipeline_status_report(),
    }
