"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type { MemberListItem, MemberListResponse } from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";

export default function MembersPage() {
  const router = useRouter();
  const token = getAccessToken();
  const { user, status, isAdmin } = useAuth();

  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState<MemberListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [searchApplied, setSearchApplied] = useState("");

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

    apiFetch<MemberListResponse>(`/api/v1/members/?${params.toString()}`, {
      method: "GET",
      token,
    })
      .then((list) => {
        if (cancelled) return;
        setMembers(list.items);
        setTotal(list.total);
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
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, pageSize, searchApplied, token, router, status, user, isAdmin]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearchApplied(search.trim());
  }

  if (status === "loading") {
    return (
      <PageShell
        title="Members"
        description="Search and open parishioner records. Only administrators can edit directory data."
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
      <PageShell
        title="Members"
        description="Search and open parishioner records. Only administrators can edit directory data."
      >
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            Redirecting to your profile…
          </div>
        </ContentCard>
      </PageShell>
    );
  }

  if (status !== "authenticated" || !user) {
    return (
      <PageShell
        title="Members"
        description="Search and open parishioner records. Only administrators can edit directory data."
      >
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
      title="Members"
      description="Search and open parishioner records. Only administrators can edit directory data."
    >
      <div className="space-y-4">
        <ContentCard>
          <form onSubmit={onSearch} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="min-w-0 flex-1 space-y-1.5">
              <label htmlFor="member-search" className="text-sm font-medium text-slate-800">
                Search
              </label>
              <input
                id="member-search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Name or email"
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
            </div>
            <button
              type="submit"
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
            >
              Search
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
              Loading the directory…
            </div>
          </ContentCard>
        ) : null}

        {!loading ? (
          <ContentCard className="overflow-hidden p-0">
            <div className="border-b border-slate-100 bg-slate-50/80 px-4 py-3">
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{total}</span> member
                {total === 1 ? "" : "s"}
                {searchApplied ? (
                  <span className="text-slate-500">
                    {" "}
                    · filtered by &ldquo;{searchApplied}&rdquo;
                  </span>
                ) : null}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-100 bg-white text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Email</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Active</th>
                    <th className="px-4 py-3">Preferred</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {members.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-10 text-center text-slate-600">
                        No members match your search.
                      </td>
                    </tr>
                  ) : (
                    members.map((m) => (
                      <tr key={m.member_id} className="hover:bg-slate-50/80">
                        <td className="px-4 py-3">
                          <Link
                            href={`/members/${m.member_id}`}
                            className="font-medium text-slate-900 underline-offset-2 hover:underline"
                          >
                            {m.full_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-slate-700">{m.email}</td>
                        <td className="px-4 py-3 capitalize text-slate-700">
                          {m.role.split("_").join(" ")}
                        </td>
                        <td className="px-4 py-3 text-slate-700">{m.is_active ? "Yes" : "No"}</td>
                        <td className="px-4 py-3 capitalize text-slate-700">
                          {m.preferred_channel ?? "—"}
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
