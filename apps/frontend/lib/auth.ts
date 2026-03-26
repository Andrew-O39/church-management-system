import { apiFetch } from "./api";
import { clearAccessToken, setAccessToken } from "./session";
import type { JwtTokenResponse, MeResponse } from "./types";

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
  return { token: tokenRes.access_token, me };
}

export function logout() {
  clearAccessToken();
}

