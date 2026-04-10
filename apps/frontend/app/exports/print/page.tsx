"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

import { apiFetch } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import { useAuth } from "components/providers/AuthProvider";
import type { PrintExportPayload } from "lib/types";
import { btnPrimary, btnSecondary, surfaceError, surfaceInfo } from "lib/ui";

const KIND_TO_PATH: Record<string, string> = {
  attendance: "attendance/print",
  volunteers: "volunteers/print",
  users: "users/print",
  "parish-registry": "parish-registry/print",
};

function formatGeneratedAt(iso: string) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, { timeZone: "UTC" }) + " UTC";
}

function PrintExportInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();
  const kind = searchParams.get("kind") ?? "";
  const filterKey = searchParams.toString();

  const [data, setData] = useState<PrintExportPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Hydration guard
  const [hasHydrated, setHasHydrated] = useState(false);
  useEffect(() => {
    setHasHydrated(true);
  }, []);

  // Print-mode flag
  useEffect(() => {
    document.documentElement.setAttribute("data-print-export", "1");
    return () => document.documentElement.removeAttribute("data-print-export");
  }, []);

  useEffect(() => {
    if (!token || status !== "authenticated" || !isAdmin) {
      setLoading(false);
      return;
    }

    const pathSuffix = KIND_TO_PATH[kind];
    if (!pathSuffix) {
      setError("Unknown export kind. Open this page from the Exports admin screen.");
      setLoading(false);
      return;
    }

    const qs = new URLSearchParams();
    searchParams.forEach((v, k) => {
      if (k !== "kind" && v) qs.set(k, v);
    });

    const q = qs.toString();
    const path = `/api/v1/exports/${pathSuffix}${q ? `?${q}` : ""}`;

    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);

      try {
        const payload = await apiFetch<PrintExportPayload>(path, {
          method: "GET",
          token,
        });
        if (!cancelled) setData(payload);
      } catch (e: unknown) {
        if (isUnauthorized(e)) {
          clearSessionAndRedirect(router);
          return;
        }
        if (isInactiveAccountError(e)) {
          clearSessionAndRedirect(router, "account_inactive");
          return;
        }
        if (!cancelled) setError(toErrorMessage(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token, status, isAdmin, kind, filterKey, router, searchParams]);

  // Prevent mismatch before hydration
  if (!hasHydrated) {
    return (
      <div className="no-print rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-600">Loading…</p>
      </div>
    );
  }

  if (!token || status === "unauthenticated") {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-slate-600">Sign in to view this export.</p>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="no-print rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-600">Loading…</p>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-slate-600">Administrators only.</p>
      </div>
    );
  }

  const backHref = kind === "parish-registry" ? "/members" : "/exports";
  const backLabel = kind === "parish-registry" ? "Back to parish registry" : "Back to exports";

  return (
    <div className="space-y-6">
      {/* Screen-only chrome — hidden via .no-print in globals.css @media print */}
      <div className="no-print flex flex-wrap items-center gap-3">
        <button type="button" className={btnPrimary} onClick={() => window.print()}>
          Print or save as PDF
        </button>
        <Link href={backHref} className={btnSecondary}>
          {backLabel}
        </Link>
      </div>

      <div className={surfaceInfo + " no-print"}>
        Use your browser’s print dialog. Choose <strong>Save as PDF</strong> if you need a file
        instead of paper. Only the document below is printed.
      </div>

      {error ? <div className={surfaceError + " no-print"}>{error}</div> : null}

      {loading ? (
        <p className="no-print text-sm text-slate-600">Building export…</p>
      ) : null}

      {!loading && !error && data ? (
        <article className="print-export-document rounded-xl border border-slate-200 bg-white p-6 shadow-sm print:border-0 print:shadow-none">
          {(() => {
            const showOrg = !!(data.church_name || data.address || data.phone || data.email);
            return (
              <>
                {showOrg ? (
                  <div
                    className="mb-4 border-b border-slate-200 pb-4 print:border-slate-300"
                    role="group"
                    aria-label="Organization"
                  >
                    {data.church_name ? (
                      <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                        {data.church_name}
                      </h1>
                    ) : null}
                    {[data.address, data.phone, data.email].some(Boolean) ? (
                      <p className="mt-1 text-sm text-slate-600">
                        {[data.address, data.phone, data.email].filter(Boolean).join(" · ")}
                      </p>
                    ) : null}
                  </div>
                ) : null}

                <div
                  className="mb-6 border-b border-slate-200 pb-4 print:border-slate-300"
                  role="group"
                  aria-label="Export details"
                >
                  {showOrg ? (
                    <h2 className="text-xl font-bold text-slate-900">{data.title}</h2>
                  ) : (
                    <h1 className="text-2xl font-bold text-slate-900">{data.title}</h1>
                  )}
                  {data.subtitle ? (
                    <p className="mt-1 text-sm text-slate-600">{data.subtitle}</p>
                  ) : null}
                  <p className="mt-2 text-xs text-slate-500">
                    Generated {formatGeneratedAt(data.generated_at)}
                  </p>
                  {data.filters_summary ? (
                    <p className="mt-2 text-xs text-slate-600">Filters: {data.filters_summary}</p>
                  ) : null}
                </div>
              </>
            );
          })()}

          <div className="overflow-x-auto print:overflow-visible">
            <table className="w-full min-w-[640px] border-collapse text-left text-sm print:min-w-0">
              <thead>
                <tr>
                  {data.columns.map((col) => (
                    <th
                      key={col}
                      className="border-b border-slate-200 bg-slate-50 px-3 py-2 font-semibold text-slate-900 print:bg-white"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, ri) => (
                  <tr key={ri} className="odd:bg-white even:bg-slate-50/80 print:even:bg-white">
                    {row.map((cell, ci) => (
                      <td key={ci} className="border-b border-slate-100 px-3 py-2 text-slate-800">
                        {cell === null || cell === undefined || cell === "" ? "—" : String(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.rows.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No rows matched the current filters.</p>
          ) : null}
        </article>
      ) : null}
    </div>
  );
}

export default function ExportPrintPage() {
  return (
    <Suspense
      fallback={
        <div className="no-print rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-slate-600">Loading…</p>
        </div>
      }
    >
      <PrintExportInner />
    </Suspense>
  );
}
