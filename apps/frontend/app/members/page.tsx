"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch, type ApiError } from "lib/api";
import { getAccessToken } from "lib/session";
import type { MemberListItem, MemberListResponse, MeResponse } from "lib/types";

function toErrorMessage(err: unknown) {
  if (typeof err === "object" && err && "status" in err) {
    const e = err as ApiError;
    if (e.detail) return e.detail;
    return `Request failed (${e.status})`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

export default function MembersPage() {
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState<MemberListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const [me, setMe] = useState<MeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [searchApplied, setSearchApplied] = useState("");

  const isAdmin = useMemo(() => me?.role === "admin", [me]);

  useEffect(() => {
    if (!token) {
      setError("Not authenticated. Please log in again.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    apiFetch<MeResponse>("/api/v1/auth/me", { method: "GET", token })
      .then((meRes) => {
        if (cancelled) return;
        setMe(meRes);
        if (meRes.role !== "admin") {
          setMembers([]);
          setTotal(0);
          return;
        }

        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        if (searchApplied) params.set("search", searchApplied);

        return apiFetch<MemberListResponse>(
          `/api/v1/members/?${params.toString()}`,
          { method: "GET", token },
        ).then((list) => {
          if (cancelled) return;
          setMembers(list.items);
          setTotal(list.total);
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setError(toErrorMessage(err));
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, pageSize, searchApplied, token]);

  async function onSearch() {
    setError(null);
    setPage(1);
    setSearchApplied(search.trim());
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Member Directory</h1>
          <p className="text-sm text-slate-600">Admin-only member listing.</p>
        </div>

        <div className="flex items-center gap-2">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name or email"
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 md:w-72"
          />
          <button
            type="button"
            onClick={onSearch}
            className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Search
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      {loading ? <p className="text-sm text-slate-600">Loading...</p> : null}

      {!loading && me && !isAdmin ? (
        <div className="rounded border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-900">Access denied</h2>
          <p className="mt-1 text-sm text-slate-600">
            Your role is <span className="font-medium text-slate-900">{me.role}</span>. Admin access is required.
          </p>
        </div>
      ) : null}

      {!loading && isAdmin ? (
        <div className="rounded border border-slate-200 bg-white">
          <div className="border-b p-3 text-sm text-slate-600">
            Total members: <span className="font-semibold text-slate-900">{total}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2">Full name</th>
                  <th className="px-4 py-2">Email</th>
                  <th className="px-4 py-2">Role</th>
                  <th className="px-4 py-2">Active</th>
                  <th className="px-4 py-2">Preferred</th>
                </tr>
              </thead>
              <tbody>
                {members.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-600">
                      No members found.
                    </td>
                  </tr>
                ) : (
                  members.map((m) => (
                    <tr key={m.member_id} className="border-t last:border-b">
                      <td className="px-4 py-2">
                        <Link href={`/members/${m.member_id}`} className="font-medium text-slate-900 hover:underline">
                          {m.full_name}
                        </Link>
                      </td>
                      <td className="px-4 py-2 text-slate-700">{m.email}</td>
                      <td className="px-4 py-2 text-slate-700">{m.role}</td>
                      <td className="px-4 py-2 text-slate-700">{m.is_active ? "Yes" : "No"}</td>
                      <td className="px-4 py-2 text-slate-700">
                        {m.preferred_channel ?? "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t p-3">
            <div className="text-sm text-slate-600">
              Page <span className="font-semibold text-slate-900">{page}</span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 disabled:opacity-60"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={members.length < pageSize}
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 disabled:opacity-60"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}


