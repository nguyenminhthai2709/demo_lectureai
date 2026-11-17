import React, { useState } from 'react';
import {
  BookOpen,
  ClipboardCheck,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  Upload,
  Users,
  X,
} from 'lucide-react';
import { User } from '../types';

export interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
}

export function getNavItemsForRole(role: User['role']): NavItem[] {
  if (role === 'student') {
    return [
      { id: 'overview', label: 'Tổng quan học tập', icon: LayoutDashboard },
      { id: 'lectures', label: 'Kho bài giảng', icon: BookOpen },
      { id: 'quizzes', label: 'Ôn tập & Kiểm tra', icon: ClipboardCheck },
    ];
  }
  if (role === 'lecturer') {
    return [
      { id: 'overview', label: 'Tổng quan giảng dạy', icon: LayoutDashboard },
      { id: 'manage', label: 'Quản lý & Tải bài giảng', icon: Upload },
      { id: 'analytics', label: 'Phân tích & Cử chỉ', icon: GraduationCap },
    ];
  }
  return [
    { id: 'overview', label: 'Thống kê hệ thống', icon: LayoutDashboard },
    { id: 'users', label: 'Quản lý người dùng', icon: Users },
    { id: 'academic', label: 'Quản lý đào tạo', icon: BookOpen },
    { id: 'system', label: 'Giám sát AI & Hệ thống', icon: Settings },
  ];
}

export function AppLayout({
  user,
  activeTab,
  onSelectTab,
  onLogout,
  children,
}: {
  user: User;
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onLogout: () => void;
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navItems = getNavItemsForRole(user.role);

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white border-r border-slate-200">
      <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-100">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
          <GraduationCap className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-slate-900">LectureAI</h1>
          <p className="text-[11px] font-medium text-blue-600">Learn Smarter. Teach Better.</p>
        </div>
      </div>

      <div className="px-4 py-3">
        <div className="rounded-lg bg-blue-50/80 px-3 py-2 border border-blue-100">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-800">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>{user.role_display}</span>
          </div>
          <p className="mt-0.5 truncate text-xs text-slate-700 font-medium">{user.full_name}</p>
          <p className="truncate text-[11px] text-slate-500">{user.email}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                onSelectTab(item.id);
                setMobileOpen(false);
              }}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="border-t border-slate-100 p-3">
        <button
          onClick={onLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          <span>Đăng xuất</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 sticky top-0 h-screen">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div className="fixed inset-0 bg-slate-900/40" onClick={() => setMobileOpen(false)} />
          <div className="relative z-50 w-64 max-w-[80vw] h-full">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 rounded-lg p-1 text-slate-500 hover:bg-slate-100"
            >
              <X className="h-5 w-5" />
            </button>
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/95 backdrop-blur px-4 py-3 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Mở menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div>
              <p className="text-xs font-medium text-slate-500">Nền tảng Trí tuệ Bài giảng Đa phương thức</p>
              <h2 className="text-base font-semibold text-slate-900">
                {navItems.find((n) => n.id === activeTab)?.label || 'Chi tiết bài giảng'}
              </h2>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Hệ thống sẵn sàng</span>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
