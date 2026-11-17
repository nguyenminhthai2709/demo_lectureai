# LectureAI – Multimodal Lecture Intelligence Platform

> **Learn Smarter. Teach Better. Understand Deeper.**

**LectureAI** là nền tảng AI đa phương thức (Multimodal AI) hỗ trợ phân tích, tóm tắt, đồng bộ và khai thác nội dung bài giảng phục vụ 3 nhóm người dùng: **Sinh viên (Student)**, **Giảng viên (Lecturer)** và **Nhà trường (Administrator)**.

---

## 1. Cấu trúc thư mục dự án

```text
demo_lectureai/
├── backend/
│   ├── app/
│   │   ├── ai_pipeline/           # Kiến trúc Pipeline AI 9 bước (dễ dàng gắn model thật)
│   │   │   ├── base.py            # Phân biệt 3 trạng thái AI: local_model | external_api | simulated
│   │   │   ├── orchestrator.py    # Điều phối 9 bước: Audio/ASR -> Diarization -> OCR -> Alignment -> Summary -> RAG -> Quiz
│   │   │   ├── rag_engine.py      # Hệ thống hỏi đáp RAG trích dẫn Slide & Timestamp
│   │   │   └── gesture_analysis.py# Module mở rộng phân tích tư thế/cử chỉ kèm giới hạn khoa học & pháp lý
│   │   ├── api/                   # REST API + JWT + Role-Based Access Control (RBAC)
│   │   │   ├── auth.py            # Đăng nhập, đăng ký, thông tin tài khoản (/api/auth/*)
│   │   │   ├── student.py         # Dashboard, kho bài giảng, tiến độ, ôn tập & chấm điểm tự động
│   │   │   ├── lecturer.py        # CRUD bài giảng, upload tệp, chạy pipeline AI, phân tích & báo cáo
│   │   │   ├── admin.py           # Quản lý người dùng, đào tạo, chất lượng, AI jobs & logs
│   │   │   └── lectures.py        # Chi tiết bài giảng đa phương thức, tìm kiếm kiến thức, RAG, xuất .MD
│   │   ├── core/
│   │   │   ├── config.py          # Đọc biến môi trường (.env)
│   │   │   └── security.py        # Mã hóa mật khẩu (bcrypt), JWT, RBAC middleware
│   │   ├── db/
│   │   │   ├── database.py        # Kết nối SQLAlchemy (SQLite mặc định, hỗ trợ PostgreSQL)
│   │   │   ├── models.py          # 19+ bảng dữ liệu chuẩn hóa
│   │   │   └── seed.py            # Dữ liệu mẫu nhất quán giữa 3 vai trò
│   │   └── main.py                # Khởi tạo FastAPI, CORS, auto-init DB & seed
│   ├── tests/
│   │   └── test_api.py            # Kiểm thử API & RBAC
│   ├── .env.example               # Mẫu biến môi trường backend
│   └── requirements.txt           # Danh sách thư viện Python
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # HTTP client tự động gắn JWT & format thời gian
│   │   ├── components/
│   │   │   ├── Layout.tsx         # Sidebar điều hướng responsive theo vai trò
│   │   │   ├── LoginPage.tsx      # Trang đăng nhập kèm chọn nhanh tài khoản demo
│   │   │   ├── LectureDetailView.tsx # Xem video/timeline đồng bộ slide, transcript, tóm tắt & chatbot RAG
│   │   │   ├── StudentDashboard.tsx  # Giao diện Sinh viên
│   │   │   ├── LecturerDashboard.tsx # Giao diện Giảng viên & biểu đồ phân tích
│   │   │   ├── AdminDashboard.tsx    # Giao diện Nhà trường & giám sát hệ thống
│   │   │   └── UIPrimitives.tsx   # Thẻ thống kê, badge trạng thái AI, loading/empty/error, toast
│   │   ├── types/index.ts         # TypeScript interfaces
│   │   ├── App.tsx                # Điều phối đăng nhập & phân quyền giao diện
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
└── README.md
```

---

## 2. Trạng thái triển khai & Minh bạch AI

