"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiFetch } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import { useAuth } from "components/providers/AuthProvider";
import type {
  DeliverySummary,
  EventListResponse,
  MinistryListResponse,
  MyNotificationItem,
  MyNotificationsResponse,
  NotificationChannel,
  NotificationCreateRequest,
  NotificationDetailResponse,
  NotificationListResponse,
  NotificationAudienceType,
  NotificationCategory,
  RunDueRemindersResponse,
  UserSearchItem,
  UserSearchResponse,
} from "lib/types";

import PageShell from "components/layout/PageShell";
import CollapsibleSection from "components/layout/CollapsibleSection";
import DeliverySummaryContent from "components/notifications/DeliverySummaryContent";
import {
  btnGhost,
  btnPagination,
  btnPrimary,
  btnSecondary,
  btnSecondarySm,
  fieldInput,
  notificationCategoryClass,
  notificationChannelClass,
  surfaceError,
  surfaceInfo,
  surfaceSuccess,
  surfaceWarning,
} from "lib/ui";

const inputCls = fieldInput;

const CATEGORY_OPTIONS: NotificationCategory[] = [
  "general",
  "event",
  "volunteer",
  "ministry",
  "system",
];

const AUDIENCE_OPTIONS: { value: NotificationAudienceType; label: string }[] = [
  { value: "direct_users", label: "Specific people (search and add)" },
  { value: "ministry_members", label: "Everyone in a ministry" },
  { value: "event_volunteers", label: "Volunteers for an event" },
];

/** Inbox list refresh interval (ms); keep in sync with helper copy below. */
const INBOX_REFRESH_MS = 20_000;

function formatDateTime(v: string | null) {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d.getTime())) return v;
  return d.toLocaleString();
}

function formatRole(role: string) {
  return role.split("_").join(" ");
}

