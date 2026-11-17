import React from 'react';
import { AlertCircle, CheckCircle2, Cpu, Info, Loader2, Sparkles, X } from 'lucide-react';

export function AIModeBadge({ mode }: { mode: string }) {
  if (mode === 'local_model') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-200">
        <Cpu className="h-3 w-3" />
        AI Nội bộ
      </span>
    );
  }
  if (mode === 'external_api') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 border border-blue-200">
        <Sparkles className="h-3 w-3" />
        API AI Ngoài
      </span>
    );
  }
  return (
    <span
      title="Đang sử dụng dữ liệu mẫu / mô phỏng có cấu trúc (chưa gắn model weights hoặc API key thực tế)"
      className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 border border-amber-200"
    >
      <Info className="h-3 w-3" />
      AI Mô phỏng
    </span>
  );
}

export function AIStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    completed: { label: 'Đã xử lý AI', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    processing: { label: 'Đang xử lý...', cls: 'bg-blue-50 text-blue-700 border-blue-200' },
    pending: { label: 'Chờ xử lý', cls: 'bg-slate-100 text-slate-600 border-slate-200' },
    failed: { label: 'Lỗi xử lý', cls: 'bg-red-50 text-red-700 border-red-200' },
  };
  const cfg = map[status] || map.pending;
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

export function LoadingState({ message = 'Đang tải dữ liệu...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-3" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
      <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
      <p className="text-sm font-medium text-red-800">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-lg bg-red-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-red-700"
        >
          Thử lại
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <p className="text-base font-semibold text-slate-700">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
    </div>
  );
}

export interface ToastMessage {
  id: number;
  type: 'success' | 'error' | 'info';
  text: string;
}

export function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: ToastMessage[];
  onDismiss: (id: number) => void;
}) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => {
        const colors =
          t.type === 'success'
            ? 'bg-emerald-600 text-white'
            : t.type === 'error'
            ? 'bg-red-600 text-white'
            : 'bg-blue-600 text-white';
        return (
          <div
            key={t.id}
            className={`flex items-center justify-between gap-3 rounded-xl px-4 py-3 text-sm font-medium shadow-lg ${colors}`}
          >
            <div className="flex items-center gap-2">
              {t.type === 'success' ? (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              ) : (
                <AlertCircle className="h-4 w-4 shrink-0" />
              )}
              <span>{t.text}</span>
            </div>
            <button onClick={() => onDismiss(t.id)} className="opacity-80 hover:opacity-100">
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = 'blue',
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  accent?: 'blue' | 'emerald' | 'indigo' | 'amber';
}) {
  const accentMap = {
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    amber: 'bg-amber-50 text-amber-600',
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{title}</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
        </div>
        <div className={`rounded-lg p-2.5 ${accentMap[accent]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
