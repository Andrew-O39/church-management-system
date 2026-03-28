"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { getAccessToken } from "lib/session";
import { logoutAndRedirect } from "lib/auth";
import { apiFetch } from "lib/api";
import type { UnreadCountResponse } from "lib/types";

function formatRole(role: string) {
  return role.split("_").join(" ");
}

function NavLink({
  href,
  children,
  active,
}: {
  href: string;
  children: React.ReactNode;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-slate-100 text-slate-900"
          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
      }`}
    >
      {children}
    </Link>
  );
}

export default function AppHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, status, isAdmin } = useAuth();

  const [hasSessionCookie, setHasSessionCookie] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number | null>(null);

  const refreshCookieHint = useCallback(() => {
    setHasSessionCookie(!!getAccessToken());
  }, []);

  const refreshUnread = useCallback(async () => {
    const t = getAccessToken();
    if (!t || status !== "authenticated") {
      setUnreadCount(null);
      return;
    }
    try {
      const res = await apiFetch<UnreadCountResponse>("/api/v1/notifications/me/unread-count", {
        method: "GET",
        token: t,
      });
      setUnreadCount(res.unread_count);
    } catch {
      setUnreadCount(null);
    }
  }, [status]);

  useEffect(() => {
    refreshCookieHint();
  }, [pathname, status, refreshCookieHint]);

  useEffect(() => {
    void refreshUnread();
  }, [pathname, status, refreshUnread]);

  useEffect(() => {
    const onUpdated = () => void refreshUnread();
    window.addEventListener("notifications:updated", onUpdated);
    return () => window.removeEventListener("notifications:updated", onUpdated);
  }, [refreshUnread]);

  const showAuthenticatedChrome =
    status === "authenticated" || (status === "loading" && hasSessionCookie);
  const showGreeting = status === "authenticated" && !!user;

  const onLogout = () => {
    logoutAndRedirect(router);
  };

  return (
    <header className="border-b border-slate-200/80 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 flex-col gap-0.5">
          <Link
            href="/"
            className="truncate text-base font-semibold tracking-tight text-slate-900 hover:text-slate-700"
          >
            Church Management System
          </Link>
          {showGreeting ? (
            <span className="truncate text-xs text-slate-500">
              Signed in as <span className="font-medium text-slate-700">{user.full_name}</span>
              <span className="text-slate-400"> · {formatRole(user.role)}</span>
            </span>
          ) : null}
        </div>

        <nav className="flex flex-wrap items-center gap-1 sm:justify-end">
          {!showAuthenticatedChrome ? (
            <>
              <NavLink href="/login" active={pathname === "/login"}>
                Sign in
              </NavLink>
              <NavLink href="/register" active={pathname === "/register"}>
                Create account
              </NavLink>
            </>
          ) : (
            <>
              <NavLink href="/profile" active={pathname === "/profile"}>
                Profile
              </NavLink>
              <NavLink
                href="/events"
                active={pathname === "/events" || pathname.startsWith("/events/")}
              >
                Events
              </NavLink>
              <NavLink
                href="/notifications"
                active={pathname === "/notifications" || pathname.startsWith("/notifications/")}
              >
                <span className="inline-flex items-center gap-1">
                  Notifications
                  {unreadCount !== null && unreadCount > 0 ? (
                    <span className="rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  ) : null}
                </span>
              </NavLink>
              {status === "authenticated" ? (
                <NavLink
                  href="/ministries"
                  active={pathname === "/ministries" || pathname.startsWith("/ministries/")}
                >
                  Ministries
                </NavLink>
              ) : null}
              {status === "authenticated" ? (
                <NavLink
                  href="/volunteers"
                  active={pathname === "/volunteers"}
                >
                  Volunteers
                </NavLink>
              ) : null}
              {status === "authenticated" && isAdmin ? (
                <>
                  <NavLink
                    href="/members"
                    active={
                      pathname === "/members" ||
                      pathname === "/members/new" ||
                      pathname.startsWith("/members/")
                    }
                  >
                    Parish registry
                  </NavLink>
                  <NavLink
                    href="/users"
                    active={pathname === "/users" || pathname.startsWith("/users/")}
                  >
                    App users
                  </NavLink>
                </>
              ) : null}
              <button
                type="button"
                onClick={onLogout}
                className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              >
                Log out
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
