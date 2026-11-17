import React, { useEffect, useState } from 'react';
import { apiRequest, getAuthToken, setAuthToken } from './api/client';
import { AdminDashboard } from './components/AdminDashboard';
import { AppLayout } from './components/Layout';
import { LectureDetailView } from './components/LectureDetailView';
import { LecturerDashboard } from './components/LecturerDashboard';
import { LoginPage } from './components/LoginPage';
import { StudentDashboard } from './components/StudentDashboard';
import { LoadingState, ToastContainer, ToastMessage } from './components/UIPrimitives';
import { User } from './types';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [openLectureId, setOpenLectureId] = useState<number | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const notify = (type: ToastMessage['type'], text: string) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, type, text }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setInitializing(false);
      return;
    }
    apiRequest<User>('/api/auth/me')
      .then((u) => setUser(u))
      .catch(() => setAuthToken(null))
      .finally(() => setInitializing(false));
  }, []);

  const handleLoginSuccess = (u: User) => {
    setUser(u);
    setActiveTab('overview');
    setOpenLectureId(null);
    notify('success', `Chào mừng ${u.full_name} (${u.role_display})`);
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    setOpenLectureId(null);
    notify('info', 'Bạn đã đăng xuất.');
  };

  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingState message="Đang khởi tạo LectureAI..." />
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <LoginPage onLoginSuccess={handleLoginSuccess} />
        <ToastContainer toasts={toasts} onDismiss={(id) => setToasts((p) => p.filter((t) => t.id !== id))} />
      </>
    );
  }

  return (
    <>
      <AppLayout
        user={user}
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
          setOpenLectureId(null);
        }}
        onLogout={handleLogout}
      >
        {openLectureId !== null ? (
          <LectureDetailView
            lectureId={openLectureId}
            userRole={user.role}
            onBack={() => setOpenLectureId(null)}
            onNotify={notify}
          />
        ) : user.role === 'student' ? (
          <StudentDashboard
            activeTab={activeTab}
            onOpenLecture={(id) => setOpenLectureId(id)}
            onNotify={notify}
          />
        ) : user.role === 'lecturer' ? (
          <LecturerDashboard
            activeTab={activeTab}
            onOpenLecture={(id) => setOpenLectureId(id)}
            onNotify={notify}
          />
        ) : (
          <AdminDashboard activeTab={activeTab} onNotify={notify} />
        )}
      </AppLayout>
      <ToastContainer toasts={toasts} onDismiss={(id) => setToasts((p) => p.filter((t) => t.id !== id))} />
    </>
  );
}
