// Unified API Client — GeniAI backend
// Base URL driven by EXPO_PUBLIC_API_URL environment variable

const API_BASE =
  process.env.EXPO_PUBLIC_API_URL ??
  (__DEV__ ? 'http://localhost:8000' : 'https://geniai.sianlk.com');

export { API_BASE };

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-App-Slug': 'geniai',
    ...((options.headers as Record<string, string>) ?? {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `API ${res.status}`);
  }
  return res.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await apiFetch(path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `API ${res.status}`);
  }
  return res.json();
}

// Auth helpers — endpoints match /api/v1/auth/* and /api/v1/users/*
export const auth = {
  register: (email: string, password: string, username = '', fullName = '') =>
    apiPost<{ id: string; email: string; username: string }>('/api/v1/auth/register', {
      email,
      password,
      username,
      full_name: fullName,
    }),
  login: (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    return apiFetch('/api/v1/auth/login', {
      method: 'POST',
      body: form.toString(),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then((r) => r.json() as Promise<{ access_token: string; refresh_token: string }>);
  },
  me: () =>
    apiGet<{
      id: string;
      email: string;
      username: string;
      full_name: string;
      role: string;
      subscription_tier: string;
    }>('/api/v1/users/me'),
  logout: (refreshToken: string) =>
    apiPost<{ message: string }>('/api/v1/auth/logout', { refresh_token: refreshToken }),
};

// AI helpers
export const aiApi = {
  complete: (message: string, context?: Array<{ role: string; content: string }>) =>
    apiPost<{ content: string; model: string; duration_ms: number }>('/api/ai/complete', {
      message,
      app_slug: 'geniai',
      context,
    }),
  agent: (task: string, agentType = 'analyst') =>
    apiPost<{ result: string; agent_type: string }>('/api/ai/agent', {
      task,
      app_slug: 'geniai',
      agent_type: agentType,
    }),
};

// Analytics
export const analyticsApi = {
  batch: (events: Array<{ event_name: string; properties?: Record<string, unknown> }>) =>
    apiFetch('/api/analytics/batch', {
      method: 'POST',
      body: JSON.stringify({ events: events.map((e) => ({ ...e, app_slug: 'geniai' })) }),
    }).then((r) => r.json()),
};
