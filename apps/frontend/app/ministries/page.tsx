"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type { MinistryListResponse, MyMinistriesResponse } from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { btnPrimary, fieldInput, fieldLabel, surfaceError } from "lib/ui";

const inputCls = fieldInput;

export default function MinistriesPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [adminItems, setAdminItems] = useState<MinistryListResponse["items"]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [search, setSearch] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [activeOnly, setActiveOnly] = useState<boolean | null>(true);

  const [myItems, setMyItems] = useState<MyMinistriesResponse["items"]>([]);

  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    if (!token || status !== "authenticated") {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      if (isAdmin) {
        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
        if (searchApplied) params.set("search", searchApplied);
        if (activeOnly !== null) params.set("is_active", String(activeOnly));
        const data = await apiFetch<MinistryListResponse>(
          `/api/v1/ministries/?${params}`,
          { method: "GET", token },
        );
        setAdminItems(data.items);
        setTotal(data.total);
      } else {
        const data = await apiFetch<MyMinistriesResponse>("/api/v1/ministries/me", {
          method: "GET",
          token,
        });
        setMyItems(data.items);
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
  }, [token, status, isAdmin, page, searchApplied, activeOnly, router]);

  useEffect(() => {
    if (status === "loading") return;
    void load();
  }, [load, status]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!token || !newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await apiFetch("/api/v1/ministries/", {
        method: "POST",
        token,
        body: {
          name: newName.trim(),
          description: newDesc.trim() || null,
          is_active: true,
        },
      });
      setNewName("");
      setNewDesc("");
      setPage(1);
      setSearchApplied("");
      setSearch("");
      await load();
    } catch (err) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router, "session_expired");
        return;
      }
      setError(toErrorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearchApplied(search.trim());
  }

  const hasNextPage = page * pageSize < total;

  if (status === "loading") {
    return (
      <PageShell
        title="Ministries"
        description="Parish groups, ministries, and fellowship communities."
      >
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Ministries"
      description={
        isAdmin
          ? "Create and manage ministries. Assign members from the directory."
          : "Ministries and groups you belong to. Ask an administrator to add you to a ministry."
      }
    >
      <div className="space-y-4">
        {error ? <div className={surfaceError}>{error}</div> : null}

        {isAdmin ? (
          <ContentCard>
            <h2 className="shepherd-section-title">New ministry</h2>
            <form onSubmit={onCreate} className="mt-3 space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label htmlFor="m-new-name" className={fieldLabel}>
                    Name
                  </label>
                  <input
                    id="m-new-name"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className={inputCls}
                    placeholder="e.g. Choir, Youth, Ushers"
                  />
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="m-new-desc" className={fieldLabel}>
                    Description <span className="font-normal text-slate-500">(optional)</span>
                  </label>
                  <input
                    id="m-new-desc"
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    className={inputCls}
                  />
                </div>
              </div>
              <button type="submit" disabled={creating || !newName.trim()} className={btnPrimary}>
                {creating ? "Creating…" : "Create ministry"}
              </button>
            </form>
          </ContentCard>
        ) : null}

        {isAdmin ? (
          <ContentCard>
            <form onSubmit={onSearch} className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="min-w-0 flex-1 space-y-1.5">
                <label htmlFor="m-search" className={fieldLabel}>
                  Search by name
                </label>
                <input
                  id="m-search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className={inputCls}
                  placeholder="Filter ministries"
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={activeOnly === true}
                  onChange={(e) => setActiveOnly(e.target.checked ? true : null)}
                />
                Active only
              </label>
              <button type="submit" className={btnPrimary}>
                Search
              </button>
            </form>
          </ContentCard>
        ) : null}

        {loading ? (
          <ContentCard>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
              Loading ministries…
            </div>
          </ContentCard>
        ) : isAdmin ? (
          <ContentCard className="overflow-hidden p-0">
            <div className="border-b border-slate-100 bg-slate-50/80 px-4 py-3">
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{total}</span> ministry
                {total === 1 ? "" : "ies"}
              </p>
            </div>
            <ul className="divide-y divide-slate-100 bg-white">
              {adminItems.length === 0 ? (
                <li className="px-4 py-8 text-center text-sm text-slate-600">No ministries match.</li>
              ) : (
                adminItems.map((m) => (
                  <li key={m.id} className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <Link
                        href={`/ministries/${m.id}`}
                        className="font-medium text-slate-900 underline-offset-2 hover:underline"
                      >
                        {m.name}
                      </Link>
                      {!m.is_active ? (
                        <span className="ml-2 rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-700">
                          Inactive
                        </span>
                      ) : null}
                      <p className="truncate text-xs text-slate-500">
                        {m.active_member_count} active member{m.active_member_count === 1 ? "" : "s"}
                      </p>
                    </div>
                    <Link
                      href={`/ministries/${m.id}`}
                      className="shrink-0 text-sm font-medium text-slate-700 hover:text-slate-900"
                    >
                      Open →
                    </Link>
                  </li>
                ))
              )}
            </ul>
            {total > pageSize ? (
              <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasNextPage}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            ) : null}
          </ContentCard>
        ) : (
          <ContentCard className="overflow-hidden p-0">
            <ul className="divide-y divide-slate-100 bg-white">
              {myItems.length === 0 ? (
                <li className="px-4 py-8 text-center text-sm text-slate-600">
                  You are not in any ministries yet.
                </li>
              ) : (
                myItems.map((m) => (
                  <li key={m.membership_id} className="px-4 py-3">
                    <Link
                      href={`/ministries/${m.ministry_id}`}
                      className="font-medium text-slate-900 underline-offset-2 hover:underline"
                    >
                      {m.name}
                    </Link>
                    <p className="mt-1 text-xs capitalize text-slate-600">
                      Your role: {m.role_in_ministry.replace("_", " ")}
                      {!m.ministry_is_active ? (
                        <span className="ml-2 text-amber-700">(ministry inactive)</span>
                      ) : null}
                    </p>
                  </li>
                ))
              )}
            </ul>
          </ContentCard>
        )}
      </div>
    </PageShell>
  );
}
