export type ApiResult<T = any> = {
  ok: boolean;
  status: number;
  data?: T;
  error?: string;
};

export async function apiFetch<T = any>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  try {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      ...(init.headers || {}),
    } as HeadersInit;
    if (token) {
      (headers as any)['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(path, { ...init, headers });
    if (res.status === 204) {
      return { ok: true, status: res.status };
    }
    const contentType = res.headers.get('content-type') || '';
    let body: any = undefined;
    if (contentType.includes('application/json')) {
      body = await res.json();
    } else {
      const text = await res.text();
      try { body = text ? JSON.parse(text) : undefined; } catch { body = text; }
    }
    if (!res.ok) {
      return { ok: false, status: res.status, error: (body && (body.detail || body.error)) || `HTTP ${res.status}` };
    }
    return { ok: true, status: res.status, data: body as T };
  } catch (e: any) {
    return { ok: false, status: 0, error: e?.message || 'Network error' };
  }
}


