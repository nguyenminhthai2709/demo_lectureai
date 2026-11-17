export type UserRole = 'student' | 'lecturer' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  role_display: string;
  department_id?: number | null;
  department_name?: string | null;
  student_code?: string | null;
  is_active: boolean;
}

export interface AIModeInfo {
  label: string;
  description: string;
  badge_color: string;
}

export interface LectureSummaryItem {
  id: number;
  title: string;
  description?: string;
  topic: string;
  course_id: number;
  course_code: string;
  course_title: string;
  lecturer_name: string;
  duration_seconds: number;
  ai_status: string;
  ai_mode: string;
  slide_count?: number;
  progress_percent?: number;
  is_completed?: boolean;
  needs_review?: boolean;
  saved_summary?: boolean;
  is_published?: boolean;
  view_count?: number;
  file_count?: number;
  created_at?: string;
}

export interface SlideItem {
  id: number;
  slide_number: number;
  title: string;
  ocr_text: string;
  bullet_points: string[];
  start_time: number;
  end_time: number;
}

export interface TranscriptItem {
  id: number;
  speaker_id?: number;
  speaker_name: string;
  speaker_label: string;
  slide_id?: number;
  slide_number?: number | null;
  start_time: number;
  end_time: number;
  text: string;
  confidence: number;
  is_repeated_emphasis: boolean;
}

export interface SegmentItem {
  id: number;
  title: string;
  description: string;
  start_time: number;
  end_time: number;
  slide_number?: number | null;
  keywords: string[];
}

export interface LectureDetail {
  id: number;
  title: string;
  description: string;
  topic: string;
  course_id: number;
  course_code: string;
  course_title: string;
  lecturer_id: number;
  lecturer_name: string;
  duration_seconds: number;
  ai_status: string;
  ai_mode: string;
  ai_mode_info: AIModeInfo;
  is_published: boolean;
  view_count: number;
  files: {
    id: number;
    file_type: string;
    original_filename: string;
    mime_type: string;
    file_size_bytes: number;
    url: string;
  }[];
  speakers: {
    id: number;
    speaker_label: string;
    display_name: string;
    speaking_duration_seconds: number;
  }[];
  slides: SlideItem[];
  transcripts: TranscriptItem[];
  segments: SegmentItem[];
  summary: {
    overview: string;
    key_points: string[];
    important_concepts: string[];
    technical_terms: {
      term: string;
      definition: string;
      slide_number?: number;
      timestamp?: number;
    }[];
    examples: string[];
    conclusion: string;
    takeaways: string[];
    ai_mode: string;
  } | null;
  quizzes: {
    id: number;
    title: string;
    description: string;
    question_count: number;
  }[];
}

export interface CitationItem {
  source_type: string;
  slide_number?: number | null;
  timestamp_seconds: number;
  timestamp_formatted: string;
  excerpt: string;
  speaker: string;
}

export interface RAGResponse {
  answer: string;
  citations: CitationItem[];
  ai_mode: string;
  ai_mode_label: string;
  disclaimer: string;
}
