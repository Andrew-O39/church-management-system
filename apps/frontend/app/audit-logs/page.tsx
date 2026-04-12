"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import PageShell, { ContentCard } from "components/layout/PageShell";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import {
  formatMetadataJson,
  getAuditActionLabel,
  getAuditTargetSummary,
} from "lib/auditLogDisplay";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import type { AuditLogItem, AuditLogListResponse } from "lib/types";
import { btnPrimary, btnSecondary, fieldInput, fieldLabel, surfaceError, surfaceInfo } from "lib/ui";

const PAGE_TITLE = "Audit log";
const PAGE_DESCRIPTION =
  "Track important administrative and security-related actions in Shepherd.";

function formatWhen(iso: string) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function formatActor(row: AuditLogListResponse["items"][0]) {
  const name = row.actor_display_name?.trim();
  const email = row.actor_email?.trim();
  if (name && email) return `${name} (${email})`;
  if (email) return email;
  if (row.actor_user_id) return row.actor_user_id;
  return "—";
}

export default function AuditLogsPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AuditLogListResponse | null>(null);
  const [actionInput, setActionInput] = useState("");
  const [dateFromInput, setDateFromInput] = useState("");
  const [dateToInput, setDateToInput] = useState("");
  const [appliedAction, setAppliedAction] = useState("");
  const [appliedFrom, setAppliedFrom] = useState("");
  const [appliedTo, setAppliedTo] = useState("");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const pageSize = 30;

  const load = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      if (appliedAction.trim()) params.set("action", appliedAction.trim());
      if (appliedFrom) params.set("date_from", new Date(appliedFrom).toISOString());
      if (appliedTo) params.set("date_to", new Date(appliedTo).toISOString());
      const res = await apiFetch<AuditLogListResponse>(`/api/v1/audit-logs/?${params.toString()}`, {
        method: "GET",
        token,
      });
      setData(res);
    } catch (e: unknown) {
      if (isUnauthorized(e)) {
        clearSessionAndRedirect(router);
        return;
      }
      if (isInactiveAccountError(e)) {
        clearSessionAndRedirect(router, "account_inactive");
        return;
      }
      setError(toErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [token, status, isAdmin, router, page, appliedAction, appliedFrom, appliedTo]);

  useEffect(() => {
    if (status === "authenticated" && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, isAdmin, router]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!token || status === "unauthenticated") {
    return (
      <PageShell title={PAGE_TITLE} description={PAGE_DESCRIPTION}>
        <p className="text-base text-slate-600">This page requires a signed-in administrator.</p>
      </PageShell>
    );
  }

  if (status === "loading") {
    return (
      <PageShell title={PAGE_TITLE} description={PAGE_DESCRIPTION}>
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (!isAdmin) {
    return (
      <PageShell title={PAGE_TITLE} description={PAGE_DESCRIPTION}>
        <p className="text-base text-slate-600">Administrator access only.</p>
      </PageShell>
    );
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <PageShell title={PAGE_TITLE} description={PAGE_DESCRIPTION}>
      <ContentCard>
        <p className="text-sm leading-relaxed text-slate-600">
          Recent entries are shown newest first. Filters use the same action codes the server stores (for example{" "}
          <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">events.create</code>).
        </p>

        <div className="mt-6 flex flex-col gap-4 border-t border-slate-200/90 pt-6 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="min-w-[12rem] flex-1">
            <label className={fieldLabel} htmlFor="audit-action">
              Filter by action code
            </label>
            <input
              id="audit-action"
              className={fieldInput}
              placeholder="e.g. events.create"
              value={actionInput}
              onChange={(e) => setActionInput(e.target.value)}
            />
          </div>
          <div>
            <label className={fieldLabel} htmlFor="audit-from">
              From
            </label>
            <input
              id="audit-from"
              type="datetime-local"
              className={fieldInput}
              value={dateFromInput}
              onChange={(e) => setDateFromInput(e.target.value)}
            />
          </div>
          <div>
            <label className={fieldLabel} htmlFor="audit-to">
              To
            </label>
            <input
              id="audit-to"
              type="datetime-local"
              className={fieldInput}
              value={dateToInput}
              onChange={(e) => setDateToInput(e.target.value)}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={btnPrimary}
              onClick={() => {
                setPage(1);
                setAppliedAction(actionInput);
                setAppliedFrom(dateFromInput);
                setAppliedTo(dateToInput);
              }}
            >
              Apply
            </button>
            <button
              type="button"
              className={btnSecondary}
              onClick={() => {
                setActionInput("");
                setDateFromInput("");
                setDateToInput("");
                setAppliedAction("");
                setAppliedFrom("");
                setAppliedTo("");
                setPage(1);
              }}
            >
              Clear
            </button>
          </div>
        </div>

        {error ? <p className={`${surfaceError} mt-4`}>{error}</p> : null}

        {loading ? (
          <p className={`${surfaceInfo} mt-6`}>Loading audit events…</p>
        ) : data && data.items.length === 0 ? (
          <p className="mt-6 text-sm text-slate-600">No audit events match the current filters.</p>
        ) : data ? (
          <>
            <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200/90">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  <tr>
                    <th className="px-3 py-2.5">When</th>
                    <th className="px-3 py-2.5">Who</th>
                    <th className="px-3 py-2.5">What</th>
                    <th className="px-3 py-2.5">Context</th>
                    <th className="px-3 py-2.5">Details</th>
                    <th className="w-10 px-2 py-2.5" aria-label="Expand" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {data.items.map((row) => (
                    <AuditRow
                      key={row.id}
                      row={row}
                      expanded={expandedId === row.id}
                      onToggle={() => setExpandedId((id) => (id === row.id ? null : row.id))}
                    />
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Showing {data.items.length} of {data.total} entr{data.total === 1 ? "y" : "ies"}.
            </p>
            {totalPages > 1 ? (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  className={btnSecondary}
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <span className="text-sm text-slate-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  className={btnSecondary}
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                </button>
              </div>
            ) : null}
          </>
        ) : null}
      </ContentCard>
    </PageShell>
  );
}

function AuditRow({
  row,
  expanded,
  onToggle,
}: {
  row: AuditLogItem;
  expanded: boolean;
  onToggle: () => void;
}) {
  const meta =
    row.metadata_json && typeof row.metadata_json === "object"
      ? (row.metadata_json as Record<string, unknown>)
      : {};

  return (
    <>
      <tr className="align-top">
        <td className="whitespace-nowrap px-3 py-2.5 text-slate-700">{formatWhen(row.created_at)}</td>
        <td className="max-w-[11rem] break-words px-3 py-2.5 text-slate-800">{formatActor(row)}</td>
        <td className="max-w-[10rem] px-3 py-2.5 font-medium text-slate-900">
          {getAuditActionLabel(row.action)}
        </td>
        <td className="max-w-[12rem] px-3 py-2.5 text-slate-700">{getAuditTargetSummary(row)}</td>
        <td className="max-w-md px-3 py-2.5 text-slate-700">{row.summary}</td>
        <td className="px-1 py-2 align-middle">
          <button
            type="button"
            onClick={onToggle}
            className="rounded p-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-50"
            aria-expanded={expanded}
          >
            {expanded ? "▲" : "▼"}
          </button>
        </td>
      </tr>
      {expanded ? (
        <tr className="bg-slate-50/90">
          <td colSpan={6} className="px-4 py-3 text-xs leading-relaxed text-slate-600">
            <p className="font-semibold text-slate-800">Technical details</p>
            <dl className="mt-2 grid gap-1 sm:grid-cols-[8rem_1fr]">
              {row.actor_display_name ? (
                <>
                  <dt className="text-slate-500">Actor name</dt>
                  <dd>{row.actor_display_name}</dd>
                </>
              ) : null}
              <dt className="text-slate-500">Action code</dt>
              <dd className="font-mono text-slate-800">{row.action}</dd>
              {row.target_type ? (
                <>
                  <dt className="text-slate-500">Target type</dt>
                  <dd>{row.target_type}</dd>
                </>
              ) : null}
              {row.target_id ? (
                <>
                  <dt className="text-slate-500">Target ID</dt>
                  <dd className="break-all font-mono text-[11px] text-slate-600">{row.target_id}</dd>
                </>
              ) : null}
              {row.actor_user_id ? (
                <>
                  <dt className="text-slate-500">Actor user ID</dt>
                  <dd className="break-all font-mono text-[11px] text-slate-600">{row.actor_user_id}</dd>
                </>
              ) : null}
              {row.ip_address ? (
                <>
                  <dt className="text-slate-500">IP</dt>
                  <dd className="font-mono text-[11px]">{row.ip_address}</dd>
                </>
              ) : null}
            </dl>
            {Object.keys(meta).length > 0 ? (
              <div className="mt-3">
                <p className="font-semibold text-slate-800">Metadata</p>
                <pre className="mt-1 max-h-48 overflow-auto rounded-lg border border-slate-200 bg-white p-2 font-mono text-[11px] text-slate-700">
                  {formatMetadataJson(meta)}
                </pre>
              </div>
            ) : null}
          </td>
        </tr>
      ) : null}
    </>
  );
}