Hệ thống phân biệt rõ 3 trạng thái AI (`AI_PIPELINE_MODE` trong `.env`):
1. `local_model`: Đã tích hợp mô hình AI nội bộ (Whisper, pyannote.audio, PaddleOCR, OpenCV/FFmpeg).
2. `external_api`: Sử dụng API AI bên ngoài thông qua biến môi trường (`OPENAI_API_KEY` / `GEMINI_API_KEY`).
3. `simulated` *(mặc định khi chưa cấu hình API key/model)*: Pipeline chạy cấu trúc thật và lưu dữ liệu vào CSDL, nhưng nội dung AI được gắn nhãn rõ ràng là **`AI Mô phỏng`**, không giả lập kết quả như AI thật.

- **Chức năng đã hoàn thành (chạy thực tế với CSDL & API):**
  - Xác thực JWT, mã hóa mật khẩu `bcrypt`, phân quyền RBAC 3 vai trò ở backend.
  - Dashboard riêng cho Sinh viên, Giảng viên, Nhà trường với biểu đồ Recharts và dữ liệu nhất quán từ CSDL.
  - CRUD bài giảng, tải tệp thực tế (`.mp4`, `.mov`, `.mp3`, `.wav`, `.m4a`, `.pdf`, `.pptx`, `.docx`, `.txt`), xuất báo cáo & tóm tắt `.md`.
  - Trang Lecture Detail đồng bộ Video/Timeline – Slide – Transcript (bấm đoạn transcript nhảy tới đúng slide & timestamp).
  - Tìm kiếm kiến thức trong bài giảng và Trợ lý học tập RAG truy xuất trực tiếp trên transcript & slide thực tế của bài giảng.
  - Làm bài kiểm tra trắc nghiệm & tự luận, chấm điểm tự động và giải thích đáp án.
  - Quản lý người dùng (tạo mới, khóa/mở khóa), quản lý Khoa & Môn học, theo dõi Processing Jobs & System Logs.
- **Chức năng đang mô phỏng:**
  - Sinh nội dung ASR, Diarization, Slide OCR, Summary, Quiz và Gesture/Posture Analysis trong `orchestrator.py` khi `AI_PIPELINE_MODE=simulated` (chưa gắn trọng số Whisper/pyannote/PaddleOCR/LLM thực).

---

## 3. Hướng dẫn cài đặt & Khởi chạy

### Yêu cầu môi trường
- Python 3.11+ (đã kiểm thử với Python 3.13)
- Node.js 20+ và npm

### Bước 1: Cấu hình file `.env`
Sao chép file mẫu ở `backend/.env.example` thành `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
Mặc định hệ thống sử dụng SQLite (`sqlite:///./lectureai.db`) để chạy ngay không cần cài PostgreSQL. Nếu dùng PostgreSQL, cập nhật `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/lectureai`.

### Bước 2: Cài đặt & Chạy Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Khi khởi động lần đầu, backend tự động tạo toàn bộ bảng CSDL và nạp dữ liệu mẫu (seeding). Tài liệu Swagger API có tại: `http://127.0.0.1:8000/docs`.

### Bước 3: Cài đặt & Chạy Frontend (React + Vite + TypeScript)
```bash
cd frontend
npm install
npm run dev
```
Truy cập ứng dụng tại: `http://localhost:5173`.

---

## 4. Tài khoản Demo cho 3 vai trò

| Vai trò | Email | Mật khẩu |
| :--- | :--- | :--- |
| **Sinh viên (Student)** | `student@lectureai.edu.vn` | `Student@123` |
| **Giảng viên (Lecturer)** | `lecturer@lectureai.edu.vn` | `Lecturer@123` |
| **Nhà trường (Administrator)** | `admin@lectureai.edu.vn` | `Admin@123` |

*(Trang đăng nhập có sẵn nút chọn nhanh 3 tài khoản demo để kiểm thử thuận tiện).*

---

## 5. Kiểm thử

- **Build Frontend:** `cd frontend && npm run build`
- **Kiểm thử Backend API & RBAC:** Chạy server `uvicorn app.main:app --port 8000` và kiểm tra `/api/health`, đăng nhập 3 vai trò, phân quyền `403`, CRUD bài giảng, upload tệp, pipeline AI và hỏi đáp RAG.
