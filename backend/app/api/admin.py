from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_pipeline.base import get_pipeline_status_report
from app.core.config import settings
from app.core.security import hash_password, require_roles
from app.db.database import get_db
from app.db.models import (
    Course,
    CourseClass,
    Department,
    LearningProgress,
    Lecture,
    LectureFile,
    ProcessingJob,
    QuizAttempt,
    Role,
    SystemLog,
    User,
)

router = APIRouter(prefix="/api/admin", tags=["Administrator"])


@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    roles_map = {r.name: r.id for r in db.query(Role).all()}
    total_students = db.query(User).filter(User.role_id == roles_map.get("student")).count()
    total_lecturers = db.query(User).filter(User.role_id == roles_map.get("lecturer")).count()
    total_admins = db.query(User).filter(User.role_id == roles_map.get("admin")).count()
    total_courses = db.query(Course).count()
    lectures = db.query(Lecture).all()
    total_lectures = len(lectures)
    processed_hours = round(sum(l.duration_seconds or 0 for l in lectures if l.ai_status == "completed") / 3600, 2)
    total_views = sum(l.view_count or 0 for l in lectures)

    # Honest training quality metrics from actual DB records (not fabricated AI scores)
    courses = db.query(Course).all()
    course_stats = []
    for c in courses:
        c_lectures = c.lectures
        c_views = sum(l.view_count or 0 for l in c_lectures)
        c_lec_ids = [l.id for l in c_lectures]
        progress_rows = (
            db.query(LearningProgress).filter(LearningProgress.lecture_id.in_(c_lec_ids)).all()
            if c_lec_ids
            else []
        )
        avg_completion = (
            round(sum(p.progress_percent for p in progress_rows) / len(progress_rows), 1)
            if progress_rows
            else 0.0
        )
        course_stats.append(
            {
                "course_id": c.id,
                "code": c.code,
                "title": c.title,
                "lecturer_name": c.lecturer.full_name if c.lecturer else "Chưa phân công",
                "lecture_count": len(c_lectures),
                "total_views": c_views,
                "avg_completion_percent": avg_completion,
                "needs_attention": len(c_lectures) == 0 or avg_completion < 50.0,
            }
        )

    # Storage usage
    total_bytes = sum(f.file_size_bytes or 0 for f in db.query(LectureFile).all())
    jobs = db.query(ProcessingJob).order_by(ProcessingJob.started_at.desc()).limit(10).all()
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(15).all()

    return {
        "stats": {
            "total_students": total_students,
            "total_lecturers": total_lecturers,
            "total_admins": total_admins,
            "total_courses": total_courses,
            "total_lectures": total_lectures,
            "processed_video_hours": processed_hours,
            "total_lecture_views": total_views,
            "total_quiz_attempts": db.query(QuizAttempt).count(),
            "storage_used_mb": round(total_bytes / (1024 * 1024), 2),
        },
        "quality_notice": "Các số liệu chất lượng đào tạo được tổng hợp trực tiếp từ lượt truy cập, tiến độ học tập và kết quả kiểm tra thực tế trong CSDL.",
        "course_quality_stats": course_stats,
        "ai_pipeline_status": get_pipeline_status_report(),
        "recent_jobs": [
            {
                "id": j.id,
                "lecture_id": j.lecture_id,
                "lecture_title": j.lecture.title if j.lecture else "",
                "status": j.status,
                "current_step": j.current_step,
                "progress_percent": j.progress_percent,
                "ai_mode": j.ai_mode,
                "started_at": j.started_at,
            }
            for j in jobs
        ],
        "system_logs": [
            {
                "id": lg.id,
                "level": lg.level,
                "module": lg.module,
                "message": lg.message,
                "created_at": lg.created_at,
            }
            for lg in logs
        ],
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.name if u.role else "student",
                "role_display": u.role.display_name if u.role else "Sinh viên",
                "department_name": u.department.name if u.department else None,
                "student_code": u.student_code,
                "is_active": u.is_active,
                "last_login_at": u.last_login_at,
            }
            for u in users
        ]
    }


class AdminCreateUserRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=6)
    role: str = Field(pattern="^(student|lecturer|admin)$")
    department_id: Optional[int] = None
    student_code: Optional[str] = None


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại trong hệ thống.")
    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        raise HTTPException(status_code=400, detail="Vai trò không hợp lệ.")

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role_id=role.id,
        department_id=payload.department_id,
        student_code=payload.student_code,
        is_active=True,
    )
    db.add(user)
    db.add(SystemLog(level="INFO", module="admin", message=f"Admin {current_user.email} tạo tài khoản {email} ({payload.role})."))
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": payload.role}


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản quản trị đang đăng nhập.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")

    user.is_active = not user.is_active
    action_text = "mở khóa" if user.is_active else "khóa"
    db.add(SystemLog(level="WARNING", module="admin", message=f"Admin {current_user.email} đã {action_text} tài khoản {user.email}."))
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.get("/academic")
def list_academic_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    departments = db.query(Department).all()
    courses = db.query(Course).all()
    classes = db.query(CourseClass).all()
    lecturers = (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .filter(Role.name == "lecturer")
        .all()
    )
    return {
        "departments": [{"id": d.id, "code": d.code, "name": d.name, "description": d.description} for d in departments],
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "credits": c.credits,
                "semester": c.semester,
                "department_name": c.department.name if c.department else "",
                "lecturer_name": c.lecturer.full_name if c.lecturer else "Chưa phân công",
                "lecture_count": len(c.lectures),
            }
            for c in courses
        ],
        "classes": [
            {
                "id": cl.id,
                "code": cl.code,
                "name": cl.name,
                "semester": cl.semester,
                "schedule": cl.schedule,
                "course_code": cl.course.code if cl.course else "",
                "enrollment_count": len(cl.enrollments),
            }
            for cl in classes
        ],
        "lecturers": [{"id": l.id, "full_name": l.full_name, "email": l.email} for l in lecturers],
    }


class DepartmentCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    description: str = ""


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    if db.query(Department).filter(Department.code == payload.code.strip().upper()).first():
        raise HTTPException(status_code=400, detail="Mã khoa đã tồn tại.")
    dept = Department(code=payload.code.strip().upper(), name=payload.name.strip(), description=payload.description.strip())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"id": dept.id, "code": dept.code, "name": dept.name}


class CourseCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    title: str = Field(min_length=3, max_length=200)
    credits: int = Field(default=3, ge=1, le=10)
    semester: str = "HK1 2026-2027"
    department_id: Optional[int] = None
    lecturer_id: Optional[int] = None


@router.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    if db.query(Course).filter(Course.code == payload.code.strip().upper()).first():
        raise HTTPException(status_code=400, detail="Mã môn học đã tồn tại.")
    course = Course(
        code=payload.code.strip().upper(),
        title=payload.title.strip(),
        credits=payload.credits,
        semester=payload.semester,
        department_id=payload.department_id,
        lecturer_id=payload.lecturer_id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"id": course.id, "code": course.code, "title": course.title}
