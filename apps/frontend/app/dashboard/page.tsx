"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiFetch } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import { useAuth } from "components/providers/AuthProvider";
import PageShell, { ContentCard } from "components/layout/PageShell";
import type {
  AttendanceReportResponse,
  DashboardSummaryResponse,
  NotificationInsightsResponse,
  VolunteerReportResponse,
} from "lib/types";
import { fieldLabel, surfaceError, surfaceInfo } from "lib/ui";

function formatDateTime(iso: string) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-slate-300/90 bg-white p-5 shadow-sm shadow-slate-900/[0.04] ring-1 ring-slate-900/[0.04]">
      <p className="text-3xl font-bold tabular-nums text-slate-900">{value}</p>
      <p className="mt-1 text-sm font-medium text-slate-600">{label}</p>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [attendance, setAttendance] = useState<AttendanceReportResponse | null>(null);
  const [volunteers, setVolunteers] = useState<VolunteerReportResponse | null>(null);
  const [notifications, setNotifications] = useState<NotificationInsightsResponse | null>(null);

  const load = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [dash, att, vol, notif] = await Promise.all([
        apiFetch<DashboardSummaryResponse>("/api/v1/reports/dashboard", { method: "GET", token }),
        apiFetch<AttendanceReportResponse>("/api/v1/reports/attendance?limit=50", { method: "GET", token }),
        apiFetch<VolunteerReportResponse>("/api/v1/reports/volunteers?limit=20", { method: "GET", token }),
        apiFetch<NotificationInsightsResponse>("/api/v1/reports/notifications", { method: "GET", token }),
      ]);
      setSummary(dash);
      setAttendance(att);
      setVolunteers(vol);
      setNotifications(notif);
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
  }, [token, status, isAdmin, router]);

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
      <PageShell title="Dashboard" description="Sign in to continue.">
        <p className="text-base text-slate-600">This page requires a signed-in app user.</p>
      </PageShell>
    );
  }

  if (status === "loading") {
    return (
      <PageShell title="Dashboard" description="Loading…">
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (!isAdmin) {
    return (
      <PageShell title="Dashboard" description="Redirecting…">
        <ContentCard>
          <p className="text-sm text-slate-600">Administrators only.</p>
        </ContentCard>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Dashboard"
      description="Operational insights from app users, events, attendance, volunteers, and notifications—no parish registry data."
    >
      {error ? <div className={surfaceError}>{error}</div> : null}

      {loading ? (
        <ContentCard>
          <p className="text-sm text-slate-600">Loading insights…</p>
        </ContentCard>
      ) : summary ? (
        <>
          <section className="space-y-4">
            <h2 className="shepherd-section-title">Overview</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <StatCard label="Total app users" value={summary.total_users} />
              <StatCard
                label="Active users (last 30 days)"
                value={summary.active_users_last_30_days}
              />
              <StatCard label="Upcoming events" value={summary.upcoming_events_count} />
              <StatCard label="Events this week" value={summary.events_this_week} />
              <StatCard
                label="Volunteer assignments (upcoming)"
                value={summary.volunteers_assigned_upcoming}
              />
              <StatCard label="Unread in-app messages (all users)" value={summary.unread_notifications_total} />
            </div>
            <p className={surfaceInfo}>
              Ministries: {summary.active_ministries} active of {summary.total_ministries} total.
            </p>
          </section>

          <ContentCard className="space-y-4">
            <h2 className="shepherd-section-title">Attendance by event</h2>
            <p className="text-sm text-slate-600">
              Events with at least one attendance row, most recent first.
            </p>
            {!attendance || attendance.items.length === 0 ? (
              <p className="text-sm text-slate-600">No attendance recorded yet.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-3 py-2">Event</th>
                      <th className="px-3 py-2">Date</th>
                      <th className="px-3 py-2">Attendance rows</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {attendance.items.map((row) => (
                      <tr key={row.event_id}>
                        <td className="px-3 py-2 font-medium text-slate-900">
                          <Link
                            href={`/events/${row.event_id}`}
                            className="text-indigo-800 hover:text-indigo-950 hover:underline"
                          >
                            {row.event_title}
                          </Link>
                        </td>
                        <td className="px-3 py-2 text-slate-700">{formatDateTime(row.start_at)}</td>
                        <td className="px-3 py-2 tabular-nums text-slate-800">{row.attendance_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </ContentCard>

          <ContentCard className="space-y-4">
            <h2 className="shepherd-section-title">Top volunteers</h2>
            <p className="text-sm text-slate-600">By total volunteer assignments (all time).</p>
            {!volunteers || volunteers.items.length === 0 ? (
              <p className="text-sm text-slate-600">No volunteer assignments yet.</p>
            ) : (
              <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
                {volunteers.items.map((v) => (
                  <li
                    key={v.user_id}
                    className="flex items-center justify-between gap-3 px-4 py-3 text-sm"
                  >
                    <span className="font-medium text-slate-900">{v.full_name}</span>
                    <span className="tabular-nums text-slate-700">{v.assignments_count} assignments</span>
                  </li>
                ))}
              </ul>
            )}
          </ContentCard>

          <ContentCard className="space-y-4">
            <h2 className="shepherd-section-title">Notifications & delivery</h2>
            {notifications ? (
              <dl className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-stone-50/60 px-4 py-3">
                  <dt className={fieldLabel}>Notifications sent</dt>
                  <dd className="mt-1 text-2xl font-bold tabular-nums text-slate-900">
                    {notifications.total_notifications_sent}
                  </dd>
                </div>
                <div className="rounded-lg border border-slate-200 bg-stone-50/60 px-4 py-3">
                  <dt className={fieldLabel}>Total recipient rows</dt>
                  <dd className="mt-1 text-2xl font-bold tabular-nums text-slate-900">
                    {notifications.total_recipients}
                  </dd>
                </div>
                <div className="rounded-lg border border-slate-200 bg-stone-50/60 px-4 py-3">
                  <dt className={fieldLabel}>In-app (sent / delivered)</dt>
                  <dd className="mt-1 text-2xl font-bold tabular-nums text-slate-900">
                    {notifications.in_app_delivered}
                  </dd>
                  {notifications.in_app_failed > 0 ? (
                    <p className="mt-1 text-xs text-red-800">Failed: {notifications.in_app_failed}</p>
                  ) : null}
                </div>
                <div className="rounded-lg border border-slate-200 bg-stone-50/60 px-4 py-3">
                  <dt className={fieldLabel}>SMS</dt>
                  <dd className="mt-1 text-slate-800">
                    Attempted: <span className="font-semibold tabular-nums">{notifications.sms_attempted}</span>
                    {" · "}
                    Failed:{" "}
                    <span className="font-semibold tabular-nums text-red-800">{notifications.sms_failed}</span>
                  </dd>
                </div>
                <div className="rounded-lg border border-slate-200 bg-stone-50/60 px-4 py-3 sm:col-span-2">
                  <dt className={fieldLabel}>WhatsApp</dt>
                  <dd className="mt-1 text-slate-800">
                    Attempted:{" "}
                    <span className="font-semibold tabular-nums">{notifications.whatsapp_attempted}</span>
                    {" · "}
                    Failed:{" "}
                    <span className="font-semibold tabular-nums text-red-800">
                      {notifications.whatsapp_failed}
                    </span>
                  </dd>
                </div>
              </dl>
            ) : null}
          </ContentCard>
        </>
      ) : null}
    </PageShell>
  );
}
