import type { MeResponse } from "./types";

/** Dispatched when the session cookie and/or known user changes (login, register, logout, manual refresh). */
export const CMS_AUTH_EVENT = "cms:auth";

export type CmsAuthDetail = {
  /**
   * When set (including `null`), updates context without calling /auth/me.
   * Omitted = re-sync from cookie via GET /auth/me.
   */
  user?: MeResponse | null;
};

export function dispatchAuthUpdate(detail: CmsAuthDetail = {}) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(CMS_AUTH_EVENT, { detail }));
}
