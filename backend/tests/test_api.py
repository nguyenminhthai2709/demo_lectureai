import io
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DATABASE_URL"] = "sqlite:///./test_lectureai.db"

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    db_file = Path("test_lectureai.db")
    if db_file.exists():
        db_file.unlink()
    with TestClient(app) as c:
        yield c
    if db_file.exists():
        db_file.unlink()


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_health_and_ai_status(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["ai_status"]["active_mode"] == "simulated"


def test_rbac_three_roles(client: TestClient):
    stu_token = _login(client, "student@lectureai.edu.vn", "Student@123")
    lec_token = _login(client, "lecturer@lectureai.edu.vn", "Lecturer@123")
    adm_token = _login(client, "admin@lectureai.edu.vn", "Admin@123")

    # Student cannot access lecturer or admin endpoints
    assert client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {stu_token}"}).status_code == 403
    assert client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {stu_token}"}).status_code == 403

    # Lecturer cannot access admin or student endpoints
    assert client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {lec_token}"}).status_code == 403
    assert client.get("/api/student/dashboard", headers={"Authorization": f"Bearer {lec_token}"}).status_code == 403

    # Admin can access admin dashboard
    res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    assert res.json()["stats"]["total_lectures"] >= 4


def test_student_lecture_search_rag_and_quiz(client: TestClient):
    stu_token = _login(client, "student@lectureai.edu.vn", "Student@123")
    headers = {"Authorization": f"Bearer {stu_token}"}

    # List lectures
    res = client.get("/api/student/lectures", headers=headers)
    assert res.status_code == 200
    lectures = res.json()["lectures"]
    assert len(lectures) >= 3
    lec_id = lectures[0]["id"]

    # Detail
    detail = client.get(f"/api/lectures/{lec_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["slides"]) >= 2

    # Knowledge search
    search_res = client.get(f"/api/lectures/{lec_id}/search?q=Attention", headers=headers)
    assert search_res.status_code == 200

    # RAG Ask
    rag_res = client.post(
        f"/api/lectures/{lec_id}/ask",
        json={"question": "Scaled Dot-Product Attention là gì?", "simplify": False},
        headers=headers,
    )
    assert rag_res.status_code == 200
    assert "citations" in rag_res.json()
    assert rag_res.json()["ai_mode"] == "simulated"

    # Quiz submit
    quizzes = client.get("/api/student/quizzes", headers=headers).json()["quizzes"]
    assert len(quizzes) >= 1
    qz = quizzes[0]
    answers = {str(q["id"]): q["options"][1] for q in qz["questions"] if q["question_type"] == "mcq" and q["options"]}
    sub_res = client.post(f"/api/student/quizzes/{qz['id']}/submit", json={"answers": answers}, headers=headers)
    assert sub_res.status_code == 200
    assert "score" in sub_res.json()


def test_lecturer_crud_upload_and_pipeline(client: TestClient):
    lec_token = _login(client, "lecturer@lectureai.edu.vn", "Lecturer@123")
    headers = {"Authorization": f"Bearer {lec_token}"}

    dash = client.get("/api/lecturer/dashboard", headers=headers).json()
    course_id = dash["courses"][0]["id"]

    # Create lecture
    create_res = client.post(
        "/api/lecturer/lectures",
        json={
            "title": "Bài kiểm thử Pipeline AI",
            "description": "Kiểm tra tạo bài giảng, tải tệp và chạy pipeline",
            "topic": "Multimodal AI",
            "course_id": course_id,
            "duration_seconds": 600,
            "is_published": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    new_id = create_res.json()["id"]

    # Upload TXT slide/doc
    upload_res = client.post(
        f"/api/lecturer/lectures/{new_id}/upload",
        files={"file": ("tai-lieu.txt", io.BytesIO(b"Noi dung tai lieu bai giang"), "text/plain")},
        headers=headers,
    )
    assert upload_res.status_code == 200

    # Run AI Pipeline
    proc_res = client.post(f"/api/lecturer/lectures/{new_id}/process", headers=headers)
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "completed"

    # Analytics & Report
    ana_res = client.get(f"/api/lecturer/lectures/{new_id}/analytics", headers=headers)
    assert ana_res.status_code == 200
    assert "gesture_analysis" in ana_res.json()

    # Delete lecture
    del_res = client.delete(f"/api/lecturer/lectures/{new_id}", headers=headers)
    assert del_res.status_code == 200
