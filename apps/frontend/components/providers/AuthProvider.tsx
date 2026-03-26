"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch } from "lib/api";
import { CMS_AUTH_EVENT, type CmsAuthDetail } from "lib/auth-events";
import { clearAccessToken, getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized } from "lib/errors";
import type { MeResponse } from "lib/types";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  user: MeResponse | null;
  status: AuthStatus;
  isAdmin: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function isPublicAuthPath(pathname: string) {
  return pathname === "/login" || pathname === "/register";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const pathnameRef = useRef(pathname);
  pathnameRef.current = pathname;

  const [user, setUser] = useState<MeResponse | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const loadMe = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setStatus("unauthenticated");
      return;
    }
    setStatus("loading");
    try {
      const u = await apiFetch<MeResponse>("/api/v1/auth/me", { method: "GET", token });
      setUser(u);
      setStatus("authenticated");
    } catch (err) {
      setUser(null);
      const p = pathnameRef.current;

      if (isUnauthorized(err)) {
        clearAccessToken();
        setStatus("unauthenticated");
        if (!isPublicAuthPath(p)) {
          router.replace("/login?reason=session_expired");
        }
        return;
      }

      if (isInactiveAccountError(err)) {
        clearAccessToken();
        setStatus("unauthenticated");
        if (!isPublicAuthPath(p)) {
          router.replace("/login?reason=account_inactive");
        }
        return;
      }

      setStatus("unauthenticated");
    }
  }, [router]);

  useEffect(() => {
    void loadMe();
  }, [loadMe]);

  useEffect(() => {
    const onAuth = (e: Event) => {
      const detail = (e as CustomEvent<CmsAuthDetail>).detail ?? {};
      if (Object.prototype.hasOwnProperty.call(detail, "user")) {
        const next = detail.user ?? null;
        setUser(next);
        setStatus(next ? "authenticated" : "unauthenticated");
        return;
      }
      void loadMe();
    };
    window.addEventListener(CMS_AUTH_EVENT, onAuth as EventListener);
    return () => window.removeEventListener(CMS_AUTH_EVENT, onAuth as EventListener);
  }, [loadMe]);

  const value: AuthContextValue = {
    user,
    status,
    isAdmin: user?.role === "admin",
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
