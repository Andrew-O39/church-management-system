"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import PageShell, { ContentCard } from "components/layout/PageShell";
import CollapsibleSection from "components/layout/CollapsibleSection";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch, apiFetchBlob } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import type {
  EventListItem,
  EventListResponse,
  MinistryListResponse,
  UserRole,
} from "lib/types";
import {
  btnPrimary,
  btnSecondary,
  fieldInput,
  fieldLabel,
  surfaceError,
  surfaceInfo,
} from "lib/ui";

type ExportKind = "attendance" | "volunteers" | "users";

/** Stable across SSR and client hydration — do not vary by auth/loading state. */
const EXPORTS_PAGE_TITLE = "Exports";
const EXPORTS_PAGE_DESCRIPTION = "Admin tools for CSV downloads and printable lists.";

const FILENAME_FALLBACK: Record<ExportKind, string> = {
  attendance: "attendance-export.csv",
  volunteers: "volunteers-export.csv",
  users: "app-users-export.csv",
};

function buildPrintHref(kind: ExportKind, params: Record<string, string>): string {
  const qs = new URLSearchParams();
  qs.set("kind", kind);
  for (const [k, v] of Object.entries(params)) {
    if (v) qs.set(k, v);
  }
  return `/exports/print?${qs.toString()}`;
}

/** Label for `<option>` — UUID only in `value`, not in visible text. */
function formatEventOptionLabel(ev: EventListItem): string {
  const d = new Date(ev.start_at);
  const when = isNaN(d.getTime())
    ? ev.start_at
    : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  const ministry = ev.ministry_name ? ` · ${ev.ministry_name}` : "";
  return `${ev.title} — ${when}${ministry}`;
}

const EVENTS_PAGE_SIZE = 100;

async function fetchRecentEventsForExport(token: string): Promise<{
  items: EventListItem[];
  total: number;
}> {
  const head = await apiFetch<EventListResponse>("/api/v1/events/?page=1&page_size=1", {
    method: "GET",
    token,
  });
  const total = head.total;
  const lastPage = Math.max(1, Math.ceil(total / EVENTS_PAGE_SIZE));
  const res = await apiFetch<EventListResponse>(
    `/api/v1/events/?page=${lastPage}&page_size=${EVENTS_PAGE_SIZE}`,
    { method: "GET", token },
  );
  const items = [...res.items].sort(
    (a, b) => new Date(b.start_at).getTime() - new Date(a.start_at).getTime(),
  );
  return { items, total };
}

