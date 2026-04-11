"use client";

import { useId, useState, type ReactNode } from "react";

export type CollapsibleSectionProps = {
  title: string;
  description?: ReactNode;
  /** When false, section body starts collapsed. Default true. */
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
  /** Optional id for anchor links / aria-controls */
  id?: string;
};

/**
 * Reusable expandable section for long admin pages — matches Shepherd card styling.
 */
export default function CollapsibleSection({
  title,
  description,
  defaultOpen = true,
  children,
  className = "",
  id,
}: CollapsibleSectionProps) {
  const genId = useId();
  const panelId = id ?? `collapsible-panel-${genId}`;
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section
      className={[
        "rounded-2xl border border-slate-300/95 bg-white shadow-md shadow-slate-900/[0.07] ring-1 ring-slate-900/[0.06]",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        type="button"
        className="flex w-full items-start justify-between gap-3 rounded-t-2xl p-6 text-left transition-colors hover:bg-slate-50/90"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={panelId}
      >
        <div className="min-w-0 flex-1">
          <h2 className="shepherd-section-title">{title}</h2>
          {description ? (
            <div className="mt-1.5 text-sm leading-relaxed text-slate-600">{description}</div>
          ) : null}
        </div>
        <span
          className={`mt-1 shrink-0 text-slate-500 transition-transform ${open ? "rotate-180" : ""}`}
          aria-hidden
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" className="block">
            <path
              fillRule="evenodd"
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.94a.75.75 0 111.08 1.04l-4.24 4.5a.75.75 0 01-1.08 0l-4.24-4.5a.75.75 0 01.02-1.06z"
              clipRule="evenodd"
            />
          </svg>
        </span>
      </button>
      {open ? (
        <div id={panelId} className="border-t border-slate-100 px-6 pb-6 pt-4">
          {children}
        </div>
      ) : null}
    </section>
  );
}
