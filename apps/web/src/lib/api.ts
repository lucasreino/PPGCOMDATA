const TOKEN_KEY = "ppgcomdata_token";

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
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return fetch(url, { ...options, headers });
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
