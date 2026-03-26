import { getAccessToken } from "./session";

export type ApiError = {
  status: number;
  detail?: string;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function buildUrl(path: string) {
  if (!path.startsWith("/")) return `${apiBaseUrl}/${path}`;
  return `${apiBaseUrl}${path}`;
}

export async function apiFetch<T>(
  path: string,
  init?: {
    method?: string;
    body?: unknown;
    token?: string | null;
    signal?: AbortSignal;
  },
): Promise<T> {
  // If the caller passes `token: null`, treat it as an explicit "no Authorization header".
  const token =
    init && "token" in init ? init.token : getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildUrl(path), {
    method: init?.method ?? "GET",
    headers,
    body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
    signal: init?.signal,
    cache: "no-store",
  });

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const json = (await res.json()) as { detail?: string; message?: string };
      detail = json.detail ?? json.message;
    } catch {
      detail = await res.text().catch(() => undefined);
    }
    const err: ApiError = { status: res.status, detail };
    throw err;
  }

  return (await res.json()) as T;
}

