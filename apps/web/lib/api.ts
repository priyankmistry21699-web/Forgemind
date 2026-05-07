/**
 * ForgeMind API client — thin fetch wrapper for backend requests.
 *
 * Reads API_BASE_URL from the environment (set at build-time via
 * NEXT_PUBLIC_API_URL). Falls back to http://localhost:8000 for local dev.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

/**
 * VULN-12 fix: store the auth token in a module-level variable (memory only)
 * instead of localStorage. localStorage is readable by any JavaScript running
 * on the page, making tokens trivially exfiltrable via XSS. An in-memory store
 * is cleared on page refresh, which is acceptable for short-lived JWTs (1h).
 *
 * For production deployments the preferred approach is httpOnly Secure cookies
 * set by the API server — the server-side auth route should do that and this
 * client should send credentials: "include" instead.
 */
let _memoryToken: string | null = null;

export function setAuthToken(token: string | null): void {
  _memoryToken = token;
}

export function getAuthToken(): string | null {
  return _memoryToken;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const authHeaders: Record<string, string> = {};
  if (_memoryToken) {
    authHeaders["Authorization"] = `Bearer ${_memoryToken}`;
  }

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    throw new ApiError(res.status, res.statusText, body);
  }

  return res.json() as Promise<T>;
}