export default function ExportsPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    setHasHydrated(true);
  }, []);

  const [ministries, setMinistries] = useState<MinistryListResponse["items"]>([]);
  const [events, setEvents] = useState<EventListItem[]>([]);
  const [eventsTotal, setEventsTotal] = useState(0);
  const [actionError, setActionError] = useState<string | null>(null);

  const [att, setAtt] = useState({
    event_id: "",
    date_from: "",
    date_to: "",
    ministry_id: "",
  });
  const [vol, setVol] = useState({
    event_id: "",
    date_from: "",
    date_to: "",
    ministry_id: "",
  });
  const [usr, setUsr] = useState({
    is_active: "",
    role: "" as "" | UserRole,
    ministry_id: "",
  });

  const loadMinistries = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin) return;
    try {
      const res = await apiFetch<MinistryListResponse>(
        "/api/v1/ministries/?page=1&page_size=100&is_active=true",
        { method: "GET", token },
      );
      setMinistries(res.items);
    } catch {
      setMinistries([]);
    }
  }, [token, status, isAdmin]);

  const loadEvents = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin) return;
    try {
      const { items, total } = await fetchRecentEventsForExport(token);
      setEvents(items);
      setEventsTotal(total);
    } catch {
      setEvents([]);
      setEventsTotal(0);
    }
  }, [token, status, isAdmin]);

  useEffect(() => {
    void loadMinistries();
  }, [loadMinistries]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    if (status === "authenticated" && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, isAdmin, router]);

  const downloadCsv = async (kind: ExportKind, params: Record<string, string>) => {
    setActionError(null);
    if (!token) {
      setActionError("Sign in to download exports.");
      return;
    }
    try {
      const { blob, filename } = await apiFetchBlob(`/api/v1/exports/${kind}.csv`, {
        token,
        params,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename ?? FILENAME_FALLBACK[kind];
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      if (isUnauthorized(e)) {
        clearSessionAndRedirect(router);
        return;
      }
      if (isInactiveAccountError(e)) {
        clearSessionAndRedirect(router, "account_inactive");
        return;
      }
      setActionError(toErrorMessage(e));
    }
  };

  const openPrint = (kind: ExportKind, params: Record<string, string>) => {
    setActionError(null);
    const href = buildPrintHref(kind, params);
    window.open(href, "_blank", "noopener,noreferrer");
  };

  const eventSelect = (
    id: string,
    value: string,
    onChange: (v: string) => void,
    options?: { showRecentHint?: boolean },
  ) => (
    <div>
      <label className={fieldLabel} htmlFor={id}>
        Event (optional)
      </label>
      <select
        id={id}
        className={`${fieldInput} mt-1`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All events</option>
        {events.map((ev) => (
          <option key={ev.event_id} value={ev.event_id}>
            {formatEventOptionLabel(ev)}
          </option>
        ))}
      </select>
      {options?.showRecentHint && eventsTotal > EVENTS_PAGE_SIZE ? (
        <p className="mt-1 text-xs text-slate-500">
          Showing the {events.length} most recent events (of {eventsTotal} total). Use date filters
          to export older ranges without selecting an event.
        </p>
      ) : null}
    </div>
  );

  const ministrySelect = (
    id: string,
    value: string,
    onChange: (v: string) => void,
  ) => (
    <div>
      <label className={fieldLabel} htmlFor={id}>
        Ministry (optional)
      </label>
      <select
        id={id}
        className={`${fieldInput} mt-1`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Any ministry</option>
        {ministries.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
          </option>
        ))}
      </select>
    </div>
  );

  if (!hasHydrated) {
    return (
      <PageShell title={EXPORTS_PAGE_TITLE} description={EXPORTS_PAGE_DESCRIPTION}>
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (!token || status === "unauthenticated") {
    return (
      <PageShell title={EXPORTS_PAGE_TITLE} description={EXPORTS_PAGE_DESCRIPTION}>
        <ContentCard>
          <p className="text-slate-600">Sign in to use exports.</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (status === "loading") {
    return (
      <PageShell title={EXPORTS_PAGE_TITLE} description={EXPORTS_PAGE_DESCRIPTION}>
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (!isAdmin) {
    return (
      <PageShell title={EXPORTS_PAGE_TITLE} description={EXPORTS_PAGE_DESCRIPTION}>
        <ContentCard>
          <p className="text-sm text-slate-600">Redirecting…</p>
        </ContentCard>
      </PageShell>
    );
  }

  const attParams: Record<string, string> = {
    ...(att.event_id ? { event_id: att.event_id } : {}),
    ...(att.date_from ? { date_from: att.date_from } : {}),
    ...(att.date_to ? { date_to: att.date_to } : {}),
    ...(att.ministry_id ? { ministry_id: att.ministry_id } : {}),
  };
  const volParams: Record<string, string> = {
    ...(vol.event_id ? { event_id: vol.event_id } : {}),
    ...(vol.date_from ? { date_from: vol.date_from } : {}),
    ...(vol.date_to ? { date_to: vol.date_to } : {}),
    ...(vol.ministry_id ? { ministry_id: vol.ministry_id } : {}),
  };
  const usrParams: Record<string, string> = {
    ...(usr.is_active ? { is_active: usr.is_active } : {}),
    ...(usr.role ? { role: usr.role } : {}),
    ...(usr.ministry_id ? { ministry_id: usr.ministry_id } : {}),
  };

  return (
    <PageShell title={EXPORTS_PAGE_TITLE} description={EXPORTS_PAGE_DESCRIPTION}>
      <div className={surfaceInfo + " mb-6"}>
        <strong>PDF:</strong> there is no server-generated PDF. Open a print view, then use{" "}
        <strong>Print → Save as PDF</strong> in your browser.
        <span className="mt-2 block text-slate-700">
          <strong>Parish registry:</strong> export CSV and print from the{" "}
          <a href="/members" className="font-semibold text-indigo-800 underline">
            Parish registry
          </a>{" "}
          page (filters apply there).
        </span>
      </div>

      {actionError ? <div className={`${surfaceError} mb-6`}>{actionError}</div> : null}

      <div className="space-y-8">
        <CollapsibleSection
          title="Attendance"
          defaultOpen
          description="App-user attendance tied to events. Filter by event, dates, or ministry-linked events."
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              {eventSelect("att-event", att.event_id, (v) => setAtt({ ...att, event_id: v }), {
                showRecentHint: true,
              })}
            </div>
            <div>
              <label className={fieldLabel} htmlFor="att-from">
                From date (optional)
              </label>
              <input
                id="att-from"
                type="date"
                className={`${fieldInput} mt-1`}
                value={att.date_from}
                onChange={(e) => setAtt({ ...att, date_from: e.target.value })}
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="att-to">
                To date (optional)
              </label>
              <input
                id="att-to"
                type="date"
                className={`${fieldInput} mt-1`}
                value={att.date_to}
                onChange={(e) => setAtt({ ...att, date_to: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              {ministrySelect("att-min", att.ministry_id, (v) => setAtt({ ...att, ministry_id: v }))}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              className={btnPrimary}
              onClick={() => void downloadCsv("attendance", attParams)}
            >
              Download CSV
            </button>
            <button
              type="button"
              className={btnSecondary}
              onClick={() => openPrint("attendance", attParams)}
            >
              Open print view
            </button>
          </div>
        </CollapsibleSection>

        <CollapsibleSection
          title="Volunteers"
          defaultOpen={false}
          description="Volunteer assignments per event (app users only)."
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">{eventSelect("vol-event", vol.event_id, (v) => setVol({ ...vol, event_id: v }))}</div>
            <div>
              <label className={fieldLabel} htmlFor="vol-from">
                From date (optional)
              </label>
              <input
                id="vol-from"
                type="date"
                className={`${fieldInput} mt-1`}
                value={vol.date_from}
                onChange={(e) => setVol({ ...vol, date_from: e.target.value })}
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="vol-to">
                To date (optional)
              </label>
              <input
                id="vol-to"
                type="date"
                className={`${fieldInput} mt-1`}
                value={vol.date_to}
                onChange={(e) => setVol({ ...vol, date_to: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              {ministrySelect("vol-min", vol.ministry_id, (v) => setVol({ ...vol, ministry_id: v }))}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              className={btnPrimary}
              onClick={() => void downloadCsv("volunteers", volParams)}
            >
              Download CSV
            </button>
            <button
              type="button"
              className={btnSecondary}
              onClick={() => openPrint("volunteers", volParams)}
            >
              Open print view
            </button>
          </div>
        </CollapsibleSection>

        <CollapsibleSection
          title="App users"
          defaultOpen={false}
          description="Login accounts and profiles—not parish registry records."
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className={fieldLabel} htmlFor="usr-active">
                Account active
              </label>
              <select
                id="usr-active"
                className={`${fieldInput} mt-1`}
                value={usr.is_active}
                onChange={(e) => setUsr({ ...usr, is_active: e.target.value })}
              >
                <option value="">Any</option>
                <option value="true">Active only</option>
                <option value="false">Inactive only</option>
              </select>
            </div>
            <div>
              <label className={fieldLabel} htmlFor="usr-role">
                Role
              </label>
              <select
                id="usr-role"
                className={`${fieldInput} mt-1`}
                value={usr.role}
                onChange={(e) => setUsr({ ...usr, role: e.target.value as "" | UserRole })}
              >
                <option value="">Any</option>
                <option value="admin">Admin</option>
                <option value="group_leader">Group leader</option>
                <option value="member">Member</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              {ministrySelect("usr-min", usr.ministry_id, (v) => setUsr({ ...usr, ministry_id: v }))}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              className={btnPrimary}
              onClick={() => void downloadCsv("users", usrParams)}
            >
              Download CSV
            </button>
            <button
              type="button"
              className={btnSecondary}
              onClick={() => openPrint("users", usrParams)}
            >
              Open print view
            </button>
          </div>
        </CollapsibleSection>
      </div>
    </PageShell>
  );
}
