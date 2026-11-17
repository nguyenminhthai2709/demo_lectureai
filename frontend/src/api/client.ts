const API_BASE = import.meta.env.VITE_API_URL || '';

export function getAuthToken(): string | null {
  return localStorage.getItem('lectureai_token');
}

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem('lectureai_token', token);
  } else {
    localStorage.removeItem('lectureai_token');
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMsg = `Lỗi HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) {
        errMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // ignore parse error
    }
    throw new Error(errMsg);
  }

  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return res.json() as Promise<T>;
  }
  return res.text() as unknown as Promise<T>;
}

export function formatTime(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
