from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.database import get_db
from app.db.models import Department, Role, SystemLog, User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=4)


class RegisterRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=6)
    student_code: Optional[str] = None
    department_id: Optional[int] = None


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name if user.role else "student",
        "role_display": user.role.display_name if user.role else "Sinh viên",
        "department_id": user.department_id,
        "department_name": user.department.name if user.department else None,
        "student_code": user.student_code,
        "is_active": user.is_active,
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đang bị khóa. Vui lòng liên hệ quản trị viên.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.add(SystemLog(level="INFO", module="auth", message=f"Người dùng {user.email} đăng nhập thành công."))
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng.")

    student_role = db.query(Role).filter(Role.name == "student").first()
    if not student_role:
        raise HTTPException(status_code=500, detail="Hệ thống chưa khởi tạo vai trò sinh viên.")

    dept_id = payload.department_id
    if not dept_id:
        first_dept = db.query(Department).first()
        dept_id = first_dept.id if first_dept else None

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role_id=student_role.id,
        department_id=dept_id,
        student_code=payload.student_code,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": "student"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _serialize_user(current_user)
