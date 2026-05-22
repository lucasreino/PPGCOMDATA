const TOKEN_KEY = "ppgcomdata_token";

export const SESSION_EXPIRED_MESSAGE =
  "Sua sessão expirou ou é inválida. Faça login novamente.";

let onUnauthorized: (() => void) | null = null;

/** Registra callback (ex.: logout) quando a API retorna 401. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

export function parseApiErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg?: string }).msg) : ""))
      .filter(Boolean)
      .join("; ");
  }
  return fallback;
}

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    return process.env.NEXT_PUBLIC_API_URL || `http://${host}:8000/api/v1`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  requireAuth = true
): Promise<Response> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const url = path.startsWith("http") ? path : `${base}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers || {});
  if (requireAuth) {
    const token = getStoredToken();
    if (!token) {
      throw new Error(SESSION_EXPIRED_MESSAGE);
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });

  if (requireAuth && response.status === 401) {
    setStoredToken(null);
    onUnauthorized?.();
    throw new Error(SESSION_EXPIRED_MESSAGE);
  }

  return response;
}

export async function login(email: string, password: string): Promise<string> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await fetch(`${base}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Falha no login.");
  }

  const data = await res.json();
  setStoredToken(data.access_token);
  return data.access_token;
}

export async function fetchCurrentUser() {
  const res = await apiFetch("/auth/me");
  if (!res.ok) throw new Error("Sessão inválida.");
  return res.json();
}
