"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { apiFetch, type ApiError } from "lib/api";
import { getAccessToken } from "lib/session";
import { loginAndFetchMe } from "lib/auth";
import type { FormEvent } from "react";
import type { MeResponse } from "lib/types";

function toErrorMessage(err: unknown) {
  if (typeof err === "object" && err && "status" in err) {
    const e = err as ApiError;
    if (e.detail) return e.detail;
    return `Request failed (${e.status})`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();

  const fromPath = params.get("from") ?? "";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkingExistingSession, setCheckingExistingSession] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setCheckingExistingSession(false);
      return;
    }

    apiFetch<MeResponse>("/api/v1/auth/me", { method: "GET", token })
      .then((me) => {
        const target =
          fromPath && (fromPath.startsWith("/profile") || fromPath.startsWith("/members"))
            ? fromPath
            : me.role === "admin"
              ? "/members"
              : "/profile";
        router.replace(target);
      })
      .catch(() => {
        setCheckingExistingSession(false);
      });
  }, [fromPath, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { me } = await loginAndFetchMe({ email, password });
      const target =
        fromPath && (fromPath.startsWith("/profile") || fromPath.startsWith("/members"))
          ? fromPath
          : me.role === "admin"
            ? "/members"
            : "/profile";
      router.replace(target);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const submitDisabled = useMemo(
    () => loading || !email.trim() || !password,
    [email, loading, password],
  );

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Login</h1>

      {checkingExistingSession ? (
        <p className="text-sm text-slate-600">Checking session...</p>
      ) : (
        <>
          {error ? (
            <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          ) : null}

          <form onSubmit={onSubmit} className="space-y-3">
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-800">Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                autoComplete="username"
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-800">Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={submitDisabled}
              className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="text-xs text-slate-500">
            Uses access tokens only (no refresh tokens yet). Logging in again may be
            required when the token expires.
          </p>
        </>
      )}
    </div>
  );
}

