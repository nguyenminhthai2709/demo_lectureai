from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_pipeline.base import AI_MODE_LABELS
from app.ai_pipeline.rag_engine import RAGEngine
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import CourseClass, Enrollment, Lecture, LectureFile, User

router = APIRouter(prefix="/api", tags=["Lectures & RAG"])
rag_engine = RAGEngine()


def verify_lecture_access(db: Session, user: User, lecture: Lecture) -> None:
    role_name = user.role.name if user.role else "student"
    if role_name == "admin":
        return
    if role_name == "lecturer":
        if lecture.lecturer_id != user.id:
            raise HTTPException(status_code=403, detail="Giảng viên chỉ được truy cập bài giảng do mình phụ trách.")
        return
    # Student: must be enrolled in a class of this course AND lecture must be published
    if not lecture.is_published:
        raise HTTPException(status_code=403, detail="Bài giảng này chưa được xuất bản.")
    enrolled = (
        db.query(Enrollment)
        .join(CourseClass, Enrollment.class_id == CourseClass.id)
        .filter(
            Enrollment.student_id == user.id,
            CourseClass.course_id == lecture.course_id,
        )
        .first()
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="Bạn chưa đăng ký học phần chứa bài giảng này.")


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    simplify: bool = False


@router.get("/lectures/{lecture_id}")
def get_lecture_detail(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")
    verify_lecture_access(db, current_user, lecture)

    # Increment view count for students
    if current_user.role and current_user.role.name == "student":
        lecture.view_count = (lecture.view_count or 0) + 1
        db.commit()

    return {
        "id": lecture.id,
        "title": lecture.title,
        "description": lecture.description,
        "topic": lecture.topic,
        "course_id": lecture.course_id,
        "course_code": lecture.course.code if lecture.course else "",
        "course_title": lecture.course.title if lecture.course else "",
        "lecturer_id": lecture.lecturer_id,
        "lecturer_name": lecture.lecturer.full_name if lecture.lecturer else "",
        "duration_seconds": lecture.duration_seconds,
        "ai_status": lecture.ai_status,
        "ai_mode": lecture.ai_mode,
        "ai_mode_info": AI_MODE_LABELS.get(lecture.ai_mode, AI_MODE_LABELS["simulated"]),
        "is_published": lecture.is_published,
        "view_count": lecture.view_count,
        "created_at": lecture.created_at,
        "files": [
            {
                "id": f.id,
                "file_type": f.file_type,
                "original_filename": f.original_filename,
                "mime_type": f.mime_type,
                "file_size_bytes": f.file_size_bytes,
                "url": f"/api/files/{f.id}",
            }
            for f in lecture.files
        ],
        "speakers": [
            {
                "id": sp.id,
                "speaker_label": sp.speaker_label,
                "display_name": sp.display_name,
                "speaking_duration_seconds": sp.speaking_duration_seconds,
            }
            for sp in lecture.speakers
        ],
        "slides": [
            {
                "id": sl.id,
                "slide_number": sl.slide_number,
                "title": sl.title,
                "ocr_text": sl.ocr_text,
                "bullet_points": sl.bullet_points or [],
                "start_time": sl.start_time,
                "end_time": sl.end_time,
            }
            for sl in lecture.slides
        ],
        "transcripts": [
            {
                "id": tr.id,
                "speaker_id": tr.speaker_id,
                "speaker_name": tr.speaker.display_name if tr.speaker else "Giảng viên",
                "speaker_label": tr.speaker.speaker_label if tr.speaker else "SPEAKER_00",
                "slide_id": tr.slide_id,
                "slide_number": tr.slide.slide_number if tr.slide else None,
                "start_time": tr.start_time,
                "end_time": tr.end_time,
                "text": tr.text,
                "confidence": tr.confidence,
                "is_repeated_emphasis": tr.is_repeated_emphasis,
            }
            for tr in lecture.transcripts
        ],
        "segments": [
            {
                "id": seg.id,
                "title": seg.title,
                "description": seg.description,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "slide_number": seg.slide_number,
                "keywords": seg.keywords or [],
            }
            for seg in lecture.segments
        ],
        "summary": {
            "overview": lecture.summary.overview,
            "key_points": lecture.summary.key_points or [],
            "important_concepts": lecture.summary.important_concepts or [],
            "technical_terms": lecture.summary.technical_terms or [],
            "examples": lecture.summary.examples or [],
            "conclusion": lecture.summary.conclusion,
            "takeaways": lecture.summary.takeaways or [],
            "ai_mode": lecture.summary.ai_mode,
        }
        if lecture.summary
        else None,
        "quizzes": [
            {
                "id": qz.id,
                "title": qz.title,
                "description": qz.description,
                "question_count": len(qz.questions),
            }
            for qz in lecture.quizzes
        ],
    }


@router.get("/lectures/{lecture_id}/search")
def search_lecture_knowledge(
    lecture_id: int,
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")
    verify_lecture_access(db, current_user, lecture)

    keyword = q.lower().strip()
    matches = []
    for tr in lecture.transcripts:
        if keyword in tr.text.lower():
            matches.append(
                {
                    "type": "transcript",
                    "slide_number": tr.slide.slide_number if tr.slide else None,
                    "timestamp_seconds": tr.start_time,
                    "speaker": tr.speaker.display_name if tr.speaker else "Giảng viên",
                    "text": tr.text,
                }
            )
    for sl in lecture.slides:
        haystack = f"{sl.title} {sl.ocr_text} {' '.join(sl.bullet_points or [])}".lower()
        if keyword in haystack:
            matches.append(
                {
                    "type": "slide",
                    "slide_number": sl.slide_number,
                    "timestamp_seconds": sl.start_time,
                    "speaker": "Slide",
                    "text": f"Slide {sl.slide_number}: {sl.title} — {sl.ocr_text}",
                }
            )
    return {"query": q, "count": len(matches), "results": matches}


@router.post("/lectures/{lecture_id}/ask")
def ask_ai_assistant(
    lecture_id: int,
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")
    verify_lecture_access(db, current_user, lecture)

    return rag_engine.answer_question(
        question=payload.question,
        lecture_title=lecture.title,
        slides=lecture.slides,
        transcripts=lecture.transcripts,
        summary=lecture.summary,
        simplify=payload.simplify,
    )


@router.get("/lectures/{lecture_id}/summary/export")
def export_summary_markdown(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture or not lecture.summary:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản tóm tắt bài giảng.")
    verify_lecture_access(db, current_user, lecture)

    s = lecture.summary
    lines = [
        f"# Tóm tắt bài giảng: {lecture.title}",
        f"- **Môn học:** {lecture.course.title if lecture.course else ''}",
        f"- **Giảng viên:** {lecture.lecturer.full_name if lecture.lecturer else ''}",
        f"- **Chế độ AI:** {s.ai_mode}",
        "",
        "## 1. Tổng quan",
        s.overview,
        "",
        "## 2. Các ý chính",
        *[f"- {kp}" for kp in (s.key_points or [])],
        "",
        "## 3. Thuật ngữ chuyên ngành",
        *[f"- **{t.get('term')}** (Slide {t.get('slide_number')}): {t.get('definition')}" for t in (s.technical_terms or [])],
        "",
        "## 4. Kết luận & Nội dung cần ghi nhớ",
        s.conclusion,
        *[f"- {tk}" for tk in (s.takeaways or [])],
    ]
    return PlainTextResponse(
        content="\n".join(lines),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="tom-tat-bai-giang-{lecture.id}.md"'},
    )


@router.get("/files/{file_id}")
def serve_lecture_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lf = db.query(LectureFile).filter(LectureFile.id == file_id).first()
    if not lf:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp.")
    verify_lecture_access(db, current_user, lf.lecture)
    path = Path(lf.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Tệp không còn tồn tại trên máy chủ.")
    return FileResponse(path=path, media_type=lf.mime_type, filename=lf.original_filename)
