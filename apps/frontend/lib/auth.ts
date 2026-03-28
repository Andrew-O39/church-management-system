import { apiFetch } from "./api";
import { dispatchAuthUpdate } from "./auth-events";
import { clearAccessToken, setAccessToken } from "./session";
import type { JwtTokenResponse, MeResponse, RegisterResponse } from "./types";

/** Where to send the user after login/register when they did not deep-link to a path. */
export function resolvePostAuthPath(
  fromPath: string | null | undefined,
  user: MeResponse,
): string {
  if (fromPath?.startsWith("/profile")) return fromPath;
  if (fromPath?.startsWith("/events")) return fromPath;
  if (fromPath?.startsWith("/ministries")) return fromPath;
  if (fromPath?.startsWith("/volunteers")) return fromPath;
  if (fromPath?.startsWith("/members")) {
    return user.role === "admin" ? fromPath : "/profile?notice=admin_only";
  }
  return user.role === "admin" ? "/members" : "/profile";
}

export async function loginAndFetchMe(params: {
  email: string;
  password: string;
}): Promise<{ token: string; me: MeResponse }> {
  const tokenRes = await apiFetch<JwtTokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: params,
    token: null,
  });
  setAccessToken(tokenRes.access_token);
  const me = await apiFetch<MeResponse>("/api/v1/auth/me", {
    method: "GET",
    token: tokenRes.access_token,
  });
  dispatchAuthUpdate({ user: me });
  return { token: tokenRes.access_token, me };
}

/**
 * Register against `POST /api/v1/auth/register`, which returns `RegisterResponse`:
 * `{ access_token, token_type: "bearer", user }` (201). Stores the token and notifies
 * auth context with `user` so the client does not need a follow-up /auth/me for the same data.
 */
export async function registerAndSignIn(params: {
  full_name: string;
  email: string;
  password: string;
}): Promise<RegisterResponse> {
  const res = await apiFetch<RegisterResponse>("/api/v1/auth/register", {
    method: "POST",
    body: params,
    token: null,
  });
  setAccessToken(res.access_token);
  dispatchAuthUpdate({ user: res.user });
  return res;
}

export function logout() {
  clearAccessToken();
  dispatchAuthUpdate({ user: null });
}

type RouterReplace = { replace: (href: string) => void };

export type LoginRedirectReason =
  | "signed_out"
  | "session_expired"
  | "account_inactive";

export function clearSessionAndRedirect(
  router: RouterReplace,
  reason: LoginRedirectReason = "session_expired",
) {
  clearAccessToken();
  dispatchAuthUpdate({ user: null });
  router.replace(`/login?reason=${reason}`);
}

export function logoutAndRedirect(router: RouterReplace) {
  clearSessionAndRedirect(router, "signed_out");
}

