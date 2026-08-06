// Declare process for environments where @types/node isn't available to avoid
// "Cannot find name 'process'" TypeScript errors in browser builds.
declare const process: any;
const API_URL = process?.env?.NEXT_PUBLIC_API_URL || "";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const res = await fetch(`${API_URL}/api${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// Absolute URL for an API path (e.g. for <a href> download links).
export function apiUrl(path: string): string {
  return `${API_URL}/api${path}`;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }), // Added this line
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};