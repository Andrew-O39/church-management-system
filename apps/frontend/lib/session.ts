"use client";

export const TOKEN_COOKIE = "access_token";

function isClient() {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

export function getAccessToken(): string | null {
  if (!isClient()) return null;
  const raw = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${TOKEN_COOKIE}=`));
  if (!raw) return null;
  const value = raw.substring(TOKEN_COOKIE.length + 1);
  return value ? decodeURIComponent(value) : null;
}

export function setAccessToken(token: string) {
  if (!isClient()) return;
  const secure = process.env.NODE_ENV === "production";
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(
    token,
  )}; path=/; SameSite=Lax;${secure ? " Secure;" : ""}`;
}

export function clearAccessToken() {
  if (!isClient()) return;
  document.cookie = `${TOKEN_COOKIE}=; path=/; SameSite=Lax; Max-Age=0;`;
}

