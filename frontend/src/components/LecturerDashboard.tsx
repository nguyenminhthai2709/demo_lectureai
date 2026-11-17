import React, { useEffect, useState } from 'react';
import {
  Activity,
  BarChart3,
  BookOpen,
  Clock,
  Download,
  Eye,
  FileUp,
  Info,
  Play,
  Plus,
  Sparkles,
  Trash2,
  Users,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest, formatTime } from '../api/client';
import {
  AIModeBadge,
  AIStatusBadge,
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from './UIPrimitives';

export function LecturerDashboard({
  activeTab,
  onOpenLecture,
  onNotify,
}: {
  activeTab: string;
  onOpenLecture: (id: number) => void;
  onNotify: (type: 'success' | 'error' | 'info', text: string) => void;
}) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create lecture form
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [description, setDescription] = useState('');
  const [courseId, setCourseId] = useState<number>(0);
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Analytics selection
  const [selectedLectureId, setSelectedLectureId] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<any>('/api/lecturer/dashboard');
      setData(res);
      if (res.courses?.length > 0 && courseId === 0) {
        setCourseId(res.courses[0].id);
      }
      if (res.lectures?.length > 0 && !selectedLectureId) {
        setSelectedLectureId(res.lectures[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể tải dữ liệu giảng viên.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadAnalytics = async (lecId: number) => {
    setAnalyticsLoading(true);
    try {
      const res = await apiRequest<any>(`/api/lecturer/lectures/${lecId}/analytics`);
      setAnalytics(res);
    } catch {
      setAnalytics(null);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'analytics' && selectedLectureId) {
      loadAnalytics(selectedLectureId);
    }
  }, [activeTab, selectedLectureId]);

  const handleCreateLecture = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!courseId) return;
    setSubmitting(true);
    try {
      const created = await apiRequest<{ id: number }>('/api/lecturer/lectures', {
        method: 'POST',
        body: JSON.stringify({
          title,
          topic,
          description,
          course_id: courseId,
          duration_seconds: durationMinutes * 60,
          is_published: true,
        }),
      });

      if (uploadFile) {
        const fd = new FormData();
        fd.append('file', uploadFile);
        await apiRequest(`/api/lecturer/lectures/${created.id}/upload`, {
          method: 'POST',
          body: fd,
        });
      }

      onNotify('success', 'Đã tạo bài giảng mới. Bạn có thể bấm "Chạy Pipeline AI" ngay.');
      setTitle('');
      setTopic('');
      setDescription('');
      setUploadFile(null);
      setShowCreate(false);
      await loadDashboard();
    } catch (err: any) {
      onNotify('error', err.message || 'Không thể tạo bài giảng.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunPipeline = async (lecId: number) => {
    try {
      onNotify('info', 'Đang chạy Pipeline 9 bước xử lý đa phương thức...');
      await apiRequest(`/api/lecturer/lectures/${lecId}/process`, { method: 'POST' });
      onNotify('success', 'Xử lý AI hoàn tất! Đã tạo Transcript, Slide OCR, Tóm tắt & Quiz.');
      await loadDashboard();
    } catch (err: any) {
      onNotify('error', err.message || 'Lỗi khi chạy Pipeline AI.');
    }
  };

  const handleDeleteLecture = async (lecId: number) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa bài giảng này?')) return;
    try {
      await apiRequest(`/api/lecturer/lectures/${lecId}`, { method: 'DELETE' });
      onNotify('success', 'Đã xóa bài giảng.');
      await loadDashboard();
    } catch (err: any) {
      onNotify('error', err.message || 'Không thể xóa bài giảng.');
    }
  };

  const handleExportReport = async (lecId: number) => {
    try {
      const md = await apiRequest<string>(`/api/lecturer/lectures/${lecId}/report`);
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bao-cao-giang-day-${lecId}.md`;
      a.click();
      URL.revokeObjectURL(url);
      onNotify('success', 'Đã xuất báo cáo bài giảng (.md).');
    } catch (err: any) {
      onNotify('error', err.message);
    }
  };

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error || 'Lỗi dữ liệu'} onRetry={loadDashboard} />;

  const { stats, courses, lectures } = data;

  if (activeTab === 'overview') {
    const chartData = lectures.slice(0, 6).map((l: any) => ({
      name: l.title.length > 18 ? l.title.slice(0, 18) + '...' : l.title,
      views: l.view_count,
      minutes: Math.round((l.duration_seconds || 0) / 60),
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Môn học phụ trách" value={stats.total_courses} icon={BookOpen} accent="blue" />
          <StatCard title="Tổng số bài giảng" value={stats.total_lectures} subtitle={`${stats.completed_ai_lectures} đã xử lý AI`} icon={Sparkles} accent="indigo" />
          <StatCard title="Thời lượng giảng dạy" value={`${stats.total_duration_hours} giờ`} icon={Clock} accent="emerald" />
          <StatCard title="Tốc độ nói TB" value={`${stats.avg_speaking_wpm} WPM`} subtitle={`Tương tác: ${stats.avg_interaction_percent}%`} icon={Activity} accent="amber" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Lượt tiếp cận bài giảng của sinh viên</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="views" name="Lượt xem" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Học phần đang giảng dạy</h3>
            <div className="space-y-2.5">
              {courses.map((c: any) => (
                <div key={c.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-blue-700">{c.code}</span>
                    <span className="text-[11px] text-slate-500">{c.lecture_count} bài giảng</span>
                  </div>
                  <p className="mt-1 text-xs font-semibold text-slate-900">{c.title}</p>
                  <p className="text-[11px] text-slate-500">{c.semester} • {c.credits} tín chỉ</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'manage') {
    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">Quản lý bài giảng & Tải lên đa phương thức</h3>
            <p className="text-xs text-slate-500">Hỗ trợ Video (MP4, MOV), Audio (MP3, WAV, M4A), Slide (PDF, PPTX) và Tài liệu (DOCX, TXT).</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Tạo bài giảng mới
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreateLecture} className="rounded-xl border border-blue-200 bg-white p-5 shadow-sm space-y-4">
            <h4 className="text-sm font-bold text-slate-900">Thông tin bài giảng mới</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tiêu đề bài giảng *</label>
                <input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ví dụ: Bài 5: Tối ưu hóa truy vấn Vector"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Chủ đề chính *</label>
                <input
                  required
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Ví dụ: Vector Database & HNSW"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Học phần *</label>
                <select
                  value={courseId}
                  onChange={(e) => setCourseId(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
                >
                  {courses.map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.code} - {c.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Thời lượng ước tính (phút)</label>
                <input
                  type="number"
                  min={1}
                  max={240}
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Mô tả ngắn</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Đính kèm Video / Audio / Slide / Tài liệu (tùy chọn)
              </label>
              <div className="flex items-center gap-3">
                <label className="inline-flex items-center gap-2 rounded-lg border border-dashed border-slate-300 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer">
                  <FileUp className="h-4 w-4 text-blue-600" />
                  <span>{uploadFile ? uploadFile.name : 'Chọn tệp (.mp4, .mp3, .pdf, .pptx, .txt...)'}</span>
                  <input
                    type="file"
                    accept=".mp4,.mov,.mp3,.wav,.m4a,.pdf,.pptx,.docx,.txt"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-5 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? 'Đang lưu...' : 'Lưu bài giảng'}
              </button>
            </div>
          </form>
        )}

        {lectures.length === 0 ? (
          <EmptyState title="Chưa có bài giảng" description="Hãy tạo bài giảng đầu tiên của bạn." />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 font-semibold">Bài giảng</th>
                  <th className="px-4 py-3 font-semibold">Học phần</th>
                  <th className="px-4 py-3 font-semibold">Trạng thái AI</th>
                  <th className="px-4 py-3 font-semibold">Lượt xem</th>
                  <th className="px-4 py-3 font-semibold text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lectures.map((lec: any) => (
                  <tr key={lec.id} className="hover:bg-slate-50/70">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-slate-900">{lec.title}</p>
                      <p className="text-[11px] text-slate-500">{lec.topic} • {formatTime(lec.duration_seconds)}</p>
                    </td>
                    <td className="px-4 py-3 font-medium text-blue-700">{lec.course_code}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <AIStatusBadge status={lec.ai_status} />
                        <AIModeBadge mode={lec.ai_mode} />
                      </div>
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-700">{lec.view_count}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onOpenLecture(lec.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1 font-medium text-slate-700 hover:bg-slate-100"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Xem
                        </button>
                        <button
                          onClick={() => handleRunPipeline(lec.id)}
                          className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-2.5 py-1 font-medium text-white hover:bg-blue-700"
                        >
                          <Play className="h-3.5 w-3.5" />
                          Chạy AI
                        </button>
                        <button
                          onClick={() => handleDeleteLecture(lec.id)}
                          className="inline-flex items-center rounded-md border border-red-200 p-1.5 text-red-600 hover:bg-red-50"
                          title="Xóa bài giảng"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  if (activeTab === 'analytics') {
    const ratioData = analytics
      ? [
          { name: 'Giảng viên trình bày', value: Math.round(analytics.lecturer_talk_ratio * 100) },
          { name: 'Trao đổi / Sinh viên', value: Math.round(analytics.interaction_ratio * 100) },
        ]
      : [];
    const COLORS = ['#2563eb', '#10b981'];

    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-blue-600" />
            <div>
              <label className="block text-[11px] font-semibold uppercase text-slate-500">Chọn bài giảng phân tích</label>
              <select
                value={selectedLectureId || ''}
                onChange={(e) => setSelectedLectureId(Number(e.target.value))}
                className="mt-0.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold bg-white"
              >
                {lectures.map((l: any) => (
                  <option key={l.id} value={l.id}>
                    {l.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {selectedLectureId && (
            <button
              onClick={() => handleExportReport(selectedLectureId)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700"
            >
              <Download className="h-4 w-4" />
              Xuất báo cáo cải thiện (.MD)
            </button>
          )}
        </div>

        {analyticsLoading ? (
          <LoadingState />
        ) : !analytics ? (
          <EmptyState title="Chưa có dữ liệu phân tích" description="Hãy chạy Pipeline AI cho bài giảng này ở mục Quản lý bài giảng." />
        ) : (
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard title="Tốc độ nói trung bình" value={`${analytics.speaking_rate_wpm} từ/phút`} icon={Activity} accent="blue" />
              <StatCard title="Tỷ lệ trao đổi lớp học" value={`${Math.round(analytics.interaction_ratio * 100)}%`} icon={Users} accent="emerald" />
              <StatCard title="Mức độ tiếp cận (View/Quiz)" value={`${analytics.student_engagement_score}/100`} icon={Eye} accent="indigo" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h4 className="text-sm font-bold text-slate-900 mb-3">Tỷ lệ trình bày vs Trao đổi</h4>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={ratioData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75} label>
                        {ratioData.map((_, index) => (
                          <Cell key={index} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h4 className="text-sm font-bold text-slate-900 mb-3">Thời gian dành cho từng chủ đề</h4>
                <div className="space-y-2.5">
                  {analytics.topic_time_distribution.map((t: any, i: number) => (
                    <div key={i}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-medium text-slate-800 truncate pr-2">{t.topic}</span>
                        <span className="text-slate-500 shrink-0">{Math.round(t.seconds / 60)} phút ({t.percent}%)</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${t.percent}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Gesture & Posture Module with explicit scientific & legal disclaimer */}
            <div className="rounded-xl border border-amber-200 bg-white p-5 shadow-sm space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h4 className="text-sm font-bold text-slate-900">Phân tích Video, Tư thế & Tương tác Slide (Module mở rộng)</h4>
                <AIModeBadge mode={analytics.gesture_analysis?.ai_mode || 'simulated'} />
              </div>

              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 flex items-start gap-2.5 text-xs text-amber-900">
                <Info className="h-4 w-4 shrink-0 mt-0.5 text-amber-700" />
                <p>{analytics.gesture_analysis?.scientific_disclaimer}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="rounded-lg bg-slate-50 p-3.5 border border-slate-200">
                  <p className="font-bold text-slate-800 mb-2">Chuyển động & Cử chỉ quan sát được</p>
                  <p>Tỷ lệ đứng giảng: <strong>{Math.round((analytics.gesture_analysis?.posture_and_movement?.standing_ratio || 0) * 100)}%</strong></p>
                  <p className="mt-1">Mức độ di chuyển: <strong>{analytics.gesture_analysis?.posture_and_movement?.movement_activity_level}</strong></p>
                  <p className="mt-1">Tần suất cử chỉ tay: <strong>{analytics.gesture_analysis?.posture_and_movement?.hand_gesture_frequency_per_min} lần/phút</strong></p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3.5 border border-slate-200">
                  <p className="font-bold text-slate-800 mb-2">Thời điểm tương tác với Slide</p>
                  <ul className="space-y-1.5">
                    {(analytics.gesture_analysis?.posture_and_movement?.slide_pointing_events || []).map((ev: any, idx: number) => (
                      <li key={idx} className="text-slate-700">
                        • <strong>{formatTime(ev.timestamp_seconds)}</strong> (Slide {ev.slide_number}): {ev.note}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Improvement suggestions */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h4 className="text-sm font-bold text-slate-900 mb-2">Đề xuất cải thiện bài giảng</h4>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {analytics.improvement_suggestions.map((s: string, i: number) => (
                  <li key={i} className="rounded-lg bg-blue-50/60 border border-blue-100 px-3 py-2">
                    • {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}
