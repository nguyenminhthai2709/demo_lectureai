import React, { useEffect, useState } from 'react';
import {
  Activity,
  BookOpen,
  Cpu,
  Database,
  GraduationCap,
  Lock,
  Plus,
  Server,
  ShieldAlert,
  Unlock,
  Users,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest } from '../api/client';
import { AIModeBadge, AIStatusBadge, ErrorState, LoadingState, StatCard } from './UIPrimitives';

export function AdminDashboard({
  activeTab,
  onNotify,
}: {
  activeTab: string;
  onNotify: (type: 'success' | 'error' | 'info', text: string) => void;
}) {
  const [dashboard, setDashboard] = useState<any>(null);
  const [usersData, setUsersData] = useState<any[]>([]);
  const [academic, setAcademic] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create user form
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newPass, setNewPass] = useState('LectureAI@123');
  const [newRole, setNewRole] = useState('student');

  // Create department / course
  const [deptCode, setDeptCode] = useState('');
  const [deptName, setDeptName] = useState('');
  const [courseCode, setCourseCode] = useState('');
  const [courseTitle, setCourseTitle] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'overview' || activeTab === 'system') {
        const d = await apiRequest('/api/admin/dashboard');
        setDashboard(d);
      } else if (activeTab === 'users') {
        const u = await apiRequest<{ users: any[] }>('/api/admin/users');
        setUsersData(u.users);
      } else if (activeTab === 'academic') {
        const a = await apiRequest('/api/admin/academic');
        setAcademic(a);
      }
    } catch (err: any) {
      setError(err.message || 'Không thể tải dữ liệu quản trị.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleToggleActive = async (userId: number) => {
    try {
      const res = await apiRequest<{ is_active: boolean }>(`/api/admin/users/${userId}/toggle-active`, {
        method: 'PATCH',
      });
      onNotify('success', res.is_active ? 'Đã mở khóa tài khoản.' : 'Đã khóa tài khoản.');
      loadData();
    } catch (err: any) {
      onNotify('error', err.message || 'Không thể cập nhật trạng thái tài khoản.');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify({
          email: newEmail,
          full_name: newName,
          password: newPass,
          role: newRole,
        }),
      });
      onNotify('success', `Đã tạo tài khoản ${newEmail}.`);
      setNewEmail('');
      setNewName('');
      loadData();
    } catch (err: any) {
      onNotify('error', err.message || 'Lỗi tạo tài khoản.');
    }
  };

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/admin/departments', {
        method: 'POST',
        body: JSON.stringify({ code: deptCode, name: deptName }),
      });
      onNotify('success', 'Đã thêm khoa mới.');
      setDeptCode('');
      setDeptName('');
      loadData();
    } catch (err: any) {
      onNotify('error', err.message);
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/admin/courses', {
        method: 'POST',
        body: JSON.stringify({
          code: courseCode,
          title: courseTitle,
          department_id: academic?.departments?.[0]?.id || null,
          lecturer_id: academic?.lecturers?.[0]?.id || null,
        }),
      });
      onNotify('success', 'Đã thêm học phần mới.');
      setCourseCode('');
      setCourseTitle('');
      loadData();
    } catch (err: any) {
      onNotify('error', err.message);
    }
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  if (activeTab === 'overview' && dashboard) {
    const { stats, course_quality_stats, quality_notice } = dashboard;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Sinh viên" value={stats.total_students} icon={Users} accent="blue" />
          <StatCard title="Giảng viên" value={stats.total_lecturers} icon={GraduationCap} accent="emerald" />
          <StatCard title="Môn học / Bài giảng" value={`${stats.total_courses} / ${stats.total_lectures}`} icon={BookOpen} accent="indigo" />
          <StatCard title="Giờ video đã xử lý" value={`${stats.processed_video_hours} giờ`} subtitle={`${stats.total_lecture_views} lượt truy cập`} icon={Activity} accent="amber" />
        </div>

        <div className="rounded-xl border border-blue-200 bg-blue-50/70 px-4 py-3 text-xs text-blue-900">
          <strong>Minh bạch dữ liệu đào tạo:</strong> {quality_notice}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Tần suất truy cập theo học phần</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={course_quality_stats}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="code" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="total_views" name="Lượt xem" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Đánh giá sử dụng tài liệu số & Học phần cần quan tâm</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-2">Học phần</th>
                    <th className="py-2">Bài giảng</th>
                    <th className="py-2">Hoàn thành TB</th>
                    <th className="py-2">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {course_quality_stats.map((c: any) => (
                    <tr key={c.course_id}>
                      <td className="py-2.5 font-semibold text-slate-900">
                        {c.code} - {c.title}
                      </td>
                      <td className="py-2.5">{c.lecture_count}</td>
                      <td className="py-2.5 font-medium text-blue-700">{c.avg_completion_percent}%</td>
                      <td className="py-2.5">
                        {c.needs_attention ? (
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
                            Cần quan tâm
                          </span>
                        ) : (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                            Ổn định
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'users') {
    return (
      <div className="space-y-6">
        <form onSubmit={handleCreateUser} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <Plus className="h-4 w-4 text-blue-600" />
            Tạo tài khoản người dùng mới
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <input
              required
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="Email (@lectureai.edu.vn)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs"
            />
            <input
              required
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Họ và tên"
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs"
            />
            <input
              required
              type="password"
              value={newPass}
              onChange={(e) => setNewPass(e.target.value)}
              placeholder="Mật khẩu"
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs"
            />
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white"
            >
              <option value="student">Sinh viên</option>
              <option value="lecturer">Giảng viên</option>
              <option value="admin">Quản trị viên</option>
            </select>
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700"
            >
              Thêm tài khoản
            </button>
          </div>
        </form>

        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Họ và tên</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Vai trò</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {usersData.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-3 font-semibold text-slate-900">{u.full_name}</td>
                  <td className="px-4 py-3 text-slate-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-blue-50 px-2 py-0.5 font-semibold text-blue-700">
                      {u.role_display}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active ? (
                      <span className="text-emerald-700 font-semibold">Hoạt động</span>
                    ) : (
                      <span className="text-red-600 font-semibold">Đã khóa</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleToggleActive(u.id)}
                      className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 font-medium ${
                        u.is_active
                          ? 'border-amber-200 text-amber-700 hover:bg-amber-50'
                          : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                      }`}
                    >
                      {u.is_active ? <Lock className="h-3.5 w-3.5" /> : <Unlock className="h-3.5 w-3.5" />}
                      {u.is_active ? 'Khóa' : 'Mở khóa'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeTab === 'academic' && academic) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Quản lý Khoa</h3>
            <form onSubmit={handleCreateDept} className="flex gap-2">
              <input
                required
                value={deptCode}
                onChange={(e) => setDeptCode(e.target.value)}
                placeholder="Mã khoa"
                className="w-28 rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
              />
              <input
                required
                value={deptName}
                onChange={(e) => setDeptName(e.target.value)}
                placeholder="Tên khoa"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
              />
              <button type="submit" className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white">
                Thêm
              </button>
            </form>
            <div className="space-y-2">
              {academic.departments.map((d: any) => (
                <div key={d.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs">
                  <span className="font-bold text-blue-700">{d.code}</span> — <span className="font-semibold">{d.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Quản lý Môn học</h3>
            <form onSubmit={handleCreateCourse} className="flex gap-2">
              <input
                required
                value={courseCode}
                onChange={(e) => setCourseCode(e.target.value)}
                placeholder="Mã môn"
                className="w-28 rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
              />
              <input
                required
                value={courseTitle}
                onChange={(e) => setCourseTitle(e.target.value)}
                placeholder="Tên môn học"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
              />
              <button type="submit" className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white">
                Thêm
              </button>
            </form>
            <div className="space-y-2">
              {academic.courses.map((c: any) => (
                <div key={c.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs flex justify-between">
                  <div>
                    <span className="font-bold text-blue-700">{c.code}</span> — <span className="font-semibold">{c.title}</span>
                    <p className="text-[11px] text-slate-500">GV: {c.lecturer_name}</p>
                  </div>
                  <span className="text-[11px] text-slate-500">{c.lecture_count} bài</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'system' && dashboard) {
    const { ai_pipeline_status, recent_jobs, system_logs, stats } = dashboard;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard title="Trạng thái AI hiện tại" value={ai_pipeline_status.mode_info.label} icon={Cpu} accent="blue" />
          <StatCard title="Dung lượng lưu trữ" value={`${stats.storage_used_mb} MB`} icon={Database} accent="indigo" />
          <StatCard title="Tác vụ xử lý gần đây" value={recent_jobs.length} icon={Server} accent="emerald" />
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-3">Kiến trúc các Module AI & Trạng thái tích hợp</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {ai_pipeline_status.modules.map((m: any) => (
              <div key={m.id} className="rounded-lg border border-slate-200 p-3.5 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-900">{m.name}</span>
                  <AIModeBadge mode={m.status} />
                </div>
                <p className="text-[11px] text-slate-500">Công nghệ mục tiêu: {m.target_tech}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">Tiến trình xử lý AI (Processing Jobs)</h3>
            <div className="space-y-2.5">
              {recent_jobs.map((j: any) => (
                <div key={j.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">{j.lecture_title}</p>
                    <p className="text-[11px] text-slate-500">{j.current_step} ({j.progress_percent}%)</p>
                  </div>
                  <AIStatusBadge status={j.status} />
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-blue-600" />
              Nhật ký hệ thống (System Logs)
            </h3>
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {system_logs.map((lg: any) => (
                <div key={lg.id} className="rounded-lg border border-slate-100 bg-slate-50 p-2.5 text-[11px]">
                  <span className={`font-bold mr-2 ${lg.level === 'ERROR' ? 'text-red-600' : lg.level === 'WARNING' ? 'text-amber-600' : 'text-blue-600'}`}>
                    [{lg.level}]
                  </span>
                  <span className="font-mono text-slate-500 mr-2">[{lg.module}]</span>
                  <span className="text-slate-800">{lg.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
