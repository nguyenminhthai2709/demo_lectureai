from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.database import get_db
from app.db.models import (
    Course,
    CourseClass,
    Enrollment,
    LearningProgress,
    Lecture,
    Question,
    Quiz,
    QuizAttempt,
    User,
)

router = APIRouter(prefix="/api/student", tags=["Student"])


def _get_enrolled_course_ids(db: Session, student_id: int) -> list[int]:
    rows = (
        db.query(CourseClass.course_id)
        .join(Enrollment, Enrollment.class_id == CourseClass.id)
        .filter(Enrollment.student_id == student_id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


@router.get("/dashboard")
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    course_ids = _get_enrolled_course_ids(db, current_user.id)
    lectures = (
        db.query(Lecture)
        .filter(Lecture.course_id.in_(course_ids), Lecture.is_published == True)
        .order_by(Lecture.created_at.desc())
        .all()
    ) if course_ids else []

    progress_map = {
        lp.lecture_id: lp
        for lp in db.query(LearningProgress).filter(LearningProgress.student_id == current_user.id).all()
    }

    total_lectures = len(lectures)
    completed_count = sum(1 for l in lectures if progress_map.get(l.id) and progress_map[l.id].is_completed)
    total_watched_seconds = sum(progress_map[l.id].watched_seconds for l in lectures if l.id in progress_map)
    avg_progress = (
        round(sum(progress_map[l.id].progress_percent for l in lectures if l.id in progress_map) / total_lectures, 1)
        if total_lectures > 0
        else 0.0
    )

    recent_lectures = []
    review_items = []
    for l in lectures[:6]:
        lp = progress_map.get(l.id)
        item = {
            "id": l.id,
            "title": l.title,
            "topic": l.topic,
            "course_code": l.course.code if l.course else "",
            "course_title": l.course.title if l.course else "",
            "lecturer_name": l.lecturer.full_name if l.lecturer else "",
            "duration_seconds": l.duration_seconds,
            "ai_status": l.ai_status,
            "ai_mode": l.ai_mode,
            "progress_percent": lp.progress_percent if lp else 0.0,
            "is_completed": lp.is_completed if lp else False,
            "needs_review": lp.needs_review if lp else False,
            "saved_summary": lp.saved_summary if lp else False,
        }
        recent_lectures.append(item)
        if (lp and lp.needs_review) or (not lp or lp.progress_percent < 100):
            review_items.append(item)

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == current_user.id)
        .order_by(QuizAttempt.submitted_at.desc())
        .limit(5)
        .all()
    )

    ai_recommendations = []
    for item in review_items[:3]:
        ai_recommendations.append(
            f"Bạn nên ôn lại '{item['title']}' ({item['course_code']}) — hiện đạt {item['progress_percent']}% tiến độ."
        )
    if not ai_recommendations and lectures:
        ai_recommendations.append("Bạn đã hoàn thành tốt các bài giảng gần đây! Hãy thử làm thêm bài kiểm tra tổng hợp.")

    return {
        "stats": {
            "total_lectures": total_lectures,
            "completed_lectures": completed_count,
            "study_hours": round(total_watched_seconds / 3600, 1),
            "overall_progress_percent": avg_progress,
            "quiz_attempts_count": db.query(QuizAttempt).filter(QuizAttempt.student_id == current_user.id).count(),
        },
        "recent_lectures": recent_lectures,
        "review_items": review_items[:4],
        "ai_recommendations": ai_recommendations,
        "recent_quiz_attempts": [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "quiz_title": a.quiz.title if a.quiz else "",
                "score": a.score,
                "max_score": a.max_score,
                "submitted_at": a.submitted_at,
            }
            for a in attempts
        ],
    }


