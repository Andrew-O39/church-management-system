"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiFetch } from "lib/api";
import { fetchAllListPages } from "lib/api-pagination";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import {
  getApiErrorDetail,
  isConflictError,
  isInactiveAccountError,
  isUnauthorized,
  toErrorMessage,
} from "lib/errors";
import { useAuth } from "components/providers/AuthProvider";

import type {
  AttendanceStatus,
  EligibleChurchMemberListItem,
  EventAttendanceListResponse,
  EventDetailResponse,
  EventMemberViewResponse,
  EventReminderAudienceType,
  EventReminderRuleCreate,
  EventReminderRuleListResponse,
  EventReminderRuleResponse,
  EventType,
  EventVisibility,
  EventVolunteerListResponse,
  MyAttendanceResponse,
  MyEventVolunteerAssignmentsResponse,
  MinistryListResponse,
  NotificationChannel,
  RunDueRemindersResponse,
  VolunteerAssignmentRow,
  VolunteerRoleListResponse,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import {
  btnDangerSm,
  btnPrimary,
  btnPrimarySm,
  btnSecondary,
  btnSecondarySm,
  fieldInput,
  surfaceError,
  surfaceInfo,
} from "lib/ui";

const inputCls = fieldInput;

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

function formatReminderOffset(m: number): string {
  if (m === 60) return "1 hour before";
  if (m === 1440) return "24 hours before";
  if (m === 10080) return "7 days before";
  return `${m} minutes before`;
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
  const [attendanceByUserId, setAttendanceByUserId] = useState<Record<string, AttendanceStatus>>({});
  const [attendanceRowPhase, setAttendanceRowPhase] = useState<Record<string, "idle" | "saving" | "success" | "error">>(
    {},
  );
  const [attendanceRowError, setAttendanceRowError] = useState<Record<string, string>>({});
  const [eligibleChurchMembers, setEligibleChurchMembers] = useState<EligibleChurchMemberListItem[]>([]);
  const [myAttendance, setMyAttendance] = useState<MyAttendanceResponse | null>(null);

  const [volunteerAssignments, setVolunteerAssignments] = useState<VolunteerAssignmentRow[]>([]);
  const [volunteerRolesForEvent, setVolunteerRolesForEvent] = useState<VolunteerRoleListResponse["items"]>([]);
  const [volNewUserId, setVolNewUserId] = useState("");
  const [volNewRoleId, setVolNewRoleId] = useState("");
  const [volNewNotes, setVolNewNotes] = useState("");
  const [volAssigning, setVolAssigning] = useState(false);
  const [volNotesDraft, setVolNotesDraft] = useState<Record<string, string>>({});
  const [volunteerSectionError, setVolunteerSectionError] = useState<string | null>(null);
  const [volNotesPhase, setVolNotesPhase] = useState<Record<string, "idle" | "saving" | "saved" | "error">>({});
  const [volNotesError, setVolNotesError] = useState<Record<string, string>>({});

  const [myVolunteers, setMyVolunteers] = useState<VolunteerAssignmentRow[]>([]);

  const [reminderRules, setReminderRules] = useState<EventReminderRuleResponse[]>([]);
  const [reminderAudience, setReminderAudience] = useState<EventReminderAudienceType>("event_volunteers");
  const [remOffsetChoice, setRemOffsetChoice] = useState<string>("60");
  const [remCustomOffset, setRemCustomOffset] = useState("120");
  const [remInApp, setRemInApp] = useState(true);
  const [remSms, setRemSms] = useState(false);
  const [remWa, setRemWa] = useState(false);
  const [reminderSaving, setReminderSaving] = useState(false);
  const [reminderSectionError, setReminderSectionError] = useState<string | null>(null);
  const [runDueBusy, setRunDueBusy] = useState(false);
  const [runDueSummary, setRunDueSummary] = useState<RunDueRemindersResponse | null>(null);

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
        setAttendanceByUserId(byUser);

        const eligible = await apiFetch<EligibleChurchMemberListItem[]>(
          `/api/v1/church-members/eligible-for-event/${encodeURIComponent(eventId)}`,
          { method: "GET", token },
        );
        setEligibleChurchMembers(eligible);

        const vlist = await apiFetch<EventVolunteerListResponse>(`/api/v1/events/${eventId}/volunteers`, {
          method: "GET",
          token,
        });
        setVolunteerAssignments(vlist.items);
        const vroles = await apiFetch<VolunteerRoleListResponse>(
          `/api/v1/volunteers/roles?for_event_id=${encodeURIComponent(eventId)}&is_active=true&page=1&page_size=100`,
          { method: "GET", token },
        );
        setVolunteerRolesForEvent(vroles.items);
        const notesInit: Record<string, string> = {};
        vlist.items.forEach((r) => {
          notesInit[r.id] = r.notes ?? "";
        });
        setVolNotesDraft(notesInit);

        const rem = await apiFetch<EventReminderRuleListResponse>(`/api/v1/events/${eventId}/reminders`, {
          method: "GET",
          token,
        });
        setReminderRules(rem.items);
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
        const myv = await apiFetch<MyEventVolunteerAssignmentsResponse>(
          `/api/v1/events/${eventId}/volunteers/me`,
          { method: "GET", token },
        );
        setMyVolunteers(myv.items);
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

    const hadRecord = Boolean(attendanceByUserId[userId]);
    const previousStatus = attendanceByUserId[userId];

    setAttendanceByUserId((prev) => ({ ...prev, [userId]: nextStatus }));
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
      setAttendanceByUserId((prev) => {
        const next = { ...prev };
        if (previousStatus === undefined) delete next[userId];
        else next[userId] = previousStatus;
        return next;
      });
      setAttendanceRowPhase((prev) => ({ ...prev, [userId]: "error" }));
      setAttendanceRowError((prev) => ({ ...prev, [userId]: toErrorMessage(err) }));
    }
  }

  function volunteerAssignFailureMessage(err: unknown): string {
    if (isConflictError(err)) {
      const d = getApiErrorDetail(err);
      if (d?.toLowerCase().includes("already")) return d;
      return "This member is already assigned to this role for this event.";
    }
    return toErrorMessage(err);
  }

  async function onAssignVolunteer(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !detail || !("event_id" in detail) || !detail.is_active) return;
    if (!volNewUserId || !volNewRoleId) {
      setVolunteerSectionError("Choose a user and a volunteer role.");
      return;
    }
    setVolAssigning(true);
    setVolunteerSectionError(null);
    try {
      await apiFetch<VolunteerAssignmentRow>(`/api/v1/events/${eventId}/volunteers`, {
        method: "POST",
        token,
        body: {
          user_id: volNewUserId,
          role_id: volNewRoleId,
          notes: volNewNotes.trim() || null,
        },
      });
      setVolNewUserId("");
      setVolNewRoleId("");
      setVolNewNotes("");
      const vlist = await apiFetch<EventVolunteerListResponse>(`/api/v1/events/${eventId}/volunteers`, {
        method: "GET",
        token,
      });
      setVolunteerAssignments(vlist.items);
      const nd: Record<string, string> = {};
      vlist.items.forEach((r) => {
        nd[r.id] = r.notes ?? "";
      });
      setVolNotesDraft(nd);
    } catch (err) {
      setVolunteerSectionError(volunteerAssignFailureMessage(err));
    } finally {
      setVolAssigning(false);
    }
  }

  async function onPatchVolunteerRole(assignmentId: string, roleId: string) {
    if (!token || !isAdmin || !detail || !("event_id" in detail)) return;
    setVolunteerSectionError(null);
    try {
      const updated = await apiFetch<VolunteerAssignmentRow>(
        `/api/v1/events/${eventId}/volunteers/${assignmentId}`,
        { method: "PATCH", token, body: { role_id: roleId } },
      );
      setVolunteerAssignments((prev) => prev.map((r) => (r.id === assignmentId ? updated : r)));
    } catch (err) {
      setVolunteerSectionError(toErrorMessage(err));
    }
  }

  async function onSaveVolunteerNotes(assignmentId: string) {
    if (!token || !isAdmin || !detail || !("event_id" in detail)) return;
    setVolunteerSectionError(null);
    setVolNotesPhase((prev) => ({ ...prev, [assignmentId]: "saving" }));
    setVolNotesError((prev) => {
      const next = { ...prev };
      delete next[assignmentId];
      return next;
    });
    try {
      const updated = await apiFetch<VolunteerAssignmentRow>(
        `/api/v1/events/${eventId}/volunteers/${assignmentId}`,
        {
          method: "PATCH",
          token,
          body: { notes: volNotesDraft[assignmentId]?.trim() || null },
        },
      );
      setVolunteerAssignments((prev) => prev.map((r) => (r.id === assignmentId ? updated : r)));
      setVolNotesDraft((prev) => ({ ...prev, [assignmentId]: updated.notes ?? "" }));
      setVolNotesPhase((prev) => ({ ...prev, [assignmentId]: "saved" }));
      window.setTimeout(() => {
        setVolNotesPhase((prev) =>
          prev[assignmentId] === "saved" ? { ...prev, [assignmentId]: "idle" } : prev,
        );
      }, 2000);
    } catch (err) {
      setVolNotesPhase((prev) => ({ ...prev, [assignmentId]: "error" }));
      setVolNotesError((prev) => ({ ...prev, [assignmentId]: toErrorMessage(err) }));
    }
  }

  async function onRemoveVolunteer(assignmentId: string) {
    if (!token || !isAdmin) return;
    if (
      !window.confirm(
        "Remove this volunteer assignment from the event? This cannot be undone from the calendar.",
      )
    ) {
      return;
    }
    setVolunteerSectionError(null);
    try {
      await apiFetch(`/api/v1/events/${eventId}/volunteers/${assignmentId}`, {
        method: "DELETE",
        token,
      });
      setVolunteerAssignments((prev) => prev.filter((r) => r.id !== assignmentId));
      setVolNotesDraft((prev) => {
        const next = { ...prev };
        delete next[assignmentId];
        return next;
      });
      setVolNotesPhase((prev) => {
        const next = { ...prev };
        delete next[assignmentId];
        return next;
      });
      setVolNotesError((prev) => {
        const next = { ...prev };
        delete next[assignmentId];
        return next;
      });
    } catch (err) {
      setVolunteerSectionError(toErrorMessage(err));
    }
  }

  async function onCreateReminder(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !detail || !("event_id" in detail)) return;
    if (!remInApp && !remSms && !remWa) {
      setReminderSectionError("Select at least one channel.");
      return;
    }
    const offset =
      remOffsetChoice === "custom"
        ? Number.parseInt(remCustomOffset, 10)
        : Number.parseInt(remOffsetChoice, 10);
    if (!Number.isFinite(offset) || offset <= 0) {
      setReminderSectionError("Enter a valid offset in minutes.");
      return;
    }
    if (reminderAudience === "ministry_members" && !detail.ministry_id) {
      setReminderSectionError("Link this event to a ministry first, or choose event volunteers.");
      return;
    }
    const channels: NotificationChannel[] = [];
    if (remInApp) channels.push("in_app");
    if (remSms) channels.push("sms");
    if (remWa) channels.push("whatsapp");
    setReminderSaving(true);
    setReminderSectionError(null);
    try {
      const body: EventReminderRuleCreate = {
        audience_type: reminderAudience,
        channels,
        offset_minutes_before: offset,
      };
      await apiFetch(`/api/v1/events/${eventId}/reminders`, {
        method: "POST",
        token,
        body,
      });
      const rem = await apiFetch<EventReminderRuleListResponse>(`/api/v1/events/${eventId}/reminders`, {
        method: "GET",
        token,
      });
      setReminderRules(rem.items);
    } catch (err) {
      setReminderSectionError(toErrorMessage(err));
    } finally {
      setReminderSaving(false);
    }
  }

  async function onToggleReminderActive(r: EventReminderRuleResponse) {
    if (!token || !isAdmin) return;
    setReminderSectionError(null);
    try {
      await apiFetch(`/api/v1/events/${eventId}/reminders/${r.id}`, {
        method: "PATCH",
        token,
        body: { is_active: !r.is_active },
      });
      const rem = await apiFetch<EventReminderRuleListResponse>(`/api/v1/events/${eventId}/reminders`, {
        method: "GET",
        token,
      });
      setReminderRules(rem.items);
    } catch (err) {
      setReminderSectionError(toErrorMessage(err));
    }
  }

  async function onDeleteReminderRule(ruleId: string) {
    if (!token || !isAdmin) return;
    if (!window.confirm("Delete this reminder rule?")) return;
    setReminderSectionError(null);
    try {
      await apiFetch(`/api/v1/events/${eventId}/reminders/${ruleId}`, { method: "DELETE", token });
      setReminderRules((prev) => prev.filter((x) => x.id !== ruleId));
    } catch (err) {
      setReminderSectionError(toErrorMessage(err));
    }
  }

  async function onRunDueRemindersHere() {
    if (!token || !isAdmin) return;
    setRunDueBusy(true);
    setRunDueSummary(null);
    setReminderSectionError(null);
    try {
      const res = await apiFetch<RunDueRemindersResponse>("/api/v1/notifications/jobs/run-reminders", {
        method: "POST",
        token,
      });
      setRunDueSummary(res);
      const rem = await apiFetch<EventReminderRuleListResponse>(`/api/v1/events/${eventId}/reminders`, {
        method: "GET",
        token,
      });
      setReminderRules(rem.items);
      window.dispatchEvent(new Event("notifications:updated"));
    } catch (err) {
      setReminderSectionError(toErrorMessage(err));
    } finally {
      setRunDueBusy(false);
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
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
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
      <div className="space-y-8">
        <div>
          <Link
            href="/events"
            className="text-sm font-medium text-indigo-800 underline-offset-2 hover:text-indigo-950 hover:underline"
          >
            ← All events
          </Link>
        </div>

        {isAdmin ? (
          <>
          <ContentCard className="space-y-5">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="shepherd-section-title">Edit event</h2>
              <p className="mt-2 text-sm text-slate-600">Update when, where, and how this event appears.</p>
            </div>
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

              {error ? <div className={surfaceError}>{error}</div> : null}

              <div className="flex flex-wrap gap-3">
                <button type="submit" className={btnPrimary}>
                  Save
                </button>
                <button type="button" onClick={onDeactivate} className={btnSecondary}>
                  Deactivate
                </button>
              </div>
            </form>
          </ContentCard>

          <ContentCard className="space-y-5">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="shepherd-section-title">Volunteer scheduling</h2>
              <p className="mt-2 text-sm text-slate-600">Assign roles and track who is serving at this event.</p>
            </div>
            {volunteerSectionError ? <div className={surfaceError}>{volunteerSectionError}</div> : null}
            {!detail.is_active ? (
              <p className="text-sm text-amber-800">Event is inactive. You cannot add new volunteer assignments.</p>
            ) : null}
            <p className="text-xs text-slate-600">
              Roles must fit the event: church-wide roles work everywhere; ministry-scoped roles only on events for that
              ministry. For ministry events, only active members of that ministry can be assigned.
            </p>

            <form
              onSubmit={onAssignVolunteer}
              className="space-y-3 rounded-xl border border-slate-200/80 bg-stone-50/50 p-4 ring-1 ring-slate-900/[0.02]"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Add assignment</p>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">App user</label>
                  <select
                    value={volNewUserId}
                    onChange={(e) => {
                      setVolNewUserId(e.target.value);
                      setVolunteerSectionError(null);
                    }}
                    className={inputCls}
                    disabled={!detail.is_active}
                  >
                    <option value="">Select user</option>
                    {eligibleChurchMembers.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name}
                        {u.email ? ` (${u.email})` : u.phone ? ` (${u.phone})` : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">Role</label>
                  <select
                    value={volNewRoleId}
                    onChange={(e) => {
                      setVolNewRoleId(e.target.value);
                      setVolunteerSectionError(null);
                    }}
                    className={inputCls}
                    disabled={!detail.is_active}
                  >
                    <option value="">Select role</option>
                    {volunteerRolesForEvent.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                        {r.ministry_name ? ` (${r.ministry_name})` : ""}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700">Notes (optional)</label>
                <input
                  value={volNewNotes}
                  onChange={(e) => {
                    setVolNewNotes(e.target.value);
                    setVolunteerSectionError(null);
                  }}
                  className={inputCls}
                  placeholder="e.g. Door A, 9:30 arrival"
                  disabled={!detail.is_active}
                />
              </div>
              <button
                type="submit"
                disabled={!detail.is_active || volAssigning || !volNewUserId || !volNewRoleId}
                className={btnPrimarySm}
              >
                {volAssigning ? "Assigning…" : "Assign volunteer"}
              </button>
            </form>

            {volunteerAssignments.length === 0 ? (
              <p className="text-sm text-slate-600">No volunteer assignments yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-100 bg-white text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-3 py-2">Volunteer</th>
                      <th className="px-3 py-2">Role</th>
                      <th className="px-3 py-2">Notes</th>
                      <th className="px-3 py-2"> </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {volunteerAssignments.map((row) => {
                      const nPhase = volNotesPhase[row.id] ?? "idle";
                      const nErr = volNotesError[row.id];
                      return (
                      <tr key={row.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium text-slate-900">{row.user_full_name}</div>
                          <div className="text-xs text-slate-600">{row.user_email}</div>
                        </td>
                        <td className="px-3 py-2 align-top">
                          <select
                            value={row.role_id}
                            onChange={(e) => {
                              void onPatchVolunteerRole(row.id, e.target.value);
                            }}
                            className={inputCls}
                          >
                            {volunteerRolesForEvent.map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.name}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-3 py-2 align-top">
                          <input
                            value={volNotesDraft[row.id] ?? ""}
                            onChange={(e) => {
                              setVolNotesDraft((prev) => ({ ...prev, [row.id]: e.target.value }));
                              if (nPhase === "error") {
                                setVolNotesPhase((prev) => ({ ...prev, [row.id]: "idle" }));
                                setVolNotesError((prev) => {
                                  const next = { ...prev };
                                  delete next[row.id];
                                  return next;
                                });
                              }
                            }}
                            className={inputCls}
                            placeholder="Notes"
                            disabled={nPhase === "saving"}
                          />
                          <button
                            type="button"
                            onClick={() => void onSaveVolunteerNotes(row.id)}
                            disabled={nPhase === "saving"}
                            className={btnSecondarySm + " mt-1"}
                          >
                            {nPhase === "saving" ? "Saving…" : "Save notes"}
                          </button>
                          {nPhase === "saved" ? (
                            <p className="mt-1 text-xs text-green-800">Saved</p>
                          ) : null}
                          {nPhase === "error" && nErr ? (
                            <p className="mt-1 text-xs text-red-800">{nErr}</p>
                          ) : null}
                        </td>
                        <td className="px-3 py-2 align-top">
                          <button
                            type="button"
                            onClick={() => void onRemoveVolunteer(row.id)}
                            className={btnDangerSm}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </ContentCard>

          <ContentCard className="space-y-5">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="shepherd-section-title">Event reminders</h2>
              <div className="mt-2 space-y-2 text-sm text-slate-600">
                <p>Set up automatic messages to be sent before this event starts.</p>
                <p>Choose when to send them and how they should be delivered.</p>
                <p>
                  Use &quot;Run due reminders now&quot; to send any reminders that are currently due.
                </p>
              </div>
            </div>
            {reminderSectionError ? <div className={surfaceError}>{reminderSectionError}</div> : null}

            <form
              onSubmit={onCreateReminder}
              className="space-y-3 rounded-xl border border-slate-200/80 bg-stone-50/50 p-4 ring-1 ring-slate-900/[0.02]"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">New reminder</p>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">Audience</label>
                  <select
                    value={reminderAudience}
                    onChange={(e) => setReminderAudience(e.target.value as EventReminderAudienceType)}
                    className={inputCls}
                    disabled={!detail.is_active}
                  >
                    <option value="event_volunteers">Event volunteers</option>
                    <option value="ministry_members" disabled={!detail.ministry_id}>
                      Ministry members (linked ministry)
                    </option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">Send before start</label>
                  <select
                    value={remOffsetChoice}
                    onChange={(e) => setRemOffsetChoice(e.target.value)}
                    className={inputCls}
                    disabled={!detail.is_active}
                  >
                    <option value="60">1 hour</option>
                    <option value="1440">24 hours</option>
                    <option value="10080">7 days</option>
                    <option value="custom">Custom (minutes)</option>
                  </select>
                  {remOffsetChoice === "custom" ? (
                    <input
                      type="number"
                      min={1}
                      value={remCustomOffset}
                      onChange={(e) => setRemCustomOffset(e.target.value)}
                      className={inputCls + " mt-1"}
                      disabled={!detail.is_active}
                    />
                  ) : null}
                </div>
              </div>
              <fieldset className="flex flex-wrap gap-3 text-sm text-slate-800">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={remInApp}
                    onChange={(e) => setRemInApp(e.target.checked)}
                    className="rounded border-slate-300"
                    disabled={!detail.is_active}
                  />
                  In-app
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={remSms}
                    onChange={(e) => setRemSms(e.target.checked)}
                    className="rounded border-slate-300"
                    disabled={!detail.is_active}
                  />
                  SMS
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={remWa}
                    onChange={(e) => setRemWa(e.target.checked)}
                    className="rounded border-slate-300"
                    disabled={!detail.is_active}
                  />
                  WhatsApp
                </label>
              </fieldset>
              <button type="submit" disabled={!detail.is_active || reminderSaving} className={btnPrimarySm}>
                {reminderSaving ? "Saving…" : "Add reminder"}
              </button>
            </form>

            {reminderRules.length === 0 ? (
              <p className="text-sm text-slate-600">No reminder rules yet.</p>
            ) : (
              <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
                {reminderRules.map((r) => (
                  <li key={r.id} className="flex flex-wrap items-start justify-between gap-2 px-3 py-3 text-sm">
                    <div>
                      <p className="font-medium text-slate-900">
                        {r.audience_type === "event_volunteers" ? "Event volunteers" : "Ministry members"} ·{" "}
                        {formatReminderOffset(r.offset_minutes_before)}
                      </p>
                      <p className="mt-1 text-xs text-slate-600">
                        Channels: {r.channels.join(", ")} · {r.is_active ? "Active" : "Inactive"}
                        {r.last_run_at ? ` · Last run ${formatDateTime(r.last_run_at)}` : ""}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" onClick={() => void onToggleReminderActive(r)} className={btnSecondarySm}>
                        {r.is_active ? "Deactivate" : "Activate"}
                      </button>
                      <button type="button" onClick={() => void onDeleteReminderRule(r.id)} className={btnDangerSm}>
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
              <button type="button" onClick={() => void onRunDueRemindersHere()} disabled={runDueBusy} className={btnSecondary}>
                {runDueBusy ? "Running…" : "Run due reminders now"}
              </button>
            </div>
            {runDueSummary ? (
              <div className={surfaceInfo + " text-sm"}>
                Reminders sent: {runDueSummary.reminders_sent} · Not due yet: {runDueSummary.skipped_not_due} ·
                Already sent: {runDueSummary.skipped_already_sent} · Couldn&apos;t send:{" "}
                {runDueSummary.skipped_invalid + runDueSummary.failed}
                {runDueSummary.failure_messages.length > 0 ? (
                  <ul className="mt-2 list-inside list-disc text-red-800">
                    {runDueSummary.failure_messages.slice(0, 6).map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </ContentCard>

          <ContentCard className="space-y-5 border-t-2 border-indigo-100 pt-1">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="shepherd-section-title">Attendance</h2>
              <p className="mt-2 text-sm text-slate-600">Record who was present after or during the event.</p>
            </div>
            {!detail.is_active ? (
              <p className="text-sm text-amber-800">
                Event is inactive. Attendance recording is disabled.
              </p>
            ) : null}
            {eligibleChurchMembers.length === 0 ? (
              <p className="text-sm text-slate-600">No eligible app users for this event.</p>
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
                    {eligibleChurchMembers.map((u) => {
                      const persisted = attendanceByUserId[u.id];
                      const selectValue = persisted ?? "";
                      const phase = attendanceRowPhase[u.id] ?? "idle";
                      const rowErr = attendanceRowError[u.id];
                      return (
                        <tr key={u.id}>
                          <td className="px-3 py-2">{u.full_name}</td>
                          <td className="px-3 py-2 text-slate-700">{u.email ?? "—"}</td>
                          <td className="px-3 py-2 align-top">
                            <select
                              value={selectValue}
                              onChange={(e) => {
                                void onAttendanceStatusChange(u.id, e.target.value);
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
          <ContentCard className="space-y-4">
            <p className="text-base text-slate-800">
              {formatDateTime(detail.start_at)} → {formatDateTime(detail.end_at)}
            </p>
            <p className="text-base text-slate-800">
              Location: {detail.location}
            </p>
            <p className="text-base text-slate-800">
              Scope: {ministryLabel}
            </p>
            <p className="text-sm text-slate-500">
              Type: {detail.event_type} · Visibility: {detail.visibility}
            </p>
            {detail.description ? <p className="text-base leading-relaxed text-slate-700">{detail.description}</p> : null}
            <div className={surfaceInfo}>
              Your attendance:{" "}
              <span className="font-semibold capitalize text-slate-900">
                {myAttendance?.recorded ? myAttendance.status : "Not recorded"}
              </span>
            </div>
            {myVolunteers.length > 0 ? (
              <div className={surfaceInfo}>
                <p className="font-semibold text-slate-900">Your volunteer role(s)</p>
                <ul className="mt-2 list-inside list-disc space-y-1 text-slate-800">
                  {myVolunteers.map((v) => (
                    <li key={v.id}>
                      <span className="font-medium">{v.role_name}</span>
                      {v.notes ? <span className="text-slate-600"> — {v.notes}</span> : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm text-slate-600">You have no volunteer assignment for this event.</p>
            )}
          </ContentCard>
        )}
      </div>
    </PageShell>
  );
}

