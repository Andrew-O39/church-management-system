"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { apiFetch } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import { useAuth } from "components/providers/AuthProvider";
import type { NotificationDetailResponse } from "lib/types";

import PageShell, { ContentCard } from "components/layout/PageShell";

function formatDateTime(v: string | null) {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d.getTime())) return v;
  return d.toLocaleString();
}

export default function NotificationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : "";
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<NotificationDetailResponse | null>(null);

  const load = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin || !id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<NotificationDetailResponse>(`/api/v1/notifications/${id}`, {
        method: "GET",
        token,
      });
      setDetail(res);
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
  }, [token, status, isAdmin, id, router]);

  useEffect(() => {
    if (status === "authenticated" && !isAdmin) {
      router.replace("/profile?notice=admin_only");
      return;
    }
    void load();
  }, [load, status, isAdmin, router]);

  if (!token || status !== "authenticated") {
    return (
      <PageShell title="Notification" description="Sign in to continue.">
        <p className="text-sm text-slate-600">This page requires a signed-in admin.</p>
      </PageShell>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <PageShell
      title="Notification detail"
      description={
        <Link href="/notifications" className="text-slate-700 underline hover:text-slate-900">
          ← Back to notifications
        </Link>
      }
    >
      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}
      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : detail ? (
        <div className="space-y-6">
          <ContentCard>
            <h2 className="text-lg font-semibold text-slate-900">{detail.title}</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{detail.body}</p>
            <dl className="mt-4 grid gap-2 text-sm text-slate-600">
              <div>
                <dt className="font-medium text-slate-700">Category</dt>
                <dd>{detail.category}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-700">Channels</dt>
                <dd className="flex flex-wrap gap-1">
                  {detail.channels.map((c) => (
                    <span key={c} className="rounded bg-slate-100 px-2 py-0.5 text-xs">
                      {c}
                    </span>
                  ))}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-700">Audience</dt>
                <dd>{detail.audience_type}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-700">Sent</dt>
                <dd>{formatDateTime(detail.sent_at ?? detail.created_at)}</dd>
              </div>
            </dl>
          </ContentCard>
          {detail.delivery_summary ? (
            <ContentCard>
              <h3 className="text-base font-semibold text-slate-900">Delivery summary</h3>
              <dl className="mt-2 grid gap-2 text-sm text-slate-600">
                <div>
                  <dt className="font-medium text-slate-700">Audience resolved</dt>
                  <dd>{detail.delivery_summary.audience_resolved_count}</dd>
                </div>
                <div>
                  <dt className="font-medium text-slate-700">In-app recipients</dt>
                  <dd>{detail.delivery_summary.in_app_recipient_count}</dd>
                </div>
                <div>
                  <dt className="font-medium text-slate-700">SMS</dt>
                  <dd>
                    attempted {detail.delivery_summary.sms_attempted}, sent{" "}
                    {detail.delivery_summary.sms_sent}, failed {detail.delivery_summary.sms_failed}, skipped
                    (no phone) {detail.delivery_summary.sms_skipped_no_phone}
                  </dd>
                </div>
              </dl>
            </ContentCard>
          ) : null}
          <ContentCard>
            <h3 className="text-base font-semibold text-slate-900">
              Recipients ({detail.recipients.length})
            </h3>
            <ul className="mt-3 divide-y divide-slate-100">
              {detail.recipients.map((r) => (
                <li key={r.id} className="py-3 text-sm">
                  <div className="flex flex-wrap justify-between gap-2">
                    <span className="font-mono text-xs text-slate-700">{r.user_id}</span>
                    <span className="text-slate-500">
                      {r.status}
                      {r.read_at ? ` · read ${formatDateTime(r.read_at)}` : ""}
                    </span>
                  </div>
                  <ul className="mt-2 space-y-1 border-l-2 border-slate-100 pl-3 text-xs text-slate-600">
                    {r.delivery_attempts.map((a) => (
                      <li key={a.id}>
                        <span className="font-medium">{a.channel}</span>: {a.status}
                        {a.provider_message_id ? ` · ${a.provider_message_id}` : ""}
                        {a.error_detail ? ` — ${a.error_detail}` : ""}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </ContentCard>
        </div>
      ) : null}
    </PageShell>
  );
}