@router.get("/lectures")
def list_student_lectures(
    search: Optional[str] = Query(default=None),
    course_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    course_ids = _get_enrolled_course_ids(db, current_user.id)
    if not course_ids:
        return {"lectures": [], "courses": []}

    query = db.query(Lecture).filter(Lecture.course_id.in_(course_ids), Lecture.is_published == True)
    if course_id:
        query = query.filter(Lecture.course_id == course_id)

    lectures = query.order_by(Lecture.created_at.desc()).all()
    if search:
        kw = search.lower().strip()
        lectures = [
            l for l in lectures
            if kw in l.title.lower()
            or kw in (l.topic or "").lower()
            or (l.course and (kw in l.course.title.lower() or kw in l.course.code.lower()))
            or (l.lecturer and kw in l.lecturer.full_name.lower())
        ]

    progress_map = {
        lp.lecture_id: lp
        for lp in db.query(LearningProgress).filter(LearningProgress.student_id == current_user.id).all()
    }
    courses = db.query(Course).filter(Course.id.in_(course_ids)).all()

    return {
        "courses": [{"id": c.id, "code": c.code, "title": c.title} for c in courses],
        "lectures": [
            {
                "id": l.id,
                "title": l.title,
                "description": l.description,
                "topic": l.topic,
                "course_id": l.course_id,
                "course_code": l.course.code if l.course else "",
                "course_title": l.course.title if l.course else "",
                "lecturer_name": l.lecturer.full_name if l.lecturer else "",
                "duration_seconds": l.duration_seconds,
                "ai_status": l.ai_status,
                "ai_mode": l.ai_mode,
                "slide_count": len(l.slides),
                "progress_percent": progress_map[l.id].progress_percent if l.id in progress_map else 0.0,
                "saved_summary": progress_map[l.id].saved_summary if l.id in progress_map else False,
                "created_at": l.created_at,
            }
            for l in lectures
        ],
    }


class ProgressUpdateRequest(BaseModel):
    progress_percent: Optional[float] = None
    watched_seconds: Optional[int] = None
    last_position_seconds: Optional[float] = None
    needs_review: Optional[bool] = None
    saved_summary: Optional[bool] = None


@router.post("/lectures/{lecture_id}/progress")
def update_learning_progress(
    lecture_id: int,
    payload: ProgressUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    lp = (
        db.query(LearningProgress)
        .filter(LearningProgress.student_id == current_user.id, LearningProgress.lecture_id == lecture_id)
        .first()
    )
    if not lp:
        lp = LearningProgress(student_id=current_user.id, lecture_id=lecture_id)
        db.add(lp)

    if payload.progress_percent is not None:
        lp.progress_percent = max(0.0, min(100.0, payload.progress_percent))
        lp.is_completed = lp.progress_percent >= 95.0
    if payload.watched_seconds is not None:
        lp.watched_seconds = max(lp.watched_seconds or 0, payload.watched_seconds)
    if payload.last_position_seconds is not None:
        lp.last_position_seconds = payload.last_position_seconds
    if payload.needs_review is not None:
        lp.needs_review = payload.needs_review
    if payload.saved_summary is not None:
        lp.saved_summary = payload.saved_summary

    db.commit()
    db.refresh(lp)
    return {
        "lecture_id": lp.lecture_id,
        "progress_percent": lp.progress_percent,
        "is_completed": lp.is_completed,
        "needs_review": lp.needs_review,
        "saved_summary": lp.saved_summary,
    }


@router.get("/quizzes")
def list_student_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    course_ids = _get_enrolled_course_ids(db, current_user.id)
    lectures = (
        db.query(Lecture).filter(Lecture.course_id.in_(course_ids), Lecture.is_published == True).all()
        if course_ids
        else []
    )
    lecture_ids = [l.id for l in lectures]
    quizzes = db.query(Quiz).filter(Quiz.lecture_id.in_(lecture_ids)).all() if lecture_ids else []

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == current_user.id)
        .order_by(QuizAttempt.submitted_at.desc())
        .all()
    )

    return {
        "quizzes": [
            {
                "id": q.id,
                "lecture_id": q.lecture_id,
                "lecture_title": q.lecture.title if q.lecture else "",
                "course_code": q.lecture.course.code if q.lecture and q.lecture.course else "",
                "title": q.title,
                "description": q.description,
                "ai_mode": q.ai_mode,
                "questions": [
                    {
                        "id": qs.id,
                        "question_type": qs.question_type,
                        "prompt": qs.prompt,
                        "options": qs.options or [],
                        "slide_number": qs.slide_number,
                        "timestamp_seconds": qs.timestamp_seconds,
                    }
                    for qs in q.questions
                ],
            }
            for q in quizzes
        ],
        "attempts": [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "quiz_title": a.quiz.title if a.quiz else "",
                "score": a.score,
                "max_score": a.max_score,
                "submitted_at": a.submitted_at,
            }
            for a in attempts
        ],
    }


class QuizSubmitRequest(BaseModel):
    answers: Dict[str, str]  # {question_id: answer}


@router.post("/quizzes/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài kiểm tra.")

    mcq_questions = [q for q in quiz.questions if q.question_type == "mcq"]
    max_score = float(len(mcq_questions))
    score = 0.0
    feedback = []

    for q in quiz.questions:
        student_ans = payload.answers.get(str(q.id), "").strip()
        is_correct = None
        if q.question_type == "mcq":
            is_correct = student_ans == q.correct_answer
            if is_correct:
                score += 1.0
        feedback.append(
            {
                "question_id": q.id,
                "question_type": q.question_type,
                "prompt": q.prompt,
                "student_answer": student_ans,
                "correct_answer": q.correct_answer,
                "is_correct": is_correct,
                "explanation": q.explanation,
                "slide_number": q.slide_number,
                "timestamp_seconds": q.timestamp_seconds,
            }
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=current_user.id,
        answers=payload.answers,
        score=score,
        max_score=max_score,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "score": score,
        "max_score": max_score,
        "feedback": feedback,
    }
