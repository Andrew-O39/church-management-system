"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch, apiFetchBlob } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type {
  ChurchMemberListResponse,
  ChurchMemberStatsResponse,
  ChurchMembershipStatus,
  RegistryAgeGroup,
  RegistrySavedFilterRecord,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import CollapsibleSection from "components/layout/CollapsibleSection";
import { btnPrimary, btnSecondary, fieldInput, fieldLabel, surfaceError, surfaceInfo } from "lib/ui";

const MEMBERSHIP_OPTIONS: { value: "" | ChurchMembershipStatus; label: string }[] = [
  { value: "", label: "Any status" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "visitor", label: "Visitor" },
  { value: "transferred", label: "Transferred" },
  { value: "deceased", label: "Deceased" },
];

const GENDER_OPTIONS = [
  { value: "", label: "Any" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
  { value: "unknown", label: "Unknown" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const AGE_GROUP_OPTIONS: { value: "" | RegistryAgeGroup; label: string }[] = [
  { value: "", label: "Any age band" },
  { value: "child", label: "Child (0–12)" },
  { value: "young_adult", label: "Young adult (13–17)" },
  { value: "adult", label: "Adult (18+)" },
];

type FilterState = {
  search: string;
  membershipStatus: "" | ChurchMembershipStatus;
  filterActive: string;
  filterDeceased: string;
  gender: string;
  isBaptized: string;
  isConfirmed: string;
  isCommunicant: string;
  isMarried: string;
  ageGroup: "" | RegistryAgeGroup;
  joinedFrom: string;
  joinedTo: string;
  deceasedFrom: string;
  deceasedTo: string;
  baptismDateFrom: string;
  baptismDateTo: string;
  firstCommunionDateFrom: string;
  firstCommunionDateTo: string;
  confirmationDateFrom: string;
  confirmationDateTo: string;
  marriageDateFrom: string;
  marriageDateTo: string;
  dobFrom: string;
  dobTo: string;
};

const emptyFilters = (): FilterState => ({
  search: "",
  membershipStatus: "",
  filterActive: "",
  filterDeceased: "",
  gender: "",
  isBaptized: "",
  isConfirmed: "",
  isCommunicant: "",
  isMarried: "",
  ageGroup: "",
  joinedFrom: "",
  joinedTo: "",
  deceasedFrom: "",
  deceasedTo: "",
  baptismDateFrom: "",
  baptismDateTo: "",
  firstCommunionDateFrom: "",
  firstCommunionDateTo: "",
  confirmationDateFrom: "",
  confirmationDateTo: "",
  marriageDateFrom: "",
  marriageDateTo: "",
  dobFrom: "",
  dobTo: "",
});

function triStateParam(v: string): boolean | undefined {
  if (v === "true") return true;
  if (v === "false") return false;
  return undefined;
}

function appendRegistryListParams(p: URLSearchParams, a: FilterState) {
  if (a.search.trim()) p.set("search", a.search.trim());
  if (a.membershipStatus) p.set("membership_status", a.membershipStatus);
  const ia = triStateParam(a.filterActive);
  if (ia !== undefined) p.set("is_active", String(ia));
  const id = triStateParam(a.filterDeceased);
  if (id !== undefined) p.set("is_deceased", String(id));
  if (a.gender) p.set("gender", a.gender);
  const b = triStateParam(a.isBaptized);
  if (b !== undefined) p.set("is_baptized", String(b));
  const c = triStateParam(a.isConfirmed);
  if (c !== undefined) p.set("is_confirmed", String(c));
  const co = triStateParam(a.isCommunicant);
  if (co !== undefined) p.set("is_communicant", String(co));
  const m = triStateParam(a.isMarried);
  if (m !== undefined) p.set("is_married", String(m));
  if (a.ageGroup) p.set("age_group", a.ageGroup);
  if (a.joinedFrom) p.set("joined_from", a.joinedFrom);
  if (a.joinedTo) p.set("joined_to", a.joinedTo);
  if (a.deceasedFrom) p.set("deceased_from", a.deceasedFrom);
  if (a.deceasedTo) p.set("deceased_to", a.deceasedTo);
  if (a.baptismDateFrom) p.set("baptism_date_from", a.baptismDateFrom);
  if (a.baptismDateTo) p.set("baptism_date_to", a.baptismDateTo);
  if (a.firstCommunionDateFrom) p.set("first_communion_date_from", a.firstCommunionDateFrom);
  if (a.firstCommunionDateTo) p.set("first_communion_date_to", a.firstCommunionDateTo);
  if (a.confirmationDateFrom) p.set("confirmation_date_from", a.confirmationDateFrom);
  if (a.confirmationDateTo) p.set("confirmation_date_to", a.confirmationDateTo);
  if (a.marriageDateFrom) p.set("marriage_date_from", a.marriageDateFrom);
  if (a.marriageDateTo) p.set("marriage_date_to", a.marriageDateTo);
  if (a.dobFrom) p.set("date_of_birth_from", a.dobFrom);
  if (a.dobTo) p.set("date_of_birth_to", a.dobTo);
}

/** Same query shape as GET /exports/parish-registry.csv (includes search where supported). */
function registryExportParams(a: FilterState): Record<string, string> {
  const o: Record<string, string> = {};
  if (a.search.trim()) o.search = a.search.trim();
  if (a.membershipStatus) o.membership_status = a.membershipStatus;
  const ia = triStateParam(a.filterActive);
  if (ia !== undefined) o.is_active = String(ia);
  const id = triStateParam(a.filterDeceased);
  if (id !== undefined) o.is_deceased = String(id);
  if (a.gender) o.gender = a.gender;
  const b = triStateParam(a.isBaptized);
  if (b !== undefined) o.is_baptized = String(b);
  const c = triStateParam(a.isConfirmed);
  if (c !== undefined) o.is_confirmed = String(c);
  const co = triStateParam(a.isCommunicant);
  if (co !== undefined) o.is_communicant = String(co);
  const m = triStateParam(a.isMarried);
  if (m !== undefined) o.is_married = String(m);
  if (a.ageGroup) o.age_group = a.ageGroup;
  if (a.joinedFrom) o.joined_from = a.joinedFrom;
  if (a.joinedTo) o.joined_to = a.joinedTo;
  if (a.deceasedFrom) o.deceased_from = a.deceasedFrom;
  if (a.deceasedTo) o.deceased_to = a.deceasedTo;
  if (a.baptismDateFrom) o.baptism_date_from = a.baptismDateFrom;
  if (a.baptismDateTo) o.baptism_date_to = a.baptismDateTo;
  if (a.firstCommunionDateFrom) o.first_communion_date_from = a.firstCommunionDateFrom;
  if (a.firstCommunionDateTo) o.first_communion_date_to = a.firstCommunionDateTo;
  if (a.confirmationDateFrom) o.confirmation_date_from = a.confirmationDateFrom;
  if (a.confirmationDateTo) o.confirmation_date_to = a.confirmationDateTo;
  if (a.marriageDateFrom) o.marriage_date_from = a.marriageDateFrom;
  if (a.marriageDateTo) o.marriage_date_to = a.marriageDateTo;
  if (a.dobFrom) o.date_of_birth_from = a.dobFrom;
  if (a.dobTo) o.date_of_birth_to = a.dobTo;
  return o;
}

/** Payload for saving — mirrors currently applied registry filters (API snake_case keys). */
function appliedToSavedRecord(a: FilterState): Record<string, string> {
  return registryExportParams(a);
}

function savedFiltersApiToFilterState(f: Record<string, string>): FilterState {
  const e = emptyFilters();
  const g = (k: string) => f[k] ?? "";
  e.search = g("search");
  e.membershipStatus = (g("membership_status") || "") as FilterState["membershipStatus"];
  e.filterActive = g("is_active");
  e.filterDeceased = g("is_deceased");
  e.gender = g("gender");
  e.isBaptized = g("is_baptized");
  e.isConfirmed = g("is_confirmed");
  e.isCommunicant = g("is_communicant");
  e.isMarried = g("is_married");
  e.ageGroup = (g("age_group") || "") as FilterState["ageGroup"];
  e.joinedFrom = g("joined_from");
  e.joinedTo = g("joined_to");
  e.deceasedFrom = g("deceased_from");
  e.deceasedTo = g("deceased_to");
  e.baptismDateFrom = g("baptism_date_from");
  e.baptismDateTo = g("baptism_date_to");
  e.firstCommunionDateFrom = g("first_communion_date_from");
  e.firstCommunionDateTo = g("first_communion_date_to");
  e.confirmationDateFrom = g("confirmation_date_from");
  e.confirmationDateTo = g("confirmation_date_to");
  e.marriageDateFrom = g("marriage_date_from");
  e.marriageDateTo = g("marriage_date_to");
  e.dobFrom = g("date_of_birth_from");
  e.dobTo = g("date_of_birth_to");
  return e;
}

function isRegistryFilterStateActive(a: FilterState): boolean {
  const z = emptyFilters();
  return (Object.keys(z) as (keyof FilterState)[]).some((k) => a[k] !== z[k]);
}

function buildPrintRegistryHref(params: Record<string, string>): string {
  const qs = new URLSearchParams();
  qs.set("kind", "parish-registry");
  for (const [k, v] of Object.entries(params)) {
    if (v) qs.set(k, v);
  }
  return `/exports/print?${qs.toString()}`;
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="text-lg font-semibold tabular-nums text-slate-900">{value}</dd>
    </div>
  );
}

export default function ParishRegistryListPage() {
  const router = useRouter();
  const token = getAccessToken();
  const { user, status, isAdmin } = useAuth();

  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<ChurchMemberListResponse["items"]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const [stats, setStats] = useState<ChurchMemberStatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const [filters, setFilters] = useState<FilterState>(emptyFilters);
  const [applied, setApplied] = useState<FilterState>(emptyFilters);

  const [savedFilters, setSavedFilters] = useState<RegistrySavedFilterRecord[]>([]);
  const [savedFiltersLoading, setSavedFiltersLoading] = useState(false);
  const [savedFiltersError, setSavedFiltersError] = useState<string | null>(null);
  const [savedFiltersRev, setSavedFiltersRev] = useState(0);
  const [saveFormOpen, setSaveFormOpen] = useState(false);
  const [saveFormName, setSaveFormName] = useState("");
  const [saveBusy, setSaveBusy] = useState(false);

  const hasNextPage = page * pageSize < total;

  useEffect(() => {
    if (status === "authenticated" && user && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, user, isAdmin, router]);

  useEffect(() => {
    if (status !== "authenticated" || !isAdmin || !token) return;
    let cancelled = false;
    setSavedFiltersLoading(true);
    setSavedFiltersError(null);
    void apiFetch<RegistrySavedFilterRecord[]>("/api/v1/registry-saved-filters/", {
      method: "GET",
      token,
    })
      .then((rows) => {
        if (!cancelled) setSavedFilters(rows);
      })
      .catch((err: unknown) => {
        if (!cancelled) setSavedFiltersError(toErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setSavedFiltersLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, isAdmin, token, savedFiltersRev]);

  useEffect(() => {
    if (status === "loading") return;
    if (status !== "authenticated" || !user || !isAdmin) {
      if (status === "unauthenticated") {
        setError("You need to sign in to view this page.");
      }
      setLoading(false);
      return;
    }

    if (!token) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    appendRegistryListParams(params, applied);

    const listReq = apiFetch<ChurchMemberListResponse>(
      `/api/v1/church-members/?${params.toString()}`,
      { method: "GET", token },
    );
    const statsReq = apiFetch<ChurchMemberStatsResponse>("/api/v1/church-members/stats", {
      method: "GET",
      token,
    });

    Promise.all([listReq, statsReq])
      .then(([list, st]) => {
        if (cancelled) return;
        setItems(list.items);
        setTotal(list.total);
        setStats(st);
      })
      .catch((err) => {
        if (cancelled) return;
        if (isUnauthorized(err)) {
          clearSessionAndRedirect(router, "session_expired");
          return;
        }
        if (isInactiveAccountError(err)) {
          clearSessionAndRedirect(router, "account_inactive");
          return;
        }
        setError(toErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, pageSize, applied, token, router, status, user, isAdmin]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setApplied({ ...filters });
  }

  function resetAllFilters() {
    const cleared = emptyFilters();
    setFilters(cleared);
    setApplied(cleared);
    setPage(1);
    setSaveFormOpen(false);
    setSaveFormName("");
  }

  async function downloadRegistryCsv() {
    setExportError(null);
    if (!token) return;
    const params = registryExportParams(applied);
    try {
      const { blob, filename } = await apiFetchBlob("/api/v1/exports/parish-registry.csv", {
        token,
        params,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename ?? "parish-registry-export.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router, "session_expired");
        return;
      }
      setExportError(toErrorMessage(err));
    }
  }

  function openRegistryPrint() {
    setExportError(null);
    window.open(buildPrintRegistryHref(registryExportParams(applied)), "_blank", "noopener,noreferrer");
  }

  function bumpSavedFiltersList() {
    setSavedFiltersRev((n) => n + 1);
  }

  function applySavedPreset(rec: RegistrySavedFilterRecord) {
    const next = savedFiltersApiToFilterState(rec.filters);
    setFilters(next);
    setApplied(next);
    setPage(1);
  }

  async function submitSaveCurrentPreset() {
    const name = saveFormName.trim();
    if (!name || !token || !isRegistryFilterStateActive(applied)) return;
    setSaveBusy(true);
    setSavedFiltersError(null);
    try {
      await apiFetch<RegistrySavedFilterRecord>("/api/v1/registry-saved-filters/", {
        method: "POST",
        token,
        body: { name, filters: appliedToSavedRecord(applied) },
      });
      setSaveFormOpen(false);
      setSaveFormName("");
      bumpSavedFiltersList();
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router, "session_expired");
        return;
      }
      setSavedFiltersError(toErrorMessage(err));
    } finally {
      setSaveBusy(false);
    }
  }

  async function deleteSavedPreset(id: string) {
    if (!token) return;
    if (!window.confirm("Remove this saved filter?")) return;
    setSavedFiltersError(null);
    try {
      await apiFetch(`/api/v1/registry-saved-filters/${id}`, { method: "DELETE", token });
      bumpSavedFiltersList();
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router, "session_expired");
        return;
      }
      setSavedFiltersError(toErrorMessage(err));
    }
  }

  async function renameSavedPreset(id: string, currentName: string) {
    if (!token) return;
    const name = window.prompt("Rename saved filter", currentName);
    if (name === null) return;
    const trimmed = name.trim();
    if (!trimmed || trimmed === currentName) return;
    setSavedFiltersError(null);
    try {
      await apiFetch(`/api/v1/registry-saved-filters/${id}`, {
        method: "PATCH",
        token,
        body: { name: trimmed },
      });
      bumpSavedFiltersList();
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router, "session_expired");
        return;
      }
      setSavedFiltersError(toErrorMessage(err));
    }
  }

  const inputCls = fieldInput;

  if (status === "loading") {
    return (
      <PageShell
        title="Parish registry"
        description="Church member records (separate from login accounts)."
      >
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
            Checking access…
          </div>
        </ContentCard>
      </PageShell>
    );
  }

  if (status === "authenticated" && user && !isAdmin) {
    return (
      <PageShell title="Parish registry" description="Administrators only.">
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
            Redirecting…
          </div>
        </ContentCard>
      </PageShell>
    );
  }

  if (status !== "authenticated" || !user) {
    return (
      <PageShell title="Parish registry" description="">
        {error ? <div className={surfaceError}>{error}</div> : null}
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Parish registry"
      description="Official parish records for administration (sacraments, membership, deceased). This is separate from app login accounts. Creating a record here does not create a software login."
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href="/members/new" className={btnPrimary}>
          Add member record
        </Link>
      </div>

      {stats ? (
        <CollapsibleSection
          className="mb-4"
          title="Registry summary"
          defaultOpen
          description={
            <span className="text-xs text-slate-500">
              Age bands use UTC &ldquo;today&rdquo; and recorded date of birth. Child 0–12, young adult
              13–17, adult 18+. Rows without DOB are excluded from those three counts (see Unknown).
            </span>
          }
        >
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Membership status</h3>
              <p className="mt-1 text-xs text-slate-500">
                Counts follow each record&rsquo;s membership status (not the generic &ldquo;active in
                registry&rdquo; checkbox).
              </p>
              <dl className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
                <StatCard label="Total" value={stats.total_members} />
                <StatCard label="Active" value={stats.active_members} />
                <StatCard label="Inactive" value={stats.inactive_members} />
                <StatCard label="Visitor" value={stats.visitor_members} />
                <StatCard label="Transferred" value={stats.transferred_members} />
                <StatCard label="Deceased" value={stats.deceased_members} />
              </dl>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Demographics</h3>
              <dl className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard
                  label="Unknown DOB (age bands)"
                  value={stats.age_groups.unknown ?? 0}
                />
                <StatCard label="Male" value={stats.male_members} />
                <StatCard label="Female" value={stats.female_members} />
                <StatCard label="Children (0–12)" value={stats.children_members} />
                <StatCard label="Young adults (13–17)" value={stats.young_adult_members} />
                <StatCard label="Adults (18+)" value={stats.adult_members} />
              </dl>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Sacramental &amp; marital</h3>
              <dl className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard label="Baptized" value={stats.baptized_members} />
                <StatCard label="Confirmed" value={stats.confirmed_members} />
                <StatCard label="Communicants" value={stats.communicant_members} />
                <StatCard label="Married" value={stats.married_members} />
                <StatCard label="Single (not married)" value={stats.single_members} />
              </dl>
            </div>
          </div>
        </CollapsibleSection>
      ) : null}

      <CollapsibleSection
        className="mb-4"
        title="Saved filters"
        defaultOpen
        description={
          <>
            Save the filter set you have <strong>applied</strong> below, then load it anytime. Exports
            and print use the same applied filters as the list.
          </>
        }
      >
        {savedFiltersError ? <div className={`${surfaceError} mt-3`}>{savedFiltersError}</div> : null}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            className={btnSecondary}
            disabled={!isRegistryFilterStateActive(applied)}
            title={
              isRegistryFilterStateActive(applied)
                ? undefined
                : "Apply at least one filter before saving a preset"
            }
            onClick={() => {
              setSaveFormOpen((o) => !o);
              setSaveFormName("");
            }}
          >
            Save current filter
          </button>
          {savedFiltersLoading ? (
            <span className="text-sm text-slate-500">Loading saved filters…</span>
          ) : null}
        </div>
        {saveFormOpen ? (
          <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50/80 p-4">
            <label htmlFor="save-preset-name" className={fieldLabel}>
              Name this filter set
            </label>
            <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-end">
              <input
                id="save-preset-name"
                value={saveFormName}
                onChange={(e) => setSaveFormName(e.target.value)}
                placeholder="e.g. Young adults, Baptized 2024"
                className={`${inputCls} sm:max-w-md`}
                maxLength={120}
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className={btnPrimary}
                  disabled={
                    saveBusy ||
                    !saveFormName.trim() ||
                    !isRegistryFilterStateActive(applied)
                  }
                  onClick={() => void submitSaveCurrentPreset()}
                >
                  {saveBusy ? "Saving…" : "Save"}
                </button>
                <button
                  type="button"
                  className={btnSecondary}
                  disabled={saveBusy}
                  onClick={() => {
                    setSaveFormOpen(false);
                    setSaveFormName("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : null}
        {!savedFiltersLoading && savedFilters.length === 0 ? (
          <p className="mt-4 text-sm text-slate-600">
            No saved filters yet. Save frequently used registry searches here.
          </p>
        ) : null}
        {savedFilters.length > 0 ? (
          <ul className="mt-4 flex flex-wrap gap-2" aria-label="Saved registry filters">
            {savedFilters.map((sf) => (
              <li
                key={sf.id}
                className="inline-flex max-w-full items-center gap-1 rounded-full border border-slate-200 bg-white py-1 pl-3 pr-1 shadow-sm"
              >
                <button
                  type="button"
                  className="min-w-0 truncate text-left text-sm font-medium text-slate-900 hover:text-indigo-900"
                  onClick={() => applySavedPreset(sf)}
                >
                  {sf.name}
                </button>
                <button
                  type="button"
                  className="shrink-0 rounded-full px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  onClick={() => void renameSavedPreset(sf.id, sf.name)}
                  aria-label={`Rename ${sf.name}`}
                >
                  Rename
                </button>
                <button
                  type="button"
                  className="shrink-0 rounded-full px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                  onClick={() => void deleteSavedPreset(sf.id)}
                  aria-label={`Delete ${sf.name}`}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </CollapsibleSection>

      <div className="space-y-4">
        <CollapsibleSection
          title="Filter &amp; export"
          defaultOpen
          description="Narrow the list, then export CSV or open a print-friendly view using the same filters."
        >
          {exportError ? <div className={`${surfaceError} mb-4`}>{exportError}</div> : null}
          <div className="mb-4 flex flex-wrap gap-3">
            <button type="button" className={btnPrimary} onClick={() => void downloadRegistryCsv()}>
              Download CSV
            </button>
            <button type="button" className={btnSecondary} onClick={openRegistryPrint}>
              Open print view
            </button>
          </div>
          <div className={surfaceInfo + " mb-4 text-sm"}>
            Print uses the same data as CSV (notes are never included). Use your browser&rsquo;s{" "}
            <strong>Print → Save as PDF</strong> if you need a file.
          </div>
          <form onSubmit={onSearch} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-1.5 md:col-span-2">
                <label htmlFor="reg-search" className={fieldLabel}>
                  Search
                </label>
                <input
                  id="reg-search"
                  value={filters.search}
                  onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
                  placeholder="Name, email, or registration #"
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Membership</label>
                <select
                  value={filters.membershipStatus}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      membershipStatus: e.target.value as typeof f.membershipStatus,
                    }))
                  }
                  className={inputCls}
                >
                  {MEMBERSHIP_OPTIONS.map((o) => (
                    <option key={o.label} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Registry row active</label>
                <select
                  value={filters.filterActive}
                  onChange={(e) => setFilters((f) => ({ ...f, filterActive: e.target.value }))}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Deceased</label>
                <select
                  value={filters.filterDeceased}
                  onChange={(e) => setFilters((f) => ({ ...f, filterDeceased: e.target.value }))}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Gender</label>
                <select
                  value={filters.gender}
                  onChange={(e) => setFilters((f) => ({ ...f, gender: e.target.value }))}
                  className={inputCls}
                >
                  {GENDER_OPTIONS.map((o) => (
                    <option key={o.label} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Age band (from DOB)</label>
                <select
                  value={filters.ageGroup}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      ageGroup: e.target.value as typeof f.ageGroup,
                    }))
                  }
                  className={inputCls}
                >
                  {AGE_GROUP_OPTIONS.map((o) => (
                    <option key={o.label} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Date of birth from</label>
                <input
                  type="date"
                  value={filters.dobFrom}
                  onChange={(e) => setFilters((f) => ({ ...f, dobFrom: e.target.value }))}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Date of birth to</label>
                <input
                  type="date"
                  value={filters.dobTo}
                  onChange={(e) => setFilters((f) => ({ ...f, dobTo: e.target.value }))}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Baptized</label>
                <select
                  value={filters.isBaptized}
                  onChange={(e) => setFilters((f) => ({ ...f, isBaptized: e.target.value }))}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Confirmed</label>
                <select
                  value={filters.isConfirmed}
                  onChange={(e) => setFilters((f) => ({ ...f, isConfirmed: e.target.value }))}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Communicant</label>
                <select
                  value={filters.isCommunicant}
                  onChange={(e) => setFilters((f) => ({ ...f, isCommunicant: e.target.value }))}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Married</label>
                <select
                  value={filters.isMarried}
                  onChange={(e) => setFilters((f) => ({ ...f, isMarried: e.target.value }))}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No (single)</option>
                </select>
              </div>
            </div>

            <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-4">
              <h3 className="text-sm font-semibold text-slate-800">Sacramental dates</h3>
              <p className="mt-1 text-xs text-slate-500">
                Filters use the recorded date fields only. Rows without a date are excluded when a
                range is set.
              </p>
              <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Baptism date
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>From</label>
                      <input
                        type="date"
                        value={filters.baptismDateFrom}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, baptismDateFrom: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>To</label>
                      <input
                        type="date"
                        value={filters.baptismDateTo}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, baptismDateTo: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    First communion date
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>From</label>
                      <input
                        type="date"
                        value={filters.firstCommunionDateFrom}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, firstCommunionDateFrom: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>To</label>
                      <input
                        type="date"
                        value={filters.firstCommunionDateTo}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, firstCommunionDateTo: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Confirmation date
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>From</label>
                      <input
                        type="date"
                        value={filters.confirmationDateFrom}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, confirmationDateFrom: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>To</label>
                      <input
                        type="date"
                        value={filters.confirmationDateTo}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, confirmationDateTo: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Marriage date
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>From</label>
                      <input
                        type="date"
                        value={filters.marriageDateFrom}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, marriageDateFrom: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className={fieldLabel}>To</label>
                      <input
                        type="date"
                        value={filters.marriageDateTo}
                        onChange={(e) =>
                          setFilters((f) => ({ ...f, marriageDateTo: e.target.value }))
                        }
                        className={inputCls}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-1.5">
                <label className={fieldLabel}>Joined from</label>
                <input
                  type="date"
                  value={filters.joinedFrom}
                  onChange={(e) => setFilters((f) => ({ ...f, joinedFrom: e.target.value }))}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Joined to</label>
                <input
                  type="date"
                  value={filters.joinedTo}
                  onChange={(e) => setFilters((f) => ({ ...f, joinedTo: e.target.value }))}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Date of death from</label>
                <input
                  type="date"
                  value={filters.deceasedFrom}
                  onChange={(e) => setFilters((f) => ({ ...f, deceasedFrom: e.target.value }))}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Date of death to</label>
                <input
                  type="date"
                  value={filters.deceasedTo}
                  onChange={(e) => setFilters((f) => ({ ...f, deceasedTo: e.target.value }))}
                  className={inputCls}
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="submit" className={btnPrimary}>
                Apply filters
              </button>
              <button type="button" className={btnSecondary} onClick={resetAllFilters}>
                Reset filters
              </button>
            </div>
          </form>
        </CollapsibleSection>

        {error ? <div className={surfaceError}>{error}</div> : null}

        <CollapsibleSection
          title="Registry records"
          defaultOpen
          description="Results for the filters you have applied (pagination is not saved in presets)."
        >
          {loading ? (
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
              Loading registry…
            </div>
          ) : null}

          {!loading ? (
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 bg-slate-50/80 px-4 py-3">
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{total}</span> record
                {total === 1 ? "" : "s"}
                {applied.search.trim() ? (
                  <span className="text-slate-500">
                    {" "}
                    · search &ldquo;{applied.search.trim()}&rdquo;
                  </span>
                ) : null}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-100 bg-white text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Registration #</th>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Joined</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {items.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-10 text-center text-slate-600">
                        No records match. Try adjusting filters or create a member.
                      </td>
                    </tr>
                  ) : (
                    items.map((m) => (
                      <tr key={m.church_member_id} className="hover:bg-slate-50/80">
                        <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-700">
                          {m.registration_number ?? "—"}
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            href={`/members/${m.church_member_id}`}
                            className="font-medium text-slate-900 underline-offset-2 hover:underline"
                          >
                            {m.full_name}
                          </Link>
                          {m.is_deceased ? (
                            <span className="ml-2 text-xs font-medium text-slate-500">(deceased)</span>
                          ) : null}
                        </td>
                        <td className="px-4 py-3 capitalize text-slate-700">{m.membership_status}</td>
                        <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                          {new Date(m.joined_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
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
          ) : null}
        </CollapsibleSection>
      </div>
    </PageShell>
  );
}
