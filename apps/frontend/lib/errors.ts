import type { ApiError } from "./api";

/** Must match backend `app.modules.auth.constants.INACTIVE_USER_DETAIL`. */
export const INACTIVE_USER_HTTP_DETAIL = "Inactive user";

export function getApiErrorDetail(err: unknown): string | undefined {
  if (typeof err === "object" && err !== null && "detail" in err) {
    const d = (err as ApiError).detail;
    if (typeof d === "string") return d;
  }
  return undefined;
}

export function toErrorMessage(err: unknown): string {
  if (typeof err === "object" && err && "status" in err) {
    const e = err as ApiError;
    const detail = getApiErrorDetail(err);
    if (detail) return detail;
    return `Request failed (${e.status})`;
  }
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function isUnauthorized(err: unknown): boolean {
  return typeof err === "object" && err !== null && "status" in err && (err as ApiError).status === 401;
}

export function isForbidden(err: unknown): boolean {
  return typeof err === "object" && err !== null && "status" in err && (err as ApiError).status === 403;
}

export function isInactiveAccountError(err: unknown): boolean {
  return isForbidden(err) && getApiErrorDetail(err) === INACTIVE_USER_HTTP_DETAIL;
}

export function isConflictError(err: unknown): boolean {
  return typeof err === "object" && err !== null && "status" in err && (err as ApiError).status === 409;
}
