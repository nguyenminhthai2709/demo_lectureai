from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # student, lecturer, admin
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), default="")

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    student_code = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    taught_courses = relationship("Course", back_populates="lecturer")
    lectures = relationship("Lecture", back_populates="lecturer")
    learning_progress = relationship("LearningProgress", back_populates="student", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    users = relationship("User", back_populates="department")
    courses = relationship("Course", back_populates="department")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    credits = Column(Integer, default=3)
    semester = Column(String(50), default="HK1 2026-2027")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    lecturer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    department = relationship("Department", back_populates="courses")
    lecturer = relationship("User", back_populates="taught_courses")
    classes = relationship("CourseClass", back_populates="course", cascade="all, delete-orphan")
    lectures = relationship("Lecture", back_populates="course", cascade="all, delete-orphan")


class CourseClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    semester = Column(String(50), default="HK1 2026-2027")
    schedule = Column(String(150), default="Thứ 2, 08:00 - 10:30")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    course = relationship("Course", back_populates="classes")
    enrollments = relationship("Enrollment", back_populates="course_class", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "class_id", name="uq_student_class"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=utcnow)

    student = relationship("User", back_populates="enrollments")
    course_class = relationship("CourseClass", back_populates="enrollments")


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    topic = Column(String(150), default="")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lecturer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    duration_seconds = Column(Integer, default=0)
    ai_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    ai_mode = Column(String(50), default="simulated")  # simulated, external_api, local_model
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    course = relationship("Course", back_populates="lectures")
    lecturer = relationship("User", back_populates="lectures")
    files = relationship("LectureFile", back_populates="lecture", cascade="all, delete-orphan")
    speakers = relationship("Speaker", back_populates="lecture", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="lecture", cascade="all, delete-orphan", order_by="Transcript.start_time")
    slides = relationship("Slide", back_populates="lecture", cascade="all, delete-orphan", order_by="Slide.slide_number")
    segments = relationship("LectureSegment", back_populates="lecture", cascade="all, delete-orphan", order_by="LectureSegment.start_time")
    summary = relationship("Summary", back_populates="lecture", uselist=False, cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lecture", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="lecture", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="lecture", uselist=False, cascade="all, delete-orphan")
    learning_progress = relationship("LearningProgress", back_populates="lecture", cascade="all, delete-orphan")


class LectureFile(Base):
    __tablename__ = "lecture_files"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    file_type = Column(String(30), nullable=False)  # video, audio, slide, document
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), default="application/octet-stream")
    file_size_bytes = Column(Integer, default=0)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    lecture = relationship("Lecture", back_populates="files")


class Speaker(Base):
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    speaker_label = Column(String(50), nullable=False)  # SPEAKER_00, SPEAKER_01
    display_name = Column(String(100), nullable=False)  # Giảng viên, Sinh viên
    speaking_duration_seconds = Column(Float, default=0.0)

    lecture = relationship("Lecture", back_populates="speakers")
    transcripts = relationship("Transcript", back_populates="speaker")


class Slide(Base):
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    slide_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    ocr_text = Column(Text, default="")
    bullet_points = Column(JSON, default=list)
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    image_url = Column(String(500), nullable=True)

    lecture = relationship("Lecture", back_populates="slides")
    transcripts = relationship("Transcript", back_populates="slide")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=True)
    slide_id = Column(Integer, ForeignKey("slides.id"), nullable=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, default=0.95)
    is_repeated_emphasis = Column(Boolean, default=False)

    lecture = relationship("Lecture", back_populates="transcripts")
    speaker = relationship("Speaker", back_populates="transcripts")
    slide = relationship("Slide", back_populates="transcripts")


class LectureSegment(Base):
    __tablename__ = "lecture_segments"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    slide_number = Column(Integer, nullable=True)
    keywords = Column(JSON, default=list)

    lecture = relationship("Lecture", back_populates="segments")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), unique=True, nullable=False)
    overview = Column(Text, default="")
    key_points = Column(JSON, default=list)
    important_concepts = Column(JSON, default=list)
    technical_terms = Column(JSON, default=list)  # list of {term, definition, slide_number, timestamp}
    examples = Column(JSON, default=list)
    conclusion = Column(Text, default="")
    takeaways = Column(JSON, default=list)
    ai_mode = Column(String(50), default="simulated")
    updated_at = Column(DateTime(timezone=True), default=utcnow)

    lecture = relationship("Lecture", back_populates="summary")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    ai_mode = Column(String(50), default="simulated")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    lecture = relationship("Lecture", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_type = Column(String(30), default="mcq")  # mcq, essay
    prompt = Column(Text, nullable=False)
    options = Column(JSON, default=list)  # for mcq: ["A", "B", "C", "D"]
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, default="")
    slide_number = Column(Integer, nullable=True)
    timestamp_seconds = Column(Float, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers = Column(JSON, default=dict)  # {question_id: answer}
    score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    submitted_at = Column(DateTime(timezone=True), default=utcnow)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User", back_populates="quiz_attempts")


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = (UniqueConstraint("student_id", "lecture_id", name="uq_student_lecture_progress"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    progress_percent = Column(Float, default=0.0)
    watched_seconds = Column(Integer, default=0)
    last_position_seconds = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    needs_review = Column(Boolean, default=False)
    saved_summary = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student = relationship("User", back_populates="learning_progress")
    lecture = relationship("Lecture", back_populates="learning_progress")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    status = Column(String(30), default="queued")  # queued, running, completed, failed
    current_step = Column(String(100), default="Khởi tạo")
    progress_percent = Column(Integer, default=0)
    ai_mode = Column(String(50), default="simulated")
    steps_log = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    lecture = relationship("Lecture", back_populates="processing_jobs")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), unique=True, nullable=False)
    speaking_rate_wpm = Column(Float, default=135.0)
    lecturer_talk_ratio = Column(Float, default=0.82)
    interaction_ratio = Column(Float, default=0.18)
    topic_time_distribution = Column(JSON, default=list)  # [{topic, seconds, percent}]
    repeated_concepts = Column(JSON, default=list)
    student_engagement_score = Column(Float, default=78.0)  # Based on views/quiz/completion
    gesture_analysis = Column(JSON, default=dict)  # Posture/gesture/slide interaction with disclaimers
    improvement_suggestions = Column(JSON, default=list)
    ai_mode = Column(String(50), default="simulated")
    updated_at = Column(DateTime(timezone=True), default=utcnow)

    lecture = relationship("Lecture", back_populates="analytics")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR
    module = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
