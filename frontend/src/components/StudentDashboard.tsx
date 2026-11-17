import React, { useEffect, useState } from 'react';
import {
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  PlayCircle,
  Search,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { apiRequest, formatTime } from '../api/client';
import { LectureSummaryItem } from '../types';
import {
  AIModeBadge,
  AIStatusBadge,
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from './UIPrimitives';

export function StudentDashboard({
  activeTab,
  onOpenLecture,
  onNotify,
}: {
  activeTab: string;
  onOpenLecture: (id: number) => void;
  onNotify: (type: 'success' | 'error' | 'info', text: string) => void;
}) {
  const [dashboard, setDashboard] = useState<any>(null);
  const [lecturesData, setLecturesData] = useState<{ courses: any[]; lectures: LectureSummaryItem[] } | null>(null);
  const [quizzesData, setQuizzesData] = useState<{ quizzes: any[]; attempts: any[] } | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedCourse, setSelectedCourse] = useState<string>('');

  // Quiz state
  const [activeQuiz, setActiveQuiz] = useState<any | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [quizResult, setQuizResult] = useState<any | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'overview') {
        const d = await apiRequest('/api/student/dashboard');
        setDashboard(d);
      } else if (activeTab === 'lectures') {
        const params = new URLSearchParams();
        if (search.trim()) params.set('search', search.trim());
        if (selectedCourse) params.set('course_id', selectedCourse);
        const l = await apiRequest<{ courses: any[]; lectures: LectureSummaryItem[] }>(
          `/api/student/lectures?${params.toString()}`
        );
        setLecturesData(l);
      } else if (activeTab === 'quizzes') {
        const q = await apiRequest<{ quizzes: any[]; attempts: any[] }>('/api/student/quizzes');
        setQuizzesData(q);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể tải dữ liệu sinh viên.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab, selectedCourse]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleSubmitQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeQuiz) return;
    try {
      const res = await apiRequest<any>(`/api/student/quizzes/${activeQuiz.id}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers }),
      });
      setQuizResult(res);
      onNotify('success', `Đã nộp bài! Điểm trắc nghiệm: ${res.score}/${res.max_score}`);
      loadData();
    } catch (err: any) {
      onNotify('error', err.message || 'Lỗi khi nộp bài kiểm tra.');
    }
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  if (activeTab === 'overview' && dashboard) {
    const { stats, recent_lectures, review_items, ai_recommendations } = dashboard;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Bài giảng đã học" value={`${stats.completed_lectures}/${stats.total_lectures}`} icon={BookOpen} accent="blue" />
          <StatCard title="Số giờ học" value={`${stats.study_hours} giờ`} icon={Clock} accent="indigo" />
          <StatCard title="Tiến độ trung bình" value={`${stats.overall_progress_percent}%`} icon={TrendingUp} accent="emerald" />
          <StatCard title="Lượt kiểm tra" value={stats.quiz_attempts_count} icon={Award} accent="amber" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Bài giảng gần đây</h3>
            {recent_lectures.length === 0 ? (
              <EmptyState title="Chưa có bài giảng" description="Bạn chưa đăng ký học phần có bài giảng nào." />
            ) : (
              <div className="space-y-3">
                {recent_lectures.map((lec: LectureSummaryItem) => (
                  <div
                    key={lec.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-4 hover:border-blue-200 transition"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-blue-100 px-2 py-0.5 text-[11px] font-semibold text-blue-800">
                          {lec.course_code}
                        </span>
                        <AIModeBadge mode={lec.ai_mode} />
                      </div>
                      <h4 className="mt-1.5 text-sm font-semibold text-slate-900 truncate">{lec.title}</h4>
                      <p className="text-xs text-slate-500">
                        {lec.lecturer_name} • {formatTime(lec.duration_seconds)} • Tiến độ: {lec.progress_percent}%
                      </p>
                    </div>
                    <button
                      onClick={() => onOpenLecture(lec.id)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 shrink-0"
                    >
                      <PlayCircle className="h-4 w-4" />
                      Vào học
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-5">
            <div className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-5 shadow-sm">
              <div className="flex items-center gap-2 text-blue-800 font-bold text-sm mb-3">
                <Sparkles className="h-4 w-4" />
                <span>Gợi ý học tập từ AI</span>
              </div>
              <ul className="space-y-2.5">
                {ai_recommendations.map((rec: string, i: number) => (
                  <li key={i} className="rounded-lg bg-white border border-blue-100 p-3 text-xs text-slate-700 leading-relaxed">
                    {rec}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-3">Nội dung cần ôn tập</h3>
              {review_items.length === 0 ? (
                <p className="text-xs text-slate-500">Tuyệt vời! Bạn không có bài giảng nào cần ôn gấp.</p>
              ) : (
                <div className="space-y-2">
                  {review_items.map((r: LectureSummaryItem) => (
                    <button
                      key={r.id}
                      onClick={() => onOpenLecture(r.id)}
                      className="w-full text-left rounded-lg border border-amber-200 bg-amber-50/50 p-2.5 hover:bg-amber-50 transition"
                    >
                      <p className="text-xs font-semibold text-slate-900 truncate">{r.title}</p>
                      <p className="text-[11px] text-amber-700 mt-0.5">
                        {r.course_code} • Tiến độ {r.progress_percent}%
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'lectures' && lecturesData) {
    return (
      <div className="space-y-5">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo tên bài giảng, môn học, giảng viên hoặc chủ đề..."
              className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white focus:border-blue-500 focus:outline-none"
          >
            <option value="">Tất cả môn học</option>
            {lecturesData.courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.code} - {c.title}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Tìm kiếm
          </button>
        </form>

        {lecturesData.lectures.length === 0 ? (
          <EmptyState title="Không tìm thấy bài giảng" description="Hãy thử từ khóa khác hoặc chọn tất cả môn học." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {lecturesData.lectures.map((lec) => (
              <div key={lec.id} className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-blue-300 transition">
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                      {lec.course_code}
                    </span>
                    <AIStatusBadge status={lec.ai_status} />
                  </div>
                  <h4 className="mt-3 text-base font-bold text-slate-900 line-clamp-2">{lec.title}</h4>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{lec.description}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                    <span>GV: {lec.lecturer_name}</span>
                    <span>•</span>
                    <span>{lec.slide_count} slides</span>
                    <span>•</span>
                    <span>{formatTime(lec.duration_seconds)}</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-slate-500">Tiến độ học tập</span>
                    <span className="font-semibold text-blue-700">{lec.progress_percent || 0}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden mb-3">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{ width: `${lec.progress_percent || 0}%` }}
                    />
                  </div>
                  <button
                    onClick={() => onOpenLecture(lec.id)}
                    className="w-full rounded-lg bg-blue-600 py-2 text-xs font-semibold text-white hover:bg-blue-700"
                  >
                    Xem & Phân tích bài giảng
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (activeTab === 'quizzes' && quizzesData) {
    return (
      <div className="space-y-6">
        {activeQuiz ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-900">{activeQuiz.title}</h3>
                <p className="text-xs text-slate-500">{activeQuiz.lecture_title}</p>
              </div>
              <button
                onClick={() => {
                  setActiveQuiz(null);
                  setQuizResult(null);
                  setAnswers({});
                }}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Đóng bài kiểm tra
              </button>
            </div>

            <form onSubmit={handleSubmitQuiz} className="space-y-5">
              {activeQuiz.questions.map((q: any, idx: number) => (
                <div key={q.id} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-blue-700">
                      Câu {idx + 1} ({q.question_type === 'mcq' ? 'Trắc nghiệm' : 'Tự luận'})
                    </span>
                    {q.slide_number && (
                      <span className="text-[11px] text-slate-500">Liên quan: Slide {q.slide_number}</span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-slate-900 mb-3">{q.prompt}</p>

                  {q.question_type === 'mcq' ? (
                    <div className="space-y-2">
                      {q.options.map((opt: string) => (
                        <label
                          key={opt}
                          className="flex items-center gap-2.5 rounded-lg border border-slate-200 px-3 py-2 text-xs cursor-pointer hover:bg-blue-50/40"
                        >
                          <input
                            type="radio"
                            name={`q_${q.id}`}
                            value={opt}
                            checked={answers[String(q.id)] === opt}
                            onChange={(e) => setAnswers({ ...answers, [String(q.id)]: e.target.value })}
                          />
                          <span>{opt}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <textarea
                      rows={3}
                      value={answers[String(q.id)] || ''}
                      onChange={(e) => setAnswers({ ...answers, [String(q.id)]: e.target.value })}
                      placeholder="Nhập câu trả lời tự luận của bạn..."
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-xs focus:border-blue-500 focus:outline-none"
                    />
                  )}
                </div>
              ))}

              <button
                type="submit"
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
              >
                Nộp bài & Chấm điểm tự động
              </button>
            </form>

            {quizResult && (
              <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50/60 p-5 space-y-3">
                <div className="flex items-center gap-2 text-emerald-800 font-bold">
                  <CheckCircle2 className="h-5 w-5" />
                  <span>Kết quả trắc nghiệm: {quizResult.score} / {quizResult.max_score} điểm</span>
                </div>
                {quizResult.feedback.map((fb: any, i: number) => (
                  <div key={i} className="rounded-lg bg-white border border-slate-200 p-3 text-xs">
                    <p className="font-semibold text-slate-900">{fb.prompt}</p>
                    <p className="mt-1">
                      Đáp án đúng: <span className="font-semibold text-emerald-700">{fb.correct_answer}</span>
                      {fb.is_correct !== null && (
                        <span className={`ml-2 font-bold ${fb.is_correct ? 'text-emerald-600' : 'text-red-600'}`}>
                          ({fb.is_correct ? 'Chính xác' : 'Chưa đúng'})
                        </span>
                      )}
                    </p>
                    <p className="mt-1 text-slate-600">Giải thích: {fb.explanation}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-3">
              <h3 className="text-sm font-bold text-slate-900">Bộ câu hỏi ôn tập theo bài giảng</h3>
              {quizzesData.quizzes.map((qz) => (
                <div key={qz.id} className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
                        {qz.course_code}
                      </span>
                      <AIModeBadge mode={qz.ai_mode} />
                    </div>
                    <h4 className="mt-1.5 text-sm font-bold text-slate-900">{qz.title}</h4>
                    <p className="text-xs text-slate-500">{qz.questions.length} câu hỏi trắc nghiệm & tự luận</p>
                  </div>
                  <button
                    onClick={() => {
                      setActiveQuiz(qz);
                      setQuizResult(null);
                      setAnswers({});
                    }}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 shrink-0"
                  >
                    Làm bài
                  </button>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-3">Lịch sử làm bài</h3>
              {quizzesData.attempts.length === 0 ? (
                <p className="text-xs text-slate-500">Chưa có lượt làm bài nào.</p>
              ) : (
                <div className="space-y-2.5">
                  {quizzesData.attempts.map((a) => (
                    <div key={a.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs">
                      <p className="font-semibold text-slate-900 truncate">{a.quiz_title}</p>
                      <p className="mt-1 text-blue-700 font-bold">
                        Điểm: {a.score} / {a.max_score}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}
