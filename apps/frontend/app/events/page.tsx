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
  EventListItem,
  EventListResponse,
  EventType,
  EventVisibility,
  MyEventsResponse,
  MinistryListResponse,
} from "lib/types";

import PageShell, { ContentCard } from "components/layout/PageShell";
import CollapsibleSection from "components/layout/CollapsibleSection";
import { btnPrimary, fieldInput, fieldLabel, surfaceError } from "lib/ui";

const inputCls = fieldInput;

function toIsoFromDatetimeLocal(v: string) {
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d.toISOString();
}

function formatDateTime(v: string) {
  const d = new Date(v);
  if (isNaN(d.getTime())) return v;
  return d.toLocaleString();
}

const EVENT_TYPES: EventType[] = ["service", "meeting", "rehearsal", "retreat", "conference", "other"];
const EVENT_VISIBILITIES: EventVisibility[] = ["public", "internal"];

export default function EventsPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [items, setItems] = useState<EventListItem[]>([]);

  // Admin list filters
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState<EventType | "all">("all");
  const [activeOnly, setActiveOnly] = useState(true);
  const [ministryId, setMinistryId] = useState<string>("all");
  const [ministries, setMinistries] = useState<MinistryListResponse["items"]>([]);

  // Admin pagination
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  // Admin create form
  const [creating, setCreating] = useState(false);
  const [cTitle, setCTitle] = useState("");
  const [cDesc, setCDesc] = useState("");
  const [cType, setCType] = useState<EventType>("service");
  const [cVisibility, setCVisibility] = useState<EventVisibility>("public");
  const [cLocation, setCLocation] = useState("");
  const [cMinistryId, setCMinistryId] = useState<string>("none");
  const [cIsActive, setCIsActive] = useState(true);
  const [cStartAt, setCStartAt] = useState("");
  const [cEndAt, setCEndAt] = useState("");

  const totalPages = Math.ceil(total / pageSize);
  const hasNextPage = page < totalPages;

  const load = useCallback(async () => {
    if (!token || status !== "authenticated") {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      if (isAdmin) {
        const mins = await apiFetch<MinistryListResponse>(
          "/api/v1/ministries/?is_active=true",
          { method: "GET", token },
        );
        setMinistries(mins.items);

        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        if (activeOnly !== null) params.set("is_active", activeOnly ? "true" : "false");
        if (search.trim()) params.set("search", search.trim());
        if (eventType !== "all") params.set("event_type", eventType);
        if (ministryId !== "all") params.set("ministry_id", ministryId);

        const res = await apiFetch<EventListResponse>(`/api/v1/events/?${params}`, {
          method: "GET",
          token,
        });
        setItems(res.items);
        setTotal(res.total);
      } else {
        const res = await apiFetch<MyEventsResponse>("/api/v1/events/me", {
          method: "GET",
          token,
        });
        setItems(res.items);
        setTotal(res.items.length);
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
    } finally {
      setLoading(false);
    }
  }, [token, status, isAdmin, router, page, pageSize, activeOnly, search, eventType, ministryId]);

  useEffect(() => {
    if (status === "loading") return;
    void load();
  }, [load, status]);

  useEffect(() => {
    if (!isAdmin) return;
    setPage(1);
  }, [search, eventType, activeOnly, ministryId, isAdmin]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    void load();
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!token) return;

    const startIso = toIsoFromDatetimeLocal(cStartAt);
    const endIso = toIsoFromDatetimeLocal(cEndAt);
    if (!cTitle.trim() || !startIso || !endIso || !cLocation.trim()) {
      setError("Please fill title, start/end date, and location.");
      return;
    }

    setCreating(true);
    setError(null);
    try {
      await apiFetch("/api/v1/events/", {
        method: "POST",
        token,
        body: {
          title: cTitle.trim(),
          description: cDesc.trim() || null,
          event_type: cType,
          start_at: startIso,
          end_at: endIso,
          location: cLocation.trim(),
          is_active: cIsActive,
          visibility: cVisibility,
          ministry_id: cMinistryId === "none" ? null : cMinistryId,
        },
      });
      setCTitle("");
      setCDesc("");
      setCLocation("");
      setCMinistryId("none");
      setCVisibility("public");
      setCIsActive(true);
      setCStartAt("");
      setCEndAt("");
      setPage(1);
      await load();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  const AdminControls = (
    <>
      <CollapsibleSection
        title="Create event"
        defaultOpen
        description="Add a new event to the calendar. Ministry-linked events are scoped to that ministry."
        className="space-y-3"
      >
        <form onSubmit={onCreate} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor="ev-title" className={fieldLabel}>
                Title
              </label>
              <input id="ev-title" value={cTitle} onChange={(e) => setCTitle(e.target.value)} className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="ev-type" className={fieldLabel}>
                Type
              </label>
              <select id="ev-type" value={cType} onChange={(e) => setCType(e.target.value as EventType)} className={inputCls}>
                {EVENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="ev-desc" className={fieldLabel}>
              Description <span className="font-normal text-slate-500">(optional)</span>
            </label>
            <textarea id="ev-desc" value={cDesc} onChange={(e) => setCDesc(e.target.value)} className={`${inputCls} min-h-[88px] resize-y`} />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor="ev-start" className={fieldLabel}>
                Start
              </label>
              <input id="ev-start" type="datetime-local" value={cStartAt} onChange={(e) => setCStartAt(e.target.value)} className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="ev-end" className={fieldLabel}>
                End
              </label>
              <input id="ev-end" type="datetime-local" value={cEndAt} onChange={(e) => setCEndAt(e.target.value)} className={inputCls} />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor="ev-loc" className={fieldLabel}>
                Location
              </label>
              <input id="ev-loc" value={cLocation} onChange={(e) => setCLocation(e.target.value)} className={inputCls} />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="ev-visibility" className={fieldLabel}>
                Visibility
              </label>
              <select id="ev-visibility" value={cVisibility} onChange={(e) => setCVisibility(e.target.value as EventVisibility)} className={inputCls}>
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
              <label htmlFor="ev-ministry" className={fieldLabel}>
                Ministry (optional)
              </label>
              <select id="ev-ministry" value={cMinistryId} onChange={(e) => setCMinistryId(e.target.value)} className={inputCls}>
                <option value="none">Church-wide</option>
                {ministries.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 pt-6 md:pt-0">
              <input
                type="checkbox"
                checked={cIsActive}
                onChange={(e) => setCIsActive(e.target.checked)}
                className="rounded border-slate-300"
              />
              <span className="text-sm font-semibold text-slate-900">Active</span>
            </label>
          </div>

          <button type="submit" disabled={creating} className={btnPrimary}>
            {creating ? "Creating…" : "Create event"}
          </button>
        </form>
      </CollapsibleSection>

      <CollapsibleSection
        title="Search & filter"
        defaultOpen
        description="Narrow the list below, then open an event for details."
      >
        <form onSubmit={onSearch} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1 space-y-1.5">
            <label htmlFor="ev-search" className={fieldLabel}>
              Search
            </label>
            <input id="ev-search" value={search} onChange={(e) => setSearch(e.target.value)} className={inputCls} placeholder="Title contains…" />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="ev-type-filter" className={fieldLabel}>
              Event type
            </label>
            <select id="ev-type-filter" value={eventType} onChange={(e) => setEventType(e.target.value as EventType | "all")} className={inputCls}>
              <option value="all">Any</option>
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label htmlFor="ev-ministry-filter" className={fieldLabel}>
              Ministry
            </label>
            <select id="ev-ministry-filter" value={ministryId} onChange={(e) => setMinistryId(e.target.value)} className={inputCls}>
              <option value="all">Any</option>
              {ministries.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 pt-6 md:pt-0">
            <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
            Active only
          </label>
          <button type="submit" className={btnPrimary}>
            Search
          </button>
        </form>
      </CollapsibleSection>
    </>
  );

  return (
    <PageShell
      title="Events"
      description={
        isAdmin
          ? "Manage and publish church events. Ministry-linked events are only visible to members in that ministry."
          : "Active events you can access."
      }
    >
      <div className="space-y-4">
        {error ? <div className={surfaceError}>{error}</div> : null}

        {status === "loading" || loading ? (
          <ContentCard>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
              Loading events…
            </div>
          </ContentCard>
        ) : null}

        {isAdmin ? (
          <>{AdminControls}</>
        ) : (
          <CollapsibleSection title="Events" defaultOpen description="Active events you can access.">
            {items.length === 0 ? (
              <p className="text-sm text-slate-600">No active events for you yet.</p>
            ) : (
              <div className="space-y-3">
                {items.map((e) => (
                  <div key={e.event_id} className="rounded-lg border border-slate-200 p-4">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="font-semibold text-slate-900">{e.title}</p>
                        <p className="text-xs text-slate-500">
                          {e.event_type} · {formatDateTime(e.start_at)}
                        </p>
                        <p className="mt-1 text-sm text-slate-700">
                          {e.location} · {e.ministry_name ?? "Church-wide"}
                        </p>
                      </div>
                      <Link href={`/events/${e.event_id}`} className="text-sm font-medium text-slate-700 hover:text-slate-900">
                        View →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CollapsibleSection>
        )}

        {isAdmin ? (
          <CollapsibleSection title="Events" defaultOpen>
          <div className="-mx-6 -mb-6 -mt-1 overflow-hidden">
            <div className="border-b border-slate-100 bg-slate-50/80 px-4 py-3">
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{total}</span> event{total === 1 ? "" : "s"}
              </p>
            </div>
            <div className="divide-y divide-slate-100 bg-white">
              {items.map((e) => (
                <div key={e.event_id} className="px-4 py-4">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{e.title}</p>
                      <p className="text-xs text-slate-500">
                        {e.event_type} · {formatDateTime(e.start_at)} → {formatDateTime(e.end_at)}
                      </p>
                      <p className="mt-1 text-sm text-slate-700">
                        {e.location} · {e.ministry_name ?? "Church-wide"}
                      </p>
                    </div>
                    <Link href={`/events/${e.event_id}`} className="shrink-0 text-sm font-medium text-slate-700 hover:text-slate-900">
                      Open →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-3 border-t border-slate-100 bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-600">
                Page <span className="font-semibold text-slate-900">{page}</span>
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasNextPage}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
          </CollapsibleSection>
        ) : null}
      </div>
    </PageShell>
  );
}

