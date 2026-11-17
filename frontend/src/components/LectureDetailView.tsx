import React, { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  BookmarkCheck,
  BookmarkPlus,
  Bot,
  Clock,
  Download,
  FileText,
  Layers,
  ListChecks,
  MessageSquare,
  Play,
  Search,
  Send,
  Sparkles,
  User as UserIcon,
} from 'lucide-react';
import { apiRequest, formatTime, getAuthToken } from '../api/client';
import { LectureDetail, RAGResponse, SlideItem } from '../types';
import { AIModeBadge, ErrorState, LoadingState } from './UIPrimitives';

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  rag?: RAGResponse;
}

export function LectureDetailView({
  lectureId,
  userRole,
  onBack,
  onNotify,
}: {
  lectureId: number;
  userRole: string;
  onBack: () => void;
  onNotify: (type: 'success' | 'error' | 'info', text: string) => void;
}) {
  const [lecture, setLecture] = useState<LectureDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentTime, setCurrentTime] = useState(0);
  const [activeSlide, setActiveSlide] = useState<SlideItem | null>(null);
  const [rightTab, setRightTab] = useState<'transcript' | 'summary' | 'assistant'>('transcript');

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[] | null>(null);

  const [chatInput, setChatInput] = useState('');
  const [simplifyMode, setSimplifyMode] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text: 'Xin chào! Tôi là Trợ lý Học tập AI của LectureAI. Hãy đặt câu hỏi về nội dung bài giảng, thuật ngữ chuyên ngành hoặc yêu cầu giải thích đơn giản hơn.',
    },
  ]);

  const [savedSummary, setSavedSummary] = useState(false);
  const mediaRef = useRef<HTMLVideoElement | null>(null);

  const loadDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRequest<LectureDetail>(`/api/lectures/${lectureId}`);
      setLecture(data);
      if (data.slides.length > 0) {
        setActiveSlide(data.slides[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể tải chi tiết bài giảng.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [lectureId]);

  // Sync active slide when currentTime changes
  useEffect(() => {
    if (!lecture || lecture.slides.length === 0) return;
    const matched = lecture.slides.find(
      (s) => currentTime >= s.start_time && currentTime <= s.end_time
    );
    if (matched) {
      setActiveSlide(matched);
    }
  }, [currentTime, lecture]);

  const seekTo = (seconds: number, slideNum?: number | null) => {
    setCurrentTime(seconds);
    if (mediaRef.current) {
      mediaRef.current.currentTime = seconds;
      mediaRef.current.play().catch(() => {});
    }
    if (slideNum && lecture) {
      const sl = lecture.slides.find((s) => s.slide_number === slideNum);
      if (sl) setActiveSlide(sl);
    }
    if (userRole === 'student' && lecture) {
      const pct = Math.min(100, Math.round((seconds / Math.max(1, lecture.duration_seconds)) * 100));
      apiRequest(`/api/student/lectures/${lecture.id}/progress`, {
        method: 'POST',
        body: JSON.stringify({
          last_position_seconds: seconds,
          watched_seconds: Math.round(seconds),
          progress_percent: Math.max(10, pct),
        }),
      }).catch(() => {});
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const res = await apiRequest<{ results: any[] }>(
        `/api/lectures/${lectureId}/search?q=${encodeURIComponent(searchQuery.trim())}`
      );
      setSearchResults(res.results);
    } catch (err: any) {
      onNotify('error', err.message || 'Lỗi tìm kiếm kiến thức.');
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = chatInput.trim();
    if (!q || chatLoading) return;
    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setChatInput('');
    setChatLoading(true);
    try {
      const res = await apiRequest<RAGResponse>(`/api/lectures/${lectureId}/ask`, {
        method: 'POST',
        body: JSON.stringify({ question: q, simplify: simplifyMode }),
      });
      setMessages((prev) => [...prev, { role: 'assistant', text: res.answer, rag: res }]);
    } catch (err: any) {
      onNotify('error', err.message || 'Không thể kết nối trợ lý AI.');
    } finally {
      setChatLoading(false);
    }
  };

  const handleSaveSummary = async () => {
    if (userRole !== 'student') {
      onNotify('info', 'Chỉ tài khoản sinh viên mới lưu tiến độ cá nhân.');
      return;
    }
    try {
      await apiRequest(`/api/student/lectures/${lectureId}/progress`, {
        method: 'POST',
        body: JSON.stringify({ saved_summary: !savedSummary }),
      });
      setSavedSummary(!savedSummary);
      onNotify('success', !savedSummary ? 'Đã lưu bản tóm tắt vào hồ sơ học tập.' : 'Đã bỏ lưu tóm tắt.');
    } catch (err: any) {
      onNotify('error', err.message);
    }
  };

  const handleExportSummary = async () => {
    try {
      const md = await apiRequest<string>(`/api/lectures/${lectureId}/summary/export`);
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tom-tat-bai-giang-${lectureId}.md`;
      a.click();
      URL.revokeObjectURL(url);
      onNotify('success', 'Đã xuất bản tóm tắt bài giảng (.md).');
    } catch (err: any) {
      onNotify('error', err.message || 'Xuất tóm tắt thất bại.');
    }
  };

  if (loading) return <LoadingState message="Đang tải dữ liệu đa phương thức của bài giảng..." />;
  if (error || !lecture) return <ErrorState message={error || 'Không tìm thấy bài giảng'} onRetry={loadDetail} />;

  const videoFile = lecture.files.find((f) => f.file_type === 'video' || f.file_type === 'audio');
  const token = getAuthToken();

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <ArrowLeft className="h-4 w-4" />
            Quay lại
          </button>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                {lecture.course_code}
              </span>
              <AIModeBadge mode={lecture.ai_mode} />
            </div>
            <h1 className="mt-1 text-lg font-bold text-slate-900">{lecture.title}</h1>
            <p className="text-xs text-slate-500">
              {lecture.course_title} • Giảng viên: {lecture.lecturer_name} • Thời lượng: {formatTime(lecture.duration_seconds)}
            </p>
          </div>
        </div>

        {/* Knowledge Search */}
        <form onSubmit={handleSearch} className="flex w-full sm:w-80 items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiến thức trong slide & lời giảng..."
              className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
          >
            Tìm
          </button>
        </form>
      </div>

      {/* Search Results Drawer */}
      {searchResults !== null && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-blue-900">
              Kết quả tìm kiếm cho "{searchQuery}" ({searchResults.length} kết quả)
            </p>
            <button
              onClick={() => setSearchResults(null)}
              className="text-xs font-medium text-blue-700 hover:underline"
            >
              Đóng kết quả
            </button>
          </div>
          {searchResults.length === 0 ? (
            <p className="text-xs text-slate-600">Không tìm thấy từ khóa phù hợp trong slide hoặc transcript.</p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2">
              {searchResults.map((r, idx) => (
                <button
                  key={idx}
                  onClick={() => seekTo(r.timestamp_seconds, r.slide_number)}
                  className="text-left rounded-lg border border-blue-200 bg-white p-2.5 hover:border-blue-400 transition"
                >
                  <div className="flex items-center gap-2 text-[11px] font-semibold text-blue-700">
                    <span>{r.type === 'slide' ? 'Slide' : 'Transcript'}</span>
                    {r.slide_number && <span>• Slide {r.slide_number}</span>}
                    <span>• {formatTime(r.timestamp_seconds)}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-700 line-clamp-2">{r.text}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main 2-Column Multimodal Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Video + Slide + Timeline */}
        <div className="lg:col-span-7 space-y-5">
          {/* Video / Interactive Player */}
          <div className="rounded-xl border border-slate-200 bg-slate-900 overflow-hidden shadow-sm">
            {videoFile ? (
              <video
                ref={mediaRef}
                controls
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                className="w-full aspect-video bg-black"
                src={`${videoFile.url}?token=${encodeURIComponent(token || '')}`}
              />
            ) : (
              <div className="aspect-video flex flex-col items-center justify-center p-6 text-center text-white bg-gradient-to-br from-slate-800 to-slate-900">
                <Play className="h-12 w-12 text-blue-400 mb-3" />
                <p className="text-sm font-semibold">Trình phát đồng bộ đa phương thức</p>
                <p className="mt-1 text-xs text-slate-300 max-w-md">
                  Bài giảng mẫu sử dụng timeline tương tác. Hãy kéo thanh thời gian bên dưới hoặc bấm vào bất kỳ đoạn transcript / slide nào để đồng bộ thời điểm.
                </p>
                <div className="mt-5 w-full max-w-md">
                  <input
                    type="range"
                    min={0}
                    max={lecture.duration_seconds || 1800}
                    value={currentTime}
                    onChange={(e) => seekTo(Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[11px] text-slate-300 mt-1">
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(lecture.duration_seconds)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Synchronized Slide Viewer */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Slide đồng bộ theo thời gian</h3>
              </div>
              <div className="flex items-center gap-1.5">
                {lecture.slides.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => seekTo(s.start_time, s.slide_number)}
                    className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                      activeSlide?.id === s.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Slide {s.slide_number}
                  </button>
                ))}
              </div>
            </div>

            {activeSlide ? (
              <div className="rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50/70 to-white p-5">
                <div className="flex items-center justify-between text-xs text-blue-700 font-medium mb-2">
                  <span>Slide {activeSlide.slide_number} / {lecture.slides.length}</span>
                  <span>{formatTime(activeSlide.start_time)} – {formatTime(activeSlide.end_time)}</span>
                </div>
                <h4 className="text-base font-bold text-slate-900">{activeSlide.title}</h4>
                <p className="mt-2 text-xs text-slate-600 leading-relaxed">{activeSlide.ocr_text}</p>
                {activeSlide.bullet_points.length > 0 && (
                  <ul className="mt-3 space-y-1.5">
                    {activeSlide.bullet_points.map((bp, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-800">
                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-blue-600 shrink-0" />
                        <span>{bp}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Chưa có dữ liệu slide.</p>
            )}
          </div>

          {/* Timeline & Main Topics */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="h-4 w-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Timeline nội dung & Chủ đề chính</h3>
            </div>
            <div className="space-y-2">
              {lecture.segments.map((seg) => (
                <button
                  key={seg.id}
                  onClick={() => seekTo(seg.start_time, seg.slide_number)}
                  className="flex w-full items-start justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50/70 p-3 text-left hover:border-blue-300 hover:bg-blue-50/40 transition"
                >
                  <div>
                    <p className="text-xs font-semibold text-slate-900">{seg.title}</p>
                    <p className="mt-0.5 text-[11px] text-slate-500 line-clamp-1">{seg.description}</p>
                  </div>
                  <span className="shrink-0 rounded bg-white px-2 py-0.5 text-[11px] font-semibold text-blue-700 border border-blue-100">
                    {formatTime(seg.start_time)}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Transcript / Summary / AI Assistant */}
        <div className="lg:col-span-5 flex flex-col rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden max-h-[820px]">
          <div className="grid grid-cols-3 border-b border-slate-200 bg-slate-50">
            <button
              onClick={() => setRightTab('transcript')}
              className={`flex items-center justify-center gap-1.5 py-3 text-xs font-semibold border-b-2 transition ${
                rightTab === 'transcript'
                  ? 'border-blue-600 text-blue-600 bg-white'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Transcript
            </button>
            <button
              onClick={() => setRightTab('summary')}
              className={`flex items-center justify-center gap-1.5 py-3 text-xs font-semibold border-b-2 transition ${
                rightTab === 'summary'
                  ? 'border-blue-600 text-blue-600 bg-white'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <ListChecks className="h-3.5 w-3.5" />
              Tóm tắt
            </button>
            <button
              onClick={() => setRightTab('assistant')}
              className={`flex items-center justify-center gap-1.5 py-3 text-xs font-semibold border-b-2 transition ${
                rightTab === 'assistant'
                  ? 'border-blue-600 text-blue-600 bg-white'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Bot className="h-3.5 w-3.5" />
              Trợ lý AI
            </button>
          </div>

          {/* Tab 1: Transcript */}
          {rightTab === 'transcript' && (
            <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
              <p className="text-[11px] text-slate-500">
                Bấm vào bất kỳ đoạn lời giảng nào để nhảy tới đúng thời điểm video và slide tương ứng.
              </p>
              {lecture.transcripts.map((tr) => {
                const isActive = currentTime >= tr.start_time && currentTime <= tr.end_time;
                const isStudent = tr.speaker_label === 'SPEAKER_01';
                return (
                  <button
                    key={tr.id}
                    onClick={() => seekTo(tr.start_time, tr.slide_number)}
                    className={`w-full text-left rounded-xl border p-3 transition ${
                      isActive
                        ? 'border-blue-500 bg-blue-50/70'
                        : 'border-slate-200 hover:border-blue-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                            isStudent ? 'bg-indigo-100 text-indigo-700' : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          <UserIcon className="h-2.5 w-2.5" />
                          {tr.speaker_name}
                        </span>
                        {tr.slide_number && (
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
                            Slide {tr.slide_number}
                          </span>
                        )}
                        {tr.is_repeated_emphasis && (
                          <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800">
                            Nhấn mạnh
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] font-mono text-blue-600">{formatTime(tr.start_time)}</span>
                    </div>
                    <p className="text-xs text-slate-800 leading-relaxed">{tr.text}</p>
                  </button>
                );
              })}
            </div>
          )}

          {/* Tab 2: Summary */}
          {rightTab === 'summary' && (
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {lecture.summary ? (
                <>
                  <div className="flex items-center justify-between gap-2">
                    <AIModeBadge mode={lecture.summary.ai_mode} />
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleSaveSummary}
                        className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        {savedSummary ? <BookmarkCheck className="h-3.5 w-3.5 text-emerald-600" /> : <BookmarkPlus className="h-3.5 w-3.5" />}
                        {savedSummary ? 'Đã lưu' : 'Lưu'}
                      </button>
                      <button
                        onClick={handleExportSummary}
                        className="flex items-center gap-1 rounded-lg bg-blue-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-blue-700"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Xuất .MD
                      </button>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500">Tổng quan bài học</h4>
                    <p className="mt-1 text-xs text-slate-700 leading-relaxed">{lecture.summary.overview}</p>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500">Các ý chính</h4>
                    <ul className="mt-1.5 space-y-1">
                      {lecture.summary.key_points.map((kp, idx) => (
                        <li key={idx} className="text-xs text-slate-800 flex items-start gap-2">
                          <span className="text-blue-600 font-bold">•</span>
                          <span>{kp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500">Thuật ngữ chuyên ngành</h4>
                    <div className="mt-1.5 space-y-2">
                      {lecture.summary.technical_terms.map((t, idx) => (
                        <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-blue-800">{t.term}</span>
                            {t.timestamp !== undefined && (
                              <button
                                onClick={() => seekTo(t.timestamp || 0, t.slide_number)}
                                className="text-[11px] font-semibold text-blue-600 hover:underline"
                              >
                                Slide {t.slide_number} • {formatTime(t.timestamp || 0)}
                              </button>
                            )}
                          </div>
                          <p className="mt-1 text-xs text-slate-600">{t.definition}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500">Nội dung cần ghi nhớ</h4>
                    <ul className="mt-1.5 space-y-1">
                      {lecture.summary.takeaways.map((tk, idx) => (
                        <li key={idx} className="text-xs text-emerald-800 bg-emerald-50 rounded-md px-2.5 py-1.5">
                          ✓ {tk}
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              ) : (
                <p className="text-xs text-slate-500">Bài giảng chưa có bản tóm tắt.</p>
              )}
            </div>
          )}

          {/* Tab 3: AI Learning Assistant (RAG) */}
          {rightTab === 'assistant' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2 bg-slate-50/60">
                <span className="text-[11px] font-medium text-slate-600 flex items-center gap-1">
                  <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                  Hỏi đáp RAG theo Slide & Transcript
                </span>
                <label className="flex items-center gap-1.5 text-[11px] font-medium text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simplifyMode}
                    onChange={(e) => setSimplifyMode(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600"
                  />
                  Giải thích đơn giản hơn
                </label>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`rounded-xl p-3 text-xs leading-relaxed ${
                      m.role === 'user'
                        ? 'ml-8 bg-blue-600 text-white'
                        : 'mr-4 border border-slate-200 bg-slate-50 text-slate-800'
                    }`}
                  >
                    <p className="whitespace-pre-line">{m.text}</p>
                    {m.rag && m.rag.citations.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-slate-200 space-y-1.5">
                        <p className="text-[10px] font-bold uppercase text-slate-500">Nguồn trích dẫn từ bài giảng:</p>
                        {m.rag.citations.map((c, cIdx) => (
                          <button
                            key={cIdx}
                            onClick={() => seekTo(c.timestamp_seconds, c.slide_number)}
                            className="block w-full text-left rounded-lg bg-white border border-blue-200 px-2.5 py-1.5 hover:bg-blue-50 transition"
                          >
                            <span className="text-[11px] font-semibold text-blue-700">
                              {c.slide_number ? `Slide ${c.slide_number}` : c.source_type} • {c.timestamp_formatted}
                            </span>
                            <p className="text-[11px] text-slate-600 line-clamp-2 mt-0.5">{c.excerpt}</p>
                          </button>
                        ))}
                        <p className="text-[10px] text-slate-400 italic">{m.rag.disclaimer}</p>
                      </div>
                    )}
                  </div>
                ))}
                {chatLoading && (
                  <div className="text-xs text-slate-500 italic">Đang truy xuất kiến thức từ bài giảng...</div>
                )}
              </div>

              <form onSubmit={handleAsk} className="border-t border-slate-200 p-3 flex items-center gap-2 bg-white">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Hỏi về khái niệm, slide hoặc công thức..."
                  className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="rounded-lg bg-blue-600 p-2 text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
