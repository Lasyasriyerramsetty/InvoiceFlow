// Centralized API base URL.
// Uses NEXT_PUBLIC_API_URL when set (e.g. in production / Docker),
// otherwise falls back to the local backend during development.
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export const apiUrl = (path: string): string =>
  `${API_BASE_URL}/api/v1${path.startsWith("/") ? path : `/${path}`}`;