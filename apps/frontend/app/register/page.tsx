"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ApiError } from "lib/api";
import { useAuth } from "components/providers/AuthProvider";
import { registerAndSignIn, resolvePostAuthPath } from "lib/auth";
import { toErrorMessage } from "lib/errors";
import PageShell, { ContentCard } from "components/layout/PageShell";

export default function RegisterPage() {
  const router = useRouter();
  const { user, status } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status !== "authenticated" || !user) return;
    router.replace(resolvePostAuthPath(undefined, user));
  }, [status, user, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});

    const name = fullName.trim();
    const em = email.trim();
    const pw = password;
    const local: Record<string, string> = {};
    if (!name) local.full_name = "Enter your full name.";
    if (!em) local.email = "Enter your email.";
    if (!pw) local.password = "Enter a password.";
    else if (pw.length < 8) local.password = "Use at least 8 characters.";
    else if (pw.length > 128) local.password = "Password is too long.";

    if (Object.keys(local).length) {
      setFieldErrors(local);
      return;
    }

    setLoading(true);
    try {
      const registration = await registerAndSignIn({
        full_name: name,
        email: em,
        password: pw,
      });
      router.replace(resolvePostAuthPath(undefined, registration.user));
    } catch (err) {
      if (typeof err === "object" && err && "status" in err) {
        const k = err as ApiError;
        if (k.status === 409) {
          setError("An account with this email already exists. Try signing in instead.");
          return;
        }
      }
      setError(toErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const submitDisabled = useMemo(
    () => loading || !fullName.trim() || !email.trim() || !password,
    [email, fullName, loading, password],
  );

  return (
    <PageShell
      title="Create account"
      description="Register to access your member profile. An administrator can grant additional access when needed."
    >
      <ContentCard>
        {status === "loading" ? (
          <p className="text-sm text-slate-600">Checking your session…</p>
        ) : (
          <div className="space-y-4">
            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                {error}
              </div>
            ) : null}

            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="reg-name" className="text-sm font-medium text-slate-800">
                  Full name
                </label>
                <input
                  id="reg-name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
                  autoComplete="name"
                />
                {fieldErrors.full_name ? (
                  <p className="text-xs text-red-600">{fieldErrors.full_name}</p>
                ) : null}
              </div>

              <div className="space-y-1.5">
                <label htmlFor="reg-email" className="text-sm font-medium text-slate-800">
                  Email
                </label>
                <input
                  id="reg-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
                  autoComplete="email"
                />
                {fieldErrors.email ? (
                  <p className="text-xs text-red-600">{fieldErrors.email}</p>
                ) : null}
              </div>

              <div className="space-y-1.5">
                <label htmlFor="reg-password" className="text-sm font-medium text-slate-800">
                  Password
                </label>
                <input
                  id="reg-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
                  autoComplete="new-password"
                />
                {fieldErrors.password ? (
                  <p className="text-xs text-red-600">{fieldErrors.password}</p>
                ) : (
                  <p className="text-xs text-slate-500">At least 8 characters.</p>
                )}
              </div>

              <button
                type="submit"
                disabled={submitDisabled}
                className="w-full rounded-lg bg-slate-900 px-3 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-60"
              >
                {loading ? "Creating account…" : "Create account"}
              </button>
            </form>

            <p className="text-center text-sm text-slate-600">
              Already registered?{" "}
              <Link href="/login" className="font-medium text-slate-900 underline underline-offset-2">
                Sign in
              </Link>
            </p>
          </div>
        )}
      </ContentCard>
    </PageShell>
  );
}
