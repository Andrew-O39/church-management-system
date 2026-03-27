"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiFetch } from "lib/api";
import { fetchAllListPages } from "lib/api-pagination";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import { useAuth } from "components/providers/AuthProvider";

import type {
  AttendanceStatus,
  EventAttendanceListResponse,
  EventDetailResponse,
  EventMemberViewResponse,
  EventType,
  EventVisibility,
  MemberListResponse,
  MyAttendanceResponse,
  MinistryListResponse,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";

const inputCls =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400";

const EVENT_TYPES: EventType[] = ["service", "meeting", "rehearsal", "retreat", "conference", "other"];
const EVENT_VISIBILITIES: EventVisibility[] = ["public", "internal"];
const ATTENDANCE_OPTIONS: AttendanceStatus[] = ["present", "absent", "excused"];

function toIsoFromDatetimeLocal(v: string) {
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d.toISOString();
}

function isoToDatetimeLocal(iso: string) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatDateTime(v: string) {
  const d = new Date(v);
  if (isNaN(d.getTime())) return v;
  return d.toLocaleString();
}

export default function EventDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const token = getAccessToken();
  const { isAdmin, status } = useAuth();
  const eventId = params.id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<EventDetailResponse | EventMemberViewResponse | null>(null);

  const [ministries, setMinistries] = useState<MinistryListResponse["items"]>([]);
  const [attendanceByUser, setAttendanceByUser] = useState<Record<string, AttendanceStatus>>({});
  const [attendanceRowPhase, setAttendanceRowPhase] = useState<Record<string, "idle" | "saving" | "success" | "error">>(
    {},
  );
  const [attendanceRowError, setAttendanceRowError] = useState<Record<string, string>>({});
  const [eligibleUsers, setEligibleUsers] = useState<MemberListResponse["items"]>([]);
  const [myAttendance, setMyAttendance] = useState<MyAttendanceResponse | null>(null);

  // Admin edit state
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editType, setEditType] = useState<EventType>("service");
  const [editVisibility, setEditVisibility] = useState<EventVisibility>("public");
  const [editLocation, setEditLocation] = useState("");
  const [editIsActive, setEditIsActive] = useState(true);
  const [editMinistryId, setEditMinistryId] = useState<string>("none");
  const [editStartAt, setEditStartAt] = useState("");
  const [editEndAt, setEditEndAt] = useState("");

  const load = useCallback(async () => {
    if (!token || status !== "authenticated") {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      if (isAdmin) {
        const d = await apiFetch<EventDetailResponse>(`/api/v1/events/${eventId}`, {
          method: "GET",
          token,
        });
        setDetail(d);
        setEditTitle(d.title);
        setEditDesc(d.description ?? "");
        setEditType(d.event_type);
        setEditVisibility(d.visibility);
        setEditLocation(d.location);
        setEditIsActive(d.is_active);
        setEditMinistryId(d.ministry_id ?? "none");
        setEditStartAt(isoToDatetimeLocal(d.start_at));
        setEditEndAt(isoToDatetimeLocal(d.end_at));

        const ministryItems = await fetchAllListPages({
          fetchPage: async (page, pageSize) => {
            const qs = new URLSearchParams({
              is_active: "true",
              page: String(page),
              page_size: String(pageSize),
            });
            return apiFetch<MinistryListResponse>(`/api/v1/ministries/?${qs.toString()}`, {
              method: "GET",
              token,
            });
          },
        });
        setMinistries(ministryItems);

        const attendance = await apiFetch<EventAttendanceListResponse>(
          `/api/v1/events/${eventId}/attendance`,
          { method: "GET", token },
        );
        const byUser: Record<string, AttendanceStatus> = {};
        attendance.items.forEach((a) => {
          byUser[a.user_id] = a.status;
        });
        setAttendanceByUser(byUser);

        const allMembers = await fetchAllListPages({
          fetchPage: async (page, pageSize) => {
            const qs = new URLSearchParams({
              is_active: "true",
              page: String(page),
              page_size: String(pageSize),
            });
            return apiFetch<MemberListResponse>(`/api/v1/members/?${qs.toString()}`, {
              method: "GET",
              token,
            });
          },
        });

        if (d.ministry_id) {
          const mDetail = await apiFetch<{
            members: Array<{
              user_id: string;
              is_active: boolean;
            }>;
          }>(`/api/v1/ministries/${d.ministry_id}`, { method: "GET", token });
          const activeIds = new Set(
            mDetail.members.filter((m) => m.is_active).map((m) => m.user_id),
          );
          setEligibleUsers(allMembers.filter((m) => activeIds.has(m.member_id)));
        } else {
          setEligibleUsers(allMembers);
        }
      } else {
        const d = await apiFetch<EventMemberViewResponse>(`/api/v1/events/${eventId}/view`, {
          method: "GET",
          token,
        });
        setDetail(d);
        const mine = await apiFetch<MyAttendanceResponse>(
          `/api/v1/events/${eventId}/attendance/me`,
          { method: "GET", token },
        );
        setMyAttendance(mine);
      }
    } catch (err) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router, "session_expired");
        return;
      }
      if (isInactiveAccountError(err)) {
        clearSessionAndRedirect(router, "account_inactive");
        return;
      }
      setError(toErrorMessage(err));
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [token, status, isAdmin, eventId, router]);

  useEffect(() => {
    if (status === "loading") return;
    void load();
  }, [load, status]);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !detail || !("event_id" in detail)) return;

    const startIso = toIsoFromDatetimeLocal(editStartAt);
    const endIso = toIsoFromDatetimeLocal(editEndAt);
    if (!editTitle.trim() || !startIso || !endIso || !editLocation.trim()) {
      setError("Please fill title, start/end date, and location.");
      return;
    }

    setError(null);
    try {
      const updated = await apiFetch<EventDetailResponse>(`/api/v1/events/${eventId}`, {
        method: "PATCH",
        token,
        body: {
          title: editTitle.trim(),
          description: editDesc.trim() || null,
          event_type: editType,
          start_at: startIso,
          end_at: endIso,
          location: editLocation.trim(),
          is_active: editIsActive,
          visibility: editVisibility,
          ministry_id: editMinistryId === "none" ? null : editMinistryId,
        },
      });
      setDetail(updated);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  async function onDeactivate() {
    if (!token || !isAdmin) return;
    setError(null);
    try {
      await apiFetch(`/api/v1/events/${eventId}`, { method: "DELETE", token });
      router.replace("/events");
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  async function onAttendanceStatusChange(userId: string, raw: string) {
    if (!token || !isAdmin || !detail || !("event_id" in detail) || !detail.is_active) return;
    if (!raw) return;
    const nextStatus = raw as AttendanceStatus;
    if (!ATTENDANCE_OPTIONS.includes(nextStatus)) return;

    const hadRecord = Boolean(attendanceByUser[userId]);
    const previousStatus = attendanceByUser[userId];

    setAttendanceByUser((prev) => ({ ...prev, [userId]: nextStatus }));
    setAttendanceRowPhase((prev) => ({ ...prev, [userId]: "saving" }));
    setAttendanceRowError((prev) => {
      const next = { ...prev };
      delete next[userId];
      return next;
    });

    try {
      if (hadRecord) {
        await apiFetch(`/api/v1/events/${eventId}/attendance/${userId}`, {
          method: "PATCH",
          token,
          body: { status: nextStatus },
        });
      } else {
        await apiFetch(`/api/v1/events/${eventId}/attendance`, {
          method: "POST",
          token,
          body: { user_id: userId, status: nextStatus },
        });
      }
      setAttendanceRowPhase((prev) => ({ ...prev, [userId]: "success" }));
      window.setTimeout(() => {
        setAttendanceRowPhase((prev) =>
          prev[userId] === "success" ? { ...prev, [userId]: "idle" } : prev,
        );
      }, 2000);
    } catch (err) {
      setAttendanceByUser((prev) => {
        const next = { ...prev };
        if (previousStatus === undefined) delete next[userId];
        else next[userId] = previousStatus;
        return next;
      });
      setAttendanceRowPhase((prev) => ({ ...prev, [userId]: "error" }));
      setAttendanceRowError((prev) => ({ ...prev, [userId]: toErrorMessage(err) }));
    }
  }

  const ministryLabel = useMemo(() => {
    if (!detail) return null;
    const minId = detail.ministry_id;
    if (!minId) return "Church-wide";
    if (detail.ministry_name) return detail.ministry_name;
    const found = ministries.find((m) => m.id === minId);
    return found?.name ?? "Ministry";
  }, [detail, ministries]);

  if (status === "loading" || loading) {
    return (
      <PageShell title="Event" description="Loading…">
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            Loading…
          </div>
        </ContentCard>
      </PageShell>
    );
  }

  if (error && !detail) {
    return (
      <PageShell title="Event" description="Event details">
        <ContentCard>
          <p className="text-sm text-red-800">{error}</p>
          <Link href="/events" className="mt-4 inline-block text-sm font-medium text-slate-800 underline">
            ← Back to events
          </Link>
        </ContentCard>
      </PageShell>
    );
  }

  if (!detail) return null;

  return (
    <PageShell title={detail.title} description="Event details">
      <div className="space-y-4">
        <div>
          <Link href="/events" className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline">
            ← All events
          </Link>
        </div>

        {isAdmin ? (
          <>
          <ContentCard className="space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">Edit event</h2>
            <form onSubmit={onSave} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Title</label>
                  <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className={inputCls} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Type</label>
                  <select value={editType} onChange={(e) => setEditType(e.target.value as EventType)} className={inputCls}>
                    {EVENT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Description</label>
                <textarea value={editDesc} onChange={(e) => setEditDesc(e.target.value)} className={`${inputCls} min-h-[88px] resize-y`} />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Start</label>
                  <input type="datetime-local" value={editStartAt} onChange={(e) => setEditStartAt(e.target.value)} className={inputCls} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">End</label>
                  <input type="datetime-local" value={editEndAt} onChange={(e) => setEditEndAt(e.target.value)} className={inputCls} />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Location</label>
                  <input value={editLocation} onChange={(e) => setEditLocation(e.target.value)} className={inputCls} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Visibility</label>
                  <select value={editVisibility} onChange={(e) => setEditVisibility(e.target.value as EventVisibility)} className={inputCls}>
                    {EVENT_VISIBILITIES.map((v) => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Ministry (optional)</label>
                  <select value={editMinistryId} onChange={(e) => setEditMinistryId(e.target.value)} className={inputCls}>
                    <option value="none">Church-wide</option>
                    {ministries.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </div>
                <label className="flex items-center gap-2 pt-6 md:pt-0">
                  <input type="checkbox" checked={editIsActive} onChange={(e) => setEditIsActive(e.target.checked)} className="rounded border-slate-300" />
                  <span className="text-sm font-medium text-slate-800">Active</span>
                </label>
              </div>

              {error ? (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {error}
                </div>
              ) : null}

              <div className="flex flex-wrap gap-3">
                <button type="submit" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800">
                  Save
                </button>
                <button
                  type="button"
                  onClick={onDeactivate}
                  className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                >
                  Deactivate
                </button>
              </div>
            </form>
          </ContentCard>
          <ContentCard className="space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">Attendance</h2>
            {!detail.is_active ? (
              <p className="text-sm text-amber-800">
                Event is inactive. Attendance recording is disabled.
              </p>
            ) : null}
            {eligibleUsers.length === 0 ? (
              <p className="text-sm text-slate-600">No eligible users for this event.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-100 bg-white text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-3 py-2">Name</th>
                      <th className="px-3 py-2">Email</th>
                      <th className="px-3 py-2">Attendance status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {eligibleUsers.map((u) => {
                      const persisted = attendanceByUser[u.member_id];
                      const selectValue = persisted ?? "";
                      const phase = attendanceRowPhase[u.member_id] ?? "idle";
                      const rowErr = attendanceRowError[u.member_id];
                      return (
                        <tr key={u.member_id}>
                          <td className="px-3 py-2">{u.full_name}</td>
                          <td className="px-3 py-2 text-slate-700">{u.email}</td>
                          <td className="px-3 py-2 align-top">
                            <select
                              value={selectValue}
                              onChange={(e) => {
                                void onAttendanceStatusChange(u.member_id, e.target.value);
                              }}
                              className={inputCls}
                              disabled={!detail.is_active || phase === "saving"}
                              aria-busy={phase === "saving"}
                            >
                              <option value="">Select status</option>
                              {ATTENDANCE_OPTIONS.map((opt) => (
                                <option key={opt} value={opt}>
                                  {opt}
                                </option>
                              ))}
                            </select>
                            {phase === "saving" ? (
                              <p className="mt-1 text-xs text-slate-600">Saving…</p>
                            ) : null}
                            {phase === "success" ? (
                              <p className="mt-1 text-xs text-green-800">Saved</p>
                            ) : null}
                            {phase === "error" && rowErr ? (
                              <p className="mt-1 text-xs text-red-800">{rowErr}</p>
                            ) : null}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </ContentCard>
          </>
        ) : (
          <ContentCard className="space-y-3">
            <p className="text-sm text-slate-700">
              {formatDateTime(detail.start_at)} → {formatDateTime(detail.end_at)}
            </p>
            <p className="text-sm text-slate-700">
              Location: {detail.location}
            </p>
            <p className="text-sm text-slate-700">
              Scope: {ministryLabel}
            </p>
            <p className="text-sm text-slate-500">
              Type: {detail.event_type} · Visibility: {detail.visibility}
            </p>
            {detail.description ? <p className="text-sm text-slate-700">{detail.description}</p> : null}
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              Your attendance:{" "}
              <span className="font-medium capitalize">
                {myAttendance?.recorded ? myAttendance.status : "Not recorded"}
              </span>
            </div>
          </ContentCard>
        )}
      </div>
    </PageShell>
  );
}

