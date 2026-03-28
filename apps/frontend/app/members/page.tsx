"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type {
  ChurchMemberListResponse,
  ChurchMemberStatsResponse,
  ChurchMembershipStatus,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";

const MEMBERSHIP_OPTIONS: { value: "" | ChurchMembershipStatus; label: string }[] = [
  { value: "", label: "Any status" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "visitor", label: "Visitor" },
  { value: "transferred", label: "Transferred" },
  { value: "deceased", label: "Deceased" },
];

function triStateParam(v: string): boolean | undefined {
  if (v === "true") return true;
  if (v === "false") return false;
  return undefined;
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

  const [search, setSearch] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [membershipStatus, setMembershipStatus] = useState<"" | ChurchMembershipStatus>("");
  const [filterActive, setFilterActive] = useState<string>(""); // "" | "true" | "false"
  const [filterDeceased, setFilterDeceased] = useState<string>("");

  const [statusApplied, setStatusApplied] = useState<"" | ChurchMembershipStatus>("");
  const [activeApplied, setActiveApplied] = useState<string>("");
  const [deceasedApplied, setDeceasedApplied] = useState<string>("");

  const hasNextPage = page * pageSize < total;

  useEffect(() => {
    if (status === "authenticated" && user && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, user, isAdmin, router]);

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
    if (searchApplied) params.set("search", searchApplied);
    if (statusApplied) params.set("membership_status", statusApplied);
    const a = triStateParam(activeApplied);
    if (a !== undefined) params.set("is_active", String(a));
    const d = triStateParam(deceasedApplied);
    if (d !== undefined) params.set("is_deceased", String(d));

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
  }, [
    page,
    pageSize,
    searchApplied,
    statusApplied,
    activeApplied,
    deceasedApplied,
    token,
    router,
    status,
    user,
    isAdmin,
  ]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearchApplied(search.trim());
    setStatusApplied(membershipStatus);
    setActiveApplied(filterActive);
    setDeceasedApplied(filterDeceased);
  }

  const inputCls =
    "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400";

  if (status === "loading") {
    return (
      <PageShell
        title="Parish registry"
        description="Church member records (separate from login accounts)."
      >
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
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
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            Redirecting…
          </div>
        </ContentCard>
      </PageShell>
    );
  }

  if (status !== "authenticated" || !user) {
    return (
      <PageShell title="Parish registry" description="">
        {error ? (
          <ContentCard>
            <p className="text-sm text-red-800">{error}</p>
          </ContentCard>
        ) : null}
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Parish registry"
      description="Official parish records for administration (sacraments, membership, deceased). This is separate from app login accounts. Creating a record here does not create a software login."
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/members/new"
          className="inline-flex rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
        >
          Add member record
        </Link>
      </div>

      {stats ? (
        <ContentCard className="mb-4">
          <h2 className="text-sm font-semibold text-slate-900">Registry summary</h2>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2">
              <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Total</dt>
              <dd className="text-lg font-semibold text-slate-900">{stats.total_members}</dd>
            </div>
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2">
              <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Active</dt>
              <dd className="text-lg font-semibold text-slate-900">{stats.active_members}</dd>
            </div>
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2">
              <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Deceased</dt>
              <dd className="text-lg font-semibold text-slate-900">{stats.deceased_members}</dd>
            </div>
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2">
              <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Registry + app login</dt>
              <dd className="text-lg font-semibold text-slate-900">{stats.members_with_accounts}</dd>
            </div>
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2">
              <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Registry only</dt>
              <dd className="text-lg font-semibold text-slate-900">{stats.members_without_accounts}</dd>
            </div>
          </dl>
        </ContentCard>
      ) : null}

      <div className="space-y-4">
        <ContentCard>
          <form onSubmit={onSearch} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-1.5 md:col-span-2">
                <label htmlFor="reg-search" className="text-sm font-medium text-slate-800">
                  Search
                </label>
                <input
                  id="reg-search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Name, email, or registration #"
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Membership</label>
                <select
                  value={membershipStatus}
                  onChange={(e) => setMembershipStatus(e.target.value as typeof membershipStatus)}
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
                <label className="text-sm font-medium text-slate-800">Active</label>
                <select
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Deceased flag</label>
                <select
                  value={filterDeceased}
                  onChange={(e) => setFilterDeceased(e.target.value)}
                  className={inputCls}
                >
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
            >
              Apply filters
            </button>
          </form>
        </ContentCard>

        {error ? (
          <ContentCard>
            <p className="text-sm text-red-800">{error}</p>
          </ContentCard>
        ) : null}

        {loading ? (
          <ContentCard>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
              Loading registry…
            </div>
          </ContentCard>
        ) : null}

        {!loading ? (
          <ContentCard className="overflow-hidden p-0">
            <div className="border-b border-slate-100 bg-slate-50/80 px-4 py-3">
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{total}</span> record
                {total === 1 ? "" : "s"}
                {searchApplied ? (
                  <span className="text-slate-500">
                    {" "}
                    · search &ldquo;{searchApplied}&rdquo;
                  </span>
                ) : null}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-100 bg-white text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Contact</th>
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
                        <td className="px-4 py-3 text-slate-700">
                          <div>{m.email ?? "—"}</div>
                          {m.phone ? <div className="text-xs text-slate-500">{m.phone}</div> : null}
                        </td>
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
          </ContentCard>
        ) : null}
      </div>
    </PageShell>
  );
}
