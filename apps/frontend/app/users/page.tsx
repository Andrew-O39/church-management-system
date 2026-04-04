"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type { MemberListResponse, UserRole } from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { btnPrimary, fieldInput, surfaceError } from "lib/ui";

function formatRole(role: string) {
  return role.split("_").join(" ");
}

export default function AppUsersListPage() {
  const router = useRouter();
  const token = getAccessToken();
  const { user, status, isAdmin } = useAuth();

  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<MemberListResponse["items"]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [roleFilter, setRoleFilter] = useState<"" | UserRole>("");
  const [activeFilter, setActiveFilter] = useState<string>(""); // "" | "true" | "false"

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
    if (roleFilter) params.set("role", roleFilter);
    if (activeFilter === "true" || activeFilter === "false") {
      params.set("is_active", activeFilter);
    }

    apiFetch<MemberListResponse>(`/api/v1/members/?${params.toString()}`, { method: "GET", token })
      .then((res) => {
        if (!cancelled) {
          setItems(res.items);
          setTotal(res.total);
        }
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
        setItems([]);
        setTotal(0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, status, user, isAdmin, page, pageSize, searchApplied, roleFilter, activeFilter, router]);

  function onApplyFilters(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearchApplied(search.trim());
  }

  return (
    <PageShell
      title="App users"
      description="Login accounts for the app (events, ministries, attendance, volunteering). This is not the parish sacramental registry—use Parish registry for official church records."
    >
      {!isAdmin && status === "authenticated" ? (
        <ContentCard>
          <p className="text-sm text-slate-700">This page is only available to administrators.</p>
        </ContentCard>
      ) : null}

      {isAdmin ? (
        <ContentCard className="space-y-4">
          <form onSubmit={onApplyFilters} className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-end">
            <div className="min-w-[200px] flex-1 space-y-1">
              <label className="text-xs font-semibold text-slate-800">Search</label>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Name or email"
                className={fieldInput}
              />
            </div>
            <div className="w-full space-y-1 md:w-40">
              <label className="text-xs font-semibold text-slate-800">Role</label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value as "" | UserRole)}
                className={fieldInput}
              >
                <option value="">Any</option>
                <option value="admin">Admin</option>
                <option value="group_leader">Group leader</option>
                <option value="member">Member</option>
              </select>
            </div>
            <div className="w-full space-y-1 md:w-36">
              <label className="text-xs font-semibold text-slate-800">Active</label>
              <select
                value={activeFilter}
                onChange={(e) => setActiveFilter(e.target.value)}
                className={fieldInput}
              >
                <option value="">Any</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
            <button type="submit" className={btnPrimary}>
              Apply
            </button>
          </form>

          {error ? <div className={surfaceError}>{error}</div> : null}

          {loading ? (
            <p className="text-sm text-slate-600">Loading…</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-slate-600">No app users match these filters.</p>
          ) : (
            <>
              <div className="overflow-x-auto rounded-lg border border-slate-100">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-100 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-3 py-2">Name</th>
                      <th className="px-3 py-2">Email</th>
                      <th className="px-3 py-2">Role</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2"> </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {items.map((row) => (
                      <tr key={row.member_id}>
                        <td className="px-3 py-2 font-medium text-slate-900">{row.full_name}</td>
                        <td className="px-3 py-2 text-slate-700">{row.email}</td>
                        <td className="px-3 py-2 text-slate-700">{formatRole(row.role)}</td>
                        <td className="px-3 py-2">
                          <span
                            className={
                              row.is_active ? "text-green-800" : "text-amber-800"
                            }
                          >
                            {row.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Link
                            href={`/users/${row.member_id}`}
                            className="text-sm font-medium text-slate-900 underline-offset-2 hover:underline"
                          >
                            Manage
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-600">
                <span>
                  Page {page} — showing {items.length} of {total}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 shadow-sm hover:bg-slate-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={!hasNextPage}
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-800 shadow-sm hover:bg-slate-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </ContentCard>
      ) : null}
    </PageShell>
  );
}
