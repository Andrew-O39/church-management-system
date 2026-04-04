/**
 * Shared UI class strings for consistent buttons, fields, and chips across the app.
 */

export const fieldInput =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-base font-medium text-slate-900 shadow-sm placeholder:font-normal placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/25";

/** Multi-line fields — same treatment as `fieldInput`. */
export const fieldTextarea = `${fieldInput} min-h-24 resize-y`;

export const fieldLabel = "text-sm font-semibold text-slate-900";

export const btnPrimary =
  "inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50";

export const btnPrimaryBlock =
  "inline-flex w-full items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50";

export const btnPrimarySm =
  "inline-flex items-center justify-center rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50";

export const btnSecondary =
  "inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-sm shadow-slate-900/[0.04] transition-colors hover:border-slate-400 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50";

export const btnSecondarySm =
  "inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-800 shadow-sm shadow-slate-900/[0.03] transition-colors hover:border-slate-400 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/30 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50";

export const btnDangerSm =
  "inline-flex items-center justify-center rounded-md border border-red-300 bg-white px-2 py-1 text-xs font-semibold text-red-900 shadow-sm transition-colors hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50";

export const btnGhost =
  "inline-flex items-center justify-center rounded-lg border border-slate-300/90 bg-white px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm shadow-slate-900/[0.04] transition-colors hover:border-slate-400 hover:bg-slate-50 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-100";

export const btnGhostLink =
  "text-sm font-medium text-indigo-700 underline-offset-2 hover:text-indigo-900 hover:underline";

export const btnPagination =
  "rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 shadow-sm shadow-slate-900/[0.04] transition-colors hover:border-slate-400 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/30 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-100 disabled:pointer-events-none disabled:opacity-40";

/** Delivery / channel chips for notifications and lists */
export function notificationChannelClass(channel: string): string {
  switch (channel) {
    case "in_app":
      return "rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-900";
    case "sms":
      return "rounded-full bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-900";
    case "whatsapp":
      return "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-900";
    default:
      return "rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700";
  }
}

export function notificationCategoryClass(): string {
  return "rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium capitalize text-amber-950 ring-1 ring-amber-200/80";
}

export const surfaceInfo =
  "rounded-xl border border-slate-300/90 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800";

export const surfaceSuccess =
  "rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950";

export const surfaceWarning =
  "rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950";

export const surfaceError =
  "rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800";
