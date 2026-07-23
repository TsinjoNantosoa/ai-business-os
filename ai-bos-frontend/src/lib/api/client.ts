// ============================================================
// AI BOS — API Client
// fetch wrapper with auth headers, 401 refresh, correlation ID
// ============================================================

const API_URL = import.meta.env.VITE_API_URL || '';
const USE_MOCKS = !API_URL || import.meta.env.VITE_USE_MOCKS === 'true';

export { USE_MOCKS, API_URL };

export class MockModeError extends Error {
  constructor(public path: string) {
    super(`Mock mode active — no real API call made for ${path}`);
    this.name = 'MockModeError';
  }
}

export class ApiError extends Error {
  constructor(public status: number, public statusText: string, public body?: unknown) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

// Lazy import to avoid circular dependency
async function getAuthState() {
  const { useAuth } = await import('@/lib/auth/store');
  return useAuth.getState();
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  if (USE_MOCKS) throw new MockModeError(path);

  const auth = await getAuthState();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: auth.token ? `Bearer ${auth.token}` : '',
      'X-Correlation-ID': crypto.randomUUID(),
      'X-Tenant-Id': auth.orgId || '',
      ...options?.headers,
    },
  });

  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch<T>(path, options);
    throw new ApiError(401, 'Unauthorized');
  }

  if (!res.ok) throw new ApiError(res.status, res.statusText, await res.json().catch(() => undefined));
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

/** Decode JWT payload without verifying signature (client-side expiry check only). */
export function readJwtExp(token: string | null | undefined): number | null {
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const json = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
    const payload = JSON.parse(json) as { exp?: number };
    return typeof payload.exp === 'number' ? payload.exp : null;
  } catch {
    return null;
  }
}

/** Refresh access token if missing/expired/near expiry (default 90s skew). */
export async function ensureFreshAccessToken(skewSeconds = 90): Promise<boolean> {
  const auth = await getAuthState();
  if (!auth.token && !auth.refreshToken) return false;
  const exp = readJwtExp(auth.token);
  const now = Math.floor(Date.now() / 1000);
  if (auth.token && exp !== null && exp > now + skewSeconds) return true;
  return tryRefresh();
}

let refreshPromise: Promise<boolean> | null = null;

/** Refresh access token once; shared by apiFetch and streaming clients (Copilot SSE). */
export async function tryRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const auth = await getAuthState();
      if (!auth.refreshToken) return false;
      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: auth.refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (!data?.token || !data?.refreshToken) return false;
      auth.setTokens(data.token, data.refreshToken);
      return true;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}
