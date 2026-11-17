import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_pipeline.orchestrator import LecturePipelineOrchestrator
from app.core.config import settings
from app.core.security import require_roles
from app.db.database import get_db
from app.db.models import Analytics, Course, Lecture, LectureFile, ProcessingJob, SystemLog, User

router = APIRouter(prefix="/api/lecturer", tags=["Lecturer"])
orchestrator = LecturePipelineOrchestrator()

ALLOWED_EXTENSIONS = {
    ".mp4": "video",
    ".mov": "video",
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".pdf": "slide",
    ".pptx": "slide",
    ".docx": "document",
    ".txt": "document",
}


@router.get("/dashboard")
def lecturer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    courses = db.query(Course).filter(Course.lecturer_id == current_user.id).all()
    lectures = (
        db.query(Lecture)
        .filter(Lecture.lecturer_id == current_user.id)
        .order_by(Lecture.created_at.desc())
        .all()
    )
    total_duration_hours = round(sum(l.duration_seconds or 0 for l in lectures) / 3600, 1)
    total_views = sum(l.view_count or 0 for l in lectures)
    completed_ai = sum(1 for l in lectures if l.ai_status == "completed")

    analytics_rows = (
        db.query(Analytics)
        .join(Lecture, Analytics.lecture_id == Lecture.id)
        .filter(Lecture.lecturer_id == current_user.id)
        .all()
    )
    avg_wpm = (
        round(sum(a.speaking_rate_wpm for a in analytics_rows) / len(analytics_rows), 1)
        if analytics_rows
        else 0.0
    )
    avg_interaction = (
        round(sum(a.interaction_ratio for a in analytics_rows) / len(analytics_rows) * 100, 1)
        if analytics_rows
        else 0.0
    )

    return {
        "stats": {
            "total_courses": len(courses),
            "total_lectures": len(lectures),
            "completed_ai_lectures": completed_ai,
            "total_duration_hours": total_duration_hours,
            "total_views": total_views,
            "avg_speaking_wpm": avg_wpm,
            "avg_interaction_percent": avg_interaction,
        },
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "semester": c.semester,
                "credits": c.credits,
                "lecture_count": len(c.lectures),
            }
            for c in courses
        ],
        "lectures": [
            {
                "id": l.id,
                "title": l.title,
                "topic": l.topic,
                "course_id": l.course_id,
                "course_code": l.course.code if l.course else "",
                "course_title": l.course.title if l.course else "",
                "duration_seconds": l.duration_seconds,
                "ai_status": l.ai_status,
                "ai_mode": l.ai_mode,
                "is_published": l.is_published,
                "view_count": l.view_count,
                "file_count": len(l.files),
                "created_at": l.created_at,
            }
            for l in lectures
        ],
    }


class LectureCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = ""
    topic: str = Field(min_length=2, max_length=150)
    course_id: int
    duration_seconds: int = Field(default=900, ge=60, le=18000)
    is_published: bool = True


class LectureUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = None
    topic: Optional[str] = None
    duration_seconds: Optional[int] = Field(default=None, ge=60, le=18000)
    is_published: Optional[bool] = None


