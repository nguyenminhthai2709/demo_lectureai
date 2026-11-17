import React, { useState } from 'react';
import { GraduationCap, KeyRound, Loader2, Mail, Shield, UserCheck } from 'lucide-react';
import { apiRequest, setAuthToken } from '../api/client';
import { User } from '../types';

const DEMO_ACCOUNTS = [
  { role: 'Sinh viên', email: 'student@lectureai.edu.vn', pass: 'Student@123', color: 'border-blue-200 bg-blue-50 text-blue-800' },
  { role: 'Giảng viên', email: 'lecturer@lectureai.edu.vn', pass: 'Lecturer@123', color: 'border-emerald-200 bg-emerald-50 text-emerald-800' },
  { role: 'Nhà trường', email: 'admin@lectureai.edu.vn', pass: 'Admin@123', color: 'border-indigo-200 bg-indigo-50 text-indigo-800' },
];

export function LoginPage({ onLoginSuccess }: { onLoginSuccess: (user: User) => void }) {
  const [email, setEmail] = useState('student@lectureai.edu.vn');
  const [password, setPassword] = useState('Student@123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<{ access_token: string; user: User }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setAuthToken(res.access_token);
      onLoginSuccess(res.user);
    } catch (err: any) {
      setError(err.message || 'Đăng nhập thất bại.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50">
      {/* Left Brand Panel */}
      <div className="lg:w-1/2 bg-gradient-to-br from-blue-700 via-blue-600 to-blue-800 text-white p-8 lg:p-14 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
              <GraduationCap className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">LectureAI</h1>
              <p className="text-xs text-blue-100">Multimodal Lecture Intelligence Platform</p>
            </div>
          </div>

          <div className="mt-12 max-w-lg">
            <p className="inline-block rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-blue-50">
              Learn Smarter. Teach Better. Understand Deeper.
            </p>
            <h2 className="mt-4 text-3xl lg:text-4xl font-bold leading-tight">
              Phân tích bài giảng đa phương thức bằng AI
            </h2>
            <p className="mt-4 text-sm lg:text-base text-blue-100 leading-relaxed">
              Đồng bộ video, âm thanh, slide và transcript theo từng giây. Tìm kiếm kiến thức chính xác tới từng slide, hỏi đáp RAG có trích dẫn nguồn và phân tích giảng dạy chuyên sâu.
            </p>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="rounded-xl bg-white/10 p-3.5 backdrop-blur">
            <UserCheck className="h-4 w-4 mb-1.5 text-blue-200" />
            <p className="font-semibold">Sinh viên</p>
            <p className="text-blue-100 mt-0.5">Xem đồng bộ slide, hỏi đáp AI & ôn tập</p>
          </div>
          <div className="rounded-xl bg-white/10 p-3.5 backdrop-blur">
            <GraduationCap className="h-4 w-4 mb-1.5 text-blue-200" />
            <p className="font-semibold">Giảng viên</p>
            <p className="text-blue-100 mt-0.5">Tải bài giảng, phân tích tốc độ & tương tác</p>
          </div>
          <div className="rounded-xl bg-white/10 p-3.5 backdrop-blur">
            <Shield className="h-4 w-4 mb-1.5 text-blue-200" />
            <p className="font-semibold">Nhà trường</p>
            <p className="text-blue-100 mt-0.5">Quản trị đào tạo, RBAC & giám sát AI</p>
          </div>
        </div>
      </div>

      {/* Right Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h3 className="text-xl font-bold text-slate-900">Đăng nhập hệ thống</h3>
          <p className="mt-1 text-sm text-slate-500">Chọn tài khoản demo hoặc nhập thông tin đăng nhập của bạn.</p>

          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Tài khoản Demo nhanh
            </p>
            <div className="grid grid-cols-3 gap-2">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => {
                    setEmail(acc.email);
                    setPassword(acc.pass);
                    setError(null);
                  }}
                  className={`rounded-lg border px-2.5 py-2 text-xs font-semibold transition hover:opacity-90 ${acc.color}`}
                >
                  {acc.role}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-xs font-medium text-red-700">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  placeholder="name@lectureai.edu.vn"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Mật khẩu</label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              <span>{loading ? 'Đang xác thực...' : 'Đăng nhập'}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
