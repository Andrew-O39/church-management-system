"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "components/providers/AuthProvider";
import { loginAndFetchMe, resolvePostAuthPath } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { btnPrimaryBlock, fieldInput, surfaceError, surfaceInfo } from "lib/ui";

const REASON_MESSAGES: Record<string, string> = {
  signed_out: "You have been signed out.",
  session_expired: "Your session expired. Please sign in again.",
  account_inactive: "This account is inactive. Contact an administrator for help.",
};

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { user, status } = useAuth();

  const fromPath = params.get("from") ?? "";
  const reason = params.get("reason") ?? "";
  const reasonMessage = reason ? REASON_MESSAGES[reason] ?? null : null;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status !== "authenticated" || !user) return;
    router.replace(resolvePostAuthPath(fromPath || undefined, user));
  }, [status, user, fromPath, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { me } = await loginAndFetchMe({ email, password });
      router.replace(resolvePostAuthPath(fromPath || undefined, me));
    } catch (err) {
      if (isUnauthorized(err)) {
        setError("Incorrect email or password.");
      } else if (isInactiveAccountError(err)) {
        setError(REASON_MESSAGES.account_inactive);
      } else {
        setError(toErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }

  const submitDisabled = useMemo(
    () => loading || !email.trim() || !password,
    [email, loading, password],
  );

  return (
    <PageShell
      title="Sign in"
      description="Use the email and password for your church account."
    >
      <ContentCard>
        {status === "loading" ? (
          <p className="text-sm text-slate-600">Checking your session…</p>
        ) : (
          <div className="space-y-4">
            {reasonMessage ? (
              <div className={surfaceInfo}>{reasonMessage}</div>
            ) : null}

            {error ? (
              <div className={surfaceError}>{error}</div>
            ) : null}

            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="login-email" className="text-sm font-medium text-slate-800">
                  Email
                </label>
                <input
                  id="login-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  className={fieldInput + " mt-1"}
                  autoComplete="username"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="login-password" className="text-sm font-medium text-slate-800">
                  Password
                </label>
                <input
                  id="login-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                  className={fieldInput + " mt-1"}
                  autoComplete="current-password"
                />
              </div>

              <button type="submit" disabled={submitDisabled} className={btnPrimaryBlock}>
                {loading ? "Signing in…" : "Sign in"}
              </button>
            </form>

            <p className="text-center text-sm text-slate-600">
              New here?{" "}
              <Link href="/register" className="font-medium text-indigo-800 underline underline-offset-2 hover:text-indigo-950">
                Create an account
              </Link>
            </p>
          </div>
        )}
      </ContentCard>
    </PageShell>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <PageShell title="Sign in" description="Loading…">
          <ContentCard>
            <p className="text-sm text-slate-600">Loading…</p>
          </ContentCard>
        </PageShell>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