@router.post("/lectures", status_code=status.HTTP_201_CREATED)
def create_lecture(
    payload: LectureCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    course = db.query(Course).filter(Course.id == payload.course_id, Course.lecturer_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Môn học không tồn tại hoặc bạn không phụ trách môn học này.")

    lecture = Lecture(
        title=payload.title.strip(),
        description=payload.description.strip(),
        topic=payload.topic.strip(),
        course_id=course.id,
        lecturer_id=current_user.id,
        duration_seconds=payload.duration_seconds,
        ai_status="pending",
        ai_mode=settings.AI_PIPELINE_MODE,
        is_published=payload.is_published,
    )
    db.add(lecture)
    db.add(SystemLog(level="INFO", module="lecturer", message=f"Giảng viên {current_user.email} tạo bài giảng '{lecture.title}'."))
    db.commit()
    db.refresh(lecture)
    return {"id": lecture.id, "title": lecture.title, "ai_status": lecture.ai_status}


@router.put("/lectures/{lecture_id}")
def update_lecture(
    lecture_id: int,
    payload: LectureUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.lecturer_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng thuộc quyền quản lý của bạn.")

    if payload.title is not None:
        lecture.title = payload.title.strip()
    if payload.description is not None:
        lecture.description = payload.description.strip()
    if payload.topic is not None:
        lecture.topic = payload.topic.strip()
    if payload.duration_seconds is not None:
        lecture.duration_seconds = payload.duration_seconds
    if payload.is_published is not None:
        lecture.is_published = payload.is_published

    db.commit()
    db.refresh(lecture)
    return {"id": lecture.id, "title": lecture.title, "is_published": lecture.is_published}


@router.delete("/lectures/{lecture_id}")
def delete_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.lecturer_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng thuộc quyền quản lý của bạn.")

    for f in lecture.files:
        p = Path(f.stored_path)
        if p.exists():
            p.unlink(missing_ok=True)

    db.delete(lecture)
    db.commit()
    return {"message": "Đã xóa bài giảng thành công."}


@router.post("/lectures/{lecture_id}/upload")
async def upload_lecture_file(
    lecture_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.lecturer_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")

    filename = file.filename or "upload.bin"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng '{ext}' không được hỗ trợ. Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS.keys())}",
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Tệp vượt quá giới hạn {settings.MAX_UPLOAD_SIZE_MB}MB.")

    lecture_dir = settings.upload_path / f"lecture_{lecture.id}"
    lecture_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = lecture_dir / safe_name
    dest_path.write_bytes(content)

    lf = LectureFile(
        lecture_id=lecture.id,
        file_type=ALLOWED_EXTENSIONS[ext],
        original_filename=filename,
        stored_path=str(dest_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content),
    )
    db.add(lf)
    db.commit()
    db.refresh(lf)

    return {
        "id": lf.id,
        "file_type": lf.file_type,
        "original_filename": lf.original_filename,
        "file_size_bytes": lf.file_size_bytes,
    }


@router.post("/lectures/{lecture_id}/process")
def trigger_ai_pipeline(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.lecturer_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")

    job = orchestrator.run_pipeline(db, lecture)
    return {
        "job_id": job.id,
        "status": job.status,
        "progress_percent": job.progress_percent,
        "ai_mode": job.ai_mode,
        "steps_log": job.steps_log,
    }


@router.get("/lectures/{lecture_id}/analytics")
def get_lecture_analytics(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.lecturer_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")

    a = lecture.analytics
    if not a:
        raise HTTPException(status_code=404, detail="Bài giảng chưa có dữ liệu phân tích AI. Hãy chạy xử lý AI trước.")

    return {
        "lecture_id": lecture.id,
        "lecture_title": lecture.title,
        "duration_seconds": lecture.duration_seconds,
        "view_count": lecture.view_count,
        "speaking_rate_wpm": a.speaking_rate_wpm,
        "lecturer_talk_ratio": a.lecturer_talk_ratio,
        "interaction_ratio": a.interaction_ratio,
        "topic_time_distribution": a.topic_time_distribution or [],
        "repeated_concepts": a.repeated_concepts or [],
        "student_engagement_score": a.student_engagement_score,
        "gesture_analysis": a.gesture_analysis or {},
        "improvement_suggestions": a.improvement_suggestions or [],
        "ai_mode": a.ai_mode,
    }


@router.get("/lectures/{lecture_id}/report")
def export_lecture_report(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("lecturer")),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.lecturer_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")

    a = lecture.analytics
    lines = [
        f"# Báo cáo Phân tích & Cải thiện Bài giảng: {lecture.title}",
        f"- **Học phần:** {lecture.course.code} - {lecture.course.title}" if lecture.course else "",
        f"- **Giảng viên:** {current_user.full_name}",
        f"- **Thời lượng:** {round((lecture.duration_seconds or 0)/60, 1)} phút | **Lượt xem:** {lecture.view_count}",
        f"- **Chế độ AI:** {lecture.ai_mode}",
        "",
        "## Chỉ số hoạt động giảng dạy",
        f"- Tốc độ nói trung bình: {a.speaking_rate_wpm if a else 'N/A'} từ/phút",
        f"- Tỷ lệ trình bày / trao đổi: {round((a.lecturer_talk_ratio or 0)*100)}% / {round((a.interaction_ratio or 0)*100)}%" if a else "- Chưa có dữ liệu",
        "",
        "## Đề xuất cải thiện bài giảng",
        *([f"- {s}" for s in (a.improvement_suggestions or [])] if a else ["- Hãy chạy phân tích AI để nhận đề xuất."]),
    ]
    return PlainTextResponse(
        content="\n".join(lines),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="bao-cao-giang-day-{lecture.id}.md"'},
    )
