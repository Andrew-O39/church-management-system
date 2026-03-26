"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { clearAccessToken, getAccessToken } from "lib/session";

export default function TopNav() {
  const router = useRouter();

  const [hasToken, setHasToken] = useState(() => {
    try {
      return !!getAccessToken();
    } catch {
      return false;
    }
  });

  const nav = useMemo(() => {
    const common = (
      <>
        <Link href="/members" className="hover:text-slate-900">
          Members
        </Link>
        <Link href="/profile" className="hover:text-slate-900">
          Profile
        </Link>
      </>
    );

    if (hasToken) return common;
    return (
      <>
        <Link href="/login" className="hover:text-slate-900">
          Login
        </Link>
      </>
    );
  }, [hasToken]);

  async function onLogout() {
    clearAccessToken();
    setHasToken(false);
    router.push("/login");
  }

  return (
    <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 p-4">
      <div className="flex items-center gap-3">
        <Link href="/" className="font-semibold text-slate-900">
          Church CMS
        </Link>
      </div>

      <nav className="flex items-center gap-4 text-sm text-slate-700">
        {nav}
        {hasToken ? (
          <button
            type="button"
            onClick={onLogout}
            className="rounded-md border border-slate-200 bg-white px-3 py-1 text-slate-800 hover:bg-slate-50"
          >
            Logout
          </button>
        ) : null}
      </nav>
    </div>
  );
}