export default function NotificationsPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [inbox, setInbox] = useState<MyNotificationItem[]>([]);
  const [inboxTotal, setInboxTotal] = useState(0);
  const [inboxPage, setInboxPage] = useState(1);
  const inboxPageSize = 20;

  const [sent, setSent] = useState<NotificationListResponse["items"]>([]);
  const [sentTotal, setSentTotal] = useState(0);
  const [sentPage, setSentPage] = useState(1);
  const sentPageSize = 20;

  const [ministries, setMinistries] = useState<MinistryListResponse["items"]>([]);
  const [events, setEvents] = useState<EventListResponse["items"]>([]);

  const [sendTitle, setSendTitle] = useState("");
  const [sendBody, setSendBody] = useState("");
  const [sendCategory, setSendCategory] = useState<NotificationCategory>("general");
  const [audienceType, setAudienceType] = useState<NotificationAudienceType>("direct_users");
  const [ministryId, setMinistryId] = useState("");
  const [eventId, setEventId] = useState("");
  const [sending, setSending] = useState(false);
  const [channelInApp, setChannelInApp] = useState(true);
  const [channelSms, setChannelSms] = useState(false);
  const [channelWhatsapp, setChannelWhatsapp] = useState(false);
  const [lastSendSummary, setLastSendSummary] = useState<DeliverySummary | null>(null);
  const [runDueBusy, setRunDueBusy] = useState(false);
  const [runDueSummary, setRunDueSummary] = useState<RunDueRemindersResponse | null>(null);

  const [userSearchInput, setUserSearchInput] = useState("");
  const [debouncedUserSearch, setDebouncedUserSearch] = useState("");
  const [selectedDirectUsers, setSelectedDirectUsers] = useState<UserSearchItem[]>([]);
  const [searchResults, setSearchResults] = useState<UserSearchItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    const id = window.setTimeout(() => setDebouncedUserSearch(userSearchInput.trim()), 350);
    return () => window.clearTimeout(id);
  }, [userSearchInput]);

  useEffect(() => {
    if (!token || !isAdmin || audienceType !== "direct_users") {
      setSearchResults([]);
      setSearchLoading(false);
      setSearchError(null);
      return;
    }
    if (debouncedUserSearch.length < 2) {
      setSearchResults([]);
      setSearchLoading(false);
      setSearchError(null);
      return;
    }
    let cancelled = false;
    setSearchLoading(true);
    setSearchError(null);
    const params = new URLSearchParams();
    params.set("q", debouncedUserSearch);
    params.set("page", "1");
    params.set("page_size", "20");
    void (async () => {
      try {
        const res = await apiFetch<UserSearchResponse>(`/api/v1/users/search?${params.toString()}`, {
          method: "GET",
          token,
        });
        if (!cancelled) setSearchResults(res.items);
      } catch (e: unknown) {
        if (!cancelled) setSearchError(toErrorMessage(e));
      } finally {
        if (!cancelled) setSearchLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [debouncedUserSearch, token, isAdmin, audienceType]);

  const addDirectUser = (item: UserSearchItem) => {
    setSelectedDirectUsers((prev) => {
      if (prev.some((p) => p.user_id === item.user_id)) return prev;
      return [...prev, item];
    });
  };

  const removeDirectUser = (userId: string) => {
    setSelectedDirectUsers((prev) => prev.filter((p) => p.user_id !== userId));
  };

  const loadInbox = useCallback(async () => {
    if (!token || status !== "authenticated") return;
    const res = await apiFetch<MyNotificationsResponse>(
      `/api/v1/notifications/me?page=${inboxPage}&page_size=${inboxPageSize}`,
      { method: "GET", token },
    );
    setInbox(res.items);
    setInboxTotal(res.total);
  }, [token, status, inboxPage]);

  const loadAdmin = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin) return;
    const [mins, evs, sentRes] = await Promise.all([
      apiFetch<MinistryListResponse>("/api/v1/ministries/?is_active=true&page=1&page_size=100", {
        method: "GET",
        token,
      }),
      apiFetch<EventListResponse>(
        "/api/v1/events/?page=1&page_size=100&is_active=true",
        { method: "GET", token },
      ),
      apiFetch<NotificationListResponse>(
        `/api/v1/notifications/?page=${sentPage}&page_size=${sentPageSize}`,
        { method: "GET", token },
      ),
    ]);
    setMinistries(mins.items);
    setEvents(evs.items);
    setSent(sentRes.items);
    setSentTotal(sentRes.total);
  }, [token, status, isAdmin, sentPage]);

  const load = useCallback(async () => {
    if (!token || status !== "authenticated") {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await loadInbox();
      if (isAdmin) await loadAdmin();
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
  }, [token, status, isAdmin, router, loadInbox, loadAdmin]);

  useEffect(() => {
    void load();
  }, [load]);

  /** Refresh inbox periodically so new messages appear without a full page reload. */
  useEffect(() => {
    if (!token || status !== "authenticated") return;
    const id = window.setInterval(() => {
      void loadInbox().then(() => {
        window.dispatchEvent(new Event("notifications:updated"));
      });
    }, INBOX_REFRESH_MS);
    return () => window.clearInterval(id);
  }, [token, status, loadInbox]);

  const onMarkRead = async (notificationId: string) => {
    if (!token) return;
    try {
      await apiFetch(`/api/v1/notifications/${notificationId}/read`, {
        method: "PATCH",
        token,
      });
      await loadInbox();
      window.dispatchEvent(new Event("notifications:updated"));
    } catch (e: unknown) {
      setError(toErrorMessage(e));
    }
  };

  const onMarkAllRead = async () => {
    if (!token) return;
    try {
      await apiFetch("/api/v1/notifications/read-all", { method: "PATCH", token });
      await loadInbox();
      window.dispatchEvent(new Event("notifications:updated"));
    } catch (e: unknown) {
      setError(toErrorMessage(e));
    }
  };

  const onSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !isAdmin) return;
    const channels: NotificationChannel[] = [];
    if (channelInApp) channels.push("in_app");
    if (channelSms) channels.push("sms");
    if (channelWhatsapp) channels.push("whatsapp");
    if (channels.length === 0) {
      setError("Choose at least one delivery channel.");
      return;
    }
    if (audienceType === "direct_users" && selectedDirectUsers.length === 0) {
      setError("Select at least one person to notify.");
      return;
    }
    setSending(true);
    setError(null);
    setLastSendSummary(null);
    try {
      const base = {
        title: sendTitle.trim(),
        body: sendBody.trim(),
        category: sendCategory,
        channels,
        audience_type: audienceType,
      };

      let req: NotificationCreateRequest;
      if (audienceType === "direct_users") {
        req = { ...base, user_ids: selectedDirectUsers.map((u) => u.user_id) };
      } else if (audienceType === "ministry_members") {
        if (!ministryId) throw new Error("Select a ministry");
        req = { ...base, ministry_id: ministryId };
      } else {
        if (!eventId) throw new Error("Select an event");
        req = { ...base, event_id: eventId };
      }

      const created = await apiFetch<NotificationDetailResponse>("/api/v1/notifications/", {
        method: "POST",
        token,
        body: req,
      });
      if (created.delivery_summary) setLastSendSummary(created.delivery_summary);
      setSendTitle("");
      setSendBody("");
      setSelectedDirectUsers([]);
      setUserSearchInput("");
      await loadAdmin();
      await loadInbox();
      window.dispatchEvent(new Event("notifications:updated"));
    } catch (e: unknown) {
      setError(toErrorMessage(e));
    } finally {
      setSending(false);
    }
  };

  const inboxPages = Math.max(1, Math.ceil(inboxTotal / inboxPageSize));
  const sentPages = Math.max(1, Math.ceil(sentTotal / sentPageSize));

  async function onRunDueReminders() {
    if (!token || !isAdmin) return;
    setRunDueBusy(true);
    setRunDueSummary(null);
    setError(null);
    try {
      const res = await apiFetch<RunDueRemindersResponse>("/api/v1/notifications/jobs/run-reminders", {
        method: "POST",
        token,
      });
      setRunDueSummary(res);
      await loadAdmin();
      await loadInbox();
      window.dispatchEvent(new Event("notifications:updated"));
    } catch (e: unknown) {
      setError(toErrorMessage(e));
    } finally {
      setRunDueBusy(false);
    }
  }

  if (!token || status !== "authenticated") {
    return (
      <PageShell title="Notifications" description="Sign in to view notifications.">
        <p className="text-sm text-slate-600">This page requires a signed-in app user.</p>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Notifications"
      description={
        isAdmin
          ? "Send messages to app users by in-app notification, SMS, or WhatsApp."
          : "Messages sent to your account in the app."
      }
    >
      <div className="space-y-8">
      {error ? <div className={surfaceError}>{error}</div> : null}

      {isAdmin ? (
        <CollapsibleSection
          title="Event reminders"
          defaultOpen={false}
          description="Runs any reminder messages that are currently due (based on the reminders you set up on each
            event). Use this if you want to send them right away instead of waiting for the next automatic run."
          className="space-y-4"
        >
          <button
            type="button"
            onClick={() => void onRunDueReminders()}
            disabled={runDueBusy}
            className={btnSecondary}
          >
            {runDueBusy ? "Running…" : "Run due reminders now"}
          </button>
          {runDueSummary ? (
            <div className={surfaceInfo}>
              <p className="text-sm">
                Reminders sent: {runDueSummary.reminders_sent} · Not due yet: {runDueSummary.skipped_not_due} ·
                Already sent: {runDueSummary.skipped_already_sent} · Couldn&apos;t send:{" "}
                {runDueSummary.skipped_invalid + runDueSummary.failed}
              </p>
              {runDueSummary.failure_messages.length > 0 ? (
                <ul className="mt-3 list-inside list-disc text-sm text-red-800">
                  {runDueSummary.failure_messages.slice(0, 8).map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </CollapsibleSection>
      ) : null}

      {isAdmin ? (
        <CollapsibleSection
          title="Send notification"
          defaultOpen
          description="Messages go to people who use this app. SMS and WhatsApp are sent using the phone number saved on
            each user&apos;s app profile."
          className="space-y-5"
        >
          {lastSendSummary ? (
            <div className={surfaceSuccess}>
              <p className="font-semibold text-slate-900">Delivery summary</p>
              <div className="mt-2 text-emerald-900">
                <DeliverySummaryContent summary={lastSendSummary} compact />
              </div>
            </div>
          ) : null}
          <form className="mt-4 space-y-4" onSubmit={onSend}>
            <div>
              <label className="block text-sm font-medium text-slate-700">Title</label>
              <input
                className={inputCls + " mt-1"}
                value={sendTitle}
                onChange={(e) => setSendTitle(e.target.value)}
                required
                maxLength={500}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Body</label>
              <textarea
                className={inputCls + " mt-1 min-h-[100px]"}
                value={sendBody}
                onChange={(e) => setSendBody(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Category</label>
              <select
                className={inputCls + " mt-1"}
                value={sendCategory}
                onChange={(e) => setSendCategory(e.target.value as NotificationCategory)}
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium text-slate-700">Delivery channels</legend>
              <p className="text-xs text-slate-500">Choose how you want this message delivered. You can select more than one.</p>
              <label className="flex items-center gap-2 text-sm text-slate-800">
                <input
                  type="checkbox"
                  checked={channelInApp}
                  onChange={(e) => setChannelInApp(e.target.checked)}
                  className="rounded border-slate-300"
                />
                In-app (shows in each person&apos;s inbox)
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-800">
                <input
                  type="checkbox"
                  checked={channelSms}
                  onChange={(e) => setChannelSms(e.target.checked)}
                  className="rounded border-slate-300"
                />
                SMS
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-800">
                <input
                  type="checkbox"
                  checked={channelWhatsapp}
                  onChange={(e) => setChannelWhatsapp(e.target.checked)}
                  className="rounded border-slate-300"
                />
                WhatsApp
              </label>
            </fieldset>
            <div>
              <label className="block text-sm font-medium text-slate-700">Audience</label>
              <select
                className={inputCls + " mt-1"}
                value={audienceType}
                onChange={(e) => setAudienceType(e.target.value as NotificationAudienceType)}
              >
                {AUDIENCE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            {audienceType === "direct_users" ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700" htmlFor="user-search">
                    Find people
                  </label>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Search by name, email, or phone number. Enter at least two characters.
                  </p>
                  <input
                    id="user-search"
                    type="search"
                    autoComplete="off"
                    className={inputCls + " mt-1"}
                    value={userSearchInput}
                    onChange={(e) => setUserSearchInput(e.target.value)}
                    placeholder="e.g. Maria or @example.com"
                  />
                </div>
                {searchLoading ? (
                  <p className="text-sm text-slate-500">Searching…</p>
                ) : null}
                {searchError ? (
                  <p className="text-sm text-red-700">{searchError}</p>
                ) : null}
                {!searchLoading &&
                !searchError &&
                audienceType === "direct_users" &&
                debouncedUserSearch.length >= 2 &&
                searchResults.length === 0 ? (
                  <p className="text-sm text-slate-600">No users match that search.</p>
                ) : null}
                {!searchLoading &&
                !searchError &&
                audienceType === "direct_users" &&
                debouncedUserSearch.length < 2 &&
                userSearchInput.trim().length > 0 ? (
                  <p className="text-sm text-slate-500">Keep typing — need at least two characters to search.</p>
                ) : null}
                {searchResults.length > 0 ? (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Results</p>
                    <ul className="mt-1 max-h-56 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200 bg-white">
                      {searchResults.map((u) => {
                        const already = selectedDirectUsers.some((s) => s.user_id === u.user_id);
                        return (
                          <li
                            key={u.user_id}
                            className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
                          >
                            <div className="min-w-0">
                              <div className="font-medium text-slate-900">{u.full_name}</div>
                              <div className="text-xs text-slate-600">
                                {u.email}
                                {u.phone_number ? ` · ${u.phone_number}` : ""} · {formatRole(u.role)}
                              </div>
                            </div>
                            <button
                              type="button"
                              disabled={already}
                              onClick={() => addDirectUser(u)}
                              className="shrink-0 rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {already ? "Added" : "Add"}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ) : null}
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Selected recipients ({selectedDirectUsers.length})
                  </p>
                  {selectedDirectUsers.length === 0 ? (
                    <p className="mt-1 text-sm text-slate-600">No users selected yet.</p>
                  ) : (
                    <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200 bg-slate-50/80">
                      {selectedDirectUsers.map((u) => (
                        <li
                          key={u.user_id}
                          className="flex flex-wrap items-start justify-between gap-2 px-3 py-2 text-sm"
                        >
                          <div className="min-w-0">
                            <div className="font-medium text-slate-900">{u.full_name}</div>
                            <div className="text-xs text-slate-600">
                              {u.email}
                              {u.phone_number ? ` · ${u.phone_number}` : ""} · {formatRole(u.role)}
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeDirectUser(u.user_id)}
                            className="shrink-0 text-xs font-medium text-slate-600 underline hover:text-slate-900"
                          >
                            Remove
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : null}
            {audienceType === "ministry_members" ? (
              <div>
                <label className="block text-sm font-medium text-slate-700">Ministry</label>
                <select
                  className={inputCls + " mt-1"}
                  value={ministryId}
                  onChange={(e) => setMinistryId(e.target.value)}
                  required
                >
                  <option value="">— Select —</option>
                  {ministries.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            {audienceType === "event_volunteers" ? (
              <div>
                <label className="block text-sm font-medium text-slate-700">Event</label>
                <select
                  className={inputCls + " mt-1"}
                  value={eventId}
                  onChange={(e) => setEventId(e.target.value)}
                  required
                >
                  <option value="">— Select —</option>
                  {events.map((ev) => (
                    <option key={ev.event_id} value={ev.event_id}>
                      {ev.title} · {formatDateTime(ev.start_at)}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            {(channelSms || channelWhatsapp) &&
            audienceType === "direct_users" &&
            selectedDirectUsers.some((u) => !u.phone_number?.trim()) ? (
              <p className={surfaceWarning}>
                Some selected people don&apos;t have a phone number on their profile. SMS and WhatsApp can&apos;t
                be sent to them; in-app still works if you turn it on above.
              </p>
            ) : null}
            {(channelSms || channelWhatsapp) && audienceType !== "direct_users" ? (
              <p className={surfaceWarning}>
                SMS and WhatsApp use the phone number saved on each person&apos;s app profile. Anyone without a
                number won&apos;t get those channels—use in-app if everyone should see the message.
              </p>
            ) : null}
            <button
              type="submit"
              disabled={
                sending ||
                (!channelInApp && !channelSms && !channelWhatsapp) ||
                (audienceType === "direct_users" && selectedDirectUsers.length === 0)
              }
              className={btnPrimary}
            >
              {sending ? "Sending…" : "Send notification"}
            </button>
          </form>
        </CollapsibleSection>
      ) : null}

      <CollapsibleSection
        title="Your inbox"
        defaultOpen
        description={`Refreshes about every ${INBOX_REFRESH_MS / 1000} seconds so new messages appear without reloading the page.`}
        className="space-y-5"
      >
        <div className="flex flex-wrap justify-end border-b border-slate-100 pb-4">
          <button type="button" onClick={() => void onMarkAllRead()} className={btnGhost}>
            Mark all read
          </button>
        </div>
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : inbox.length === 0 ? (
          <p className="text-base text-slate-600">No notifications yet.</p>
        ) : (
          <ul className="space-y-3">
            {inbox.map((n) => (
              <li
                key={n.notification_id}
                className="rounded-xl border border-slate-200/90 bg-stone-50/60 p-4 ring-1 ring-slate-900/[0.02]"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-base font-semibold text-slate-900">{n.title}</p>
                    <p className="mt-2 whitespace-pre-wrap text-base leading-relaxed text-slate-700">{n.body}</p>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span className={notificationCategoryClass()}>{n.category}</span>
                      {n.channels.map((c) => (
                        <span key={c} className={notificationChannelClass(c)}>
                          {c}
                        </span>
                      ))}
                      <span className="text-slate-400">·</span>
                      <span>{formatDateTime(n.sent_at ?? n.created_at)}</span>
                      {n.related_event_id ? (
                        <Link
                          href={`/events/${n.related_event_id}`}
                          className="font-medium text-indigo-700 hover:text-indigo-900 hover:underline"
                        >
                          Related event
                        </Link>
                      ) : null}
                      {n.related_ministry_id ? (
                        <Link
                          href={`/ministries/${n.related_ministry_id}`}
                          className="font-medium text-indigo-700 hover:text-indigo-900 hover:underline"
                        >
                          Related ministry
                        </Link>
                      ) : null}
                    </div>
                  </div>
                  <div className="shrink-0">
                    {n.recipient_status === "delivered" ? (
                      <button
                        type="button"
                        onClick={() => void onMarkRead(n.notification_id)}
                        className={btnSecondarySm}
                      >
                        Mark read
                      </button>
                    ) : (
                      <span className="text-xs font-medium text-slate-400">Read</span>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
        {inboxTotal > inboxPageSize ? (
          <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4 text-sm">
            <button
              type="button"
              disabled={inboxPage <= 1}
              onClick={() => setInboxPage((p) => Math.max(1, p - 1))}
              className={btnPagination}
            >
              Previous
            </button>
            <span className="text-slate-600">
              Page {inboxPage} of {inboxPages}
            </span>
            <button
              type="button"
              disabled={inboxPage >= inboxPages}
              onClick={() => setInboxPage((p) => p + 1)}
              className={btnPagination}
            >
              Next
            </button>
          </div>
        ) : null}
      </CollapsibleSection>

      {isAdmin ? (
        <CollapsibleSection title="Sent notifications" defaultOpen={false} className="space-y-4">
          {sent.length === 0 ? (
            <p className="text-base text-slate-600">No notifications sent yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {sent.map((s) => (
                <li key={s.id} className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0">
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-900">{s.title}</p>
                    <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-600">
                      <span className={notificationCategoryClass()}>{s.category}</span>
                      <span className="text-slate-400">·</span>
                      <span>{s.audience_type}</span>
                      <span className="text-slate-400">·</span>
                      <span className="inline-flex flex-wrap gap-1">
                        {s.channels.map((c) => (
                          <span key={c} className={notificationChannelClass(c)}>
                            {c}
                          </span>
                        ))}
                      </span>
                      <span className="text-slate-400">·</span>
                      <span>{s.recipient_count} recipients</span>
                      <span className="text-slate-400">·</span>
                      <span className="text-slate-500">{formatDateTime(s.sent_at ?? s.created_at)}</span>
                    </p>
                  </div>
                  <Link
                    href={`/notifications/${s.id}`}
                    className="shrink-0 text-sm font-semibold text-indigo-700 hover:text-indigo-900 hover:underline"
                  >
                    View
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {sentTotal > sentPageSize ? (
            <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4 text-sm">
              <button
                type="button"
                disabled={sentPage <= 1}
                onClick={() => setSentPage((p) => Math.max(1, p - 1))}
                className={btnPagination}
              >
                Previous
              </button>
              <span className="text-slate-600">
                Page {sentPage} of {sentPages}
              </span>
              <button
                type="button"
                disabled={sentPage >= sentPages}
                onClick={() => setSentPage((p) => p + 1)}
                className={btnPagination}
              >
                Next
              </button>
            </div>
          ) : null}
        </CollapsibleSection>
      ) : null}
      </div>
    </PageShell>
  );
}
