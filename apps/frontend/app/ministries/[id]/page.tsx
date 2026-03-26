"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type {
  MemberListResponse,
  MinistryDetailResponse,
  MinistryMemberRow,
  MinistryRoleInMinistry,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";

const inputCls =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400";

const ROLE_OPTIONS: MinistryRoleInMinistry[] = ["member", "leader", "coordinator"];

function formatRole(r: string) {
  return r.split("_").join(" ");
}

export default function MinistryDetailPage({ params }: { params: { id: string } }) {
  const ministryId = params.id;
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<MinistryDetailResponse | null>(null);

  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editActive, setEditActive] = useState(true);
  const [savingMinistry, setSavingMinistry] = useState(false);

  const [addEmail, setAddEmail] = useState("");
  const [addRole, setAddRole] = useState<MinistryRoleInMinistry>("member");
  const [adding, setAdding] = useState(false);

  const [memberSearch, setMemberSearch] = useState("");
  const [searchHits, setSearchHits] = useState<MemberListResponse["items"]>([]);
  const [searching, setSearching] = useState(false);

  const load = useCallback(async () => {
    if (!token || status !== "authenticated") {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const d = await apiFetch<MinistryDetailResponse>(`/api/v1/ministries/${ministryId}`, {
        method: "GET",
        token,
      });
      setDetail(d);
      setEditName(d.name);
      setEditDesc(d.description ?? "");
      setEditActive(d.is_active);
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
  }, [token, status, ministryId, router]);

  useEffect(() => {
    if (status === "loading") return;
    void load();
  }, [load, status]);

  async function searchDirectory(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !memberSearch.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("search", memberSearch.trim());
      params.set("page", "1");
      params.set("page_size", "10");
      const res = await apiFetch<MemberListResponse>(`/api/v1/members/?${params}`, {
        method: "GET",
        token,
      });
      setSearchHits(res.items);
    } catch (err) {
      setError(toErrorMessage(err));
      setSearchHits([]);
    } finally {
      setSearching(false);
    }
  }

  async function onSaveMinistry(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !detail) return;
    setSavingMinistry(true);
    setError(null);
    try {
      const d = await apiFetch<MinistryDetailResponse>(`/api/v1/ministries/${ministryId}`, {
        method: "PATCH",
        token,
        body: {
          name: editName.trim(),
          description: editDesc.trim() || null,
          is_active: editActive,
        },
      });
      setDetail(d);
      setEditName(d.name);
      setEditDesc(d.description ?? "");
      setEditActive(d.is_active);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setSavingMinistry(false);
    }
  }

  async function onAddMember(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !addEmail.trim()) return;
    setAdding(true);
    setError(null);
    try {
      await apiFetch(`/api/v1/ministries/${ministryId}/members`, {
        method: "POST",
        token,
        body: { email: addEmail.trim(), role_in_ministry: addRole },
      });
      setAddEmail("");
      await load();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setAdding(false);
    }
  }

  async function quickAddUserId(userId: string) {
    if (!token || !isAdmin) return;
    setError(null);
    try {
      await apiFetch(`/api/v1/ministries/${ministryId}/members`, {
        method: "POST",
        token,
        body: { user_id: userId, role_in_ministry: addRole },
      });
      await load();
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  async function patchMembership(userId: string, patch: { role_in_ministry?: MinistryRoleInMinistry; is_active?: boolean }) {
    if (!token || !isAdmin) return;
    setError(null);
    try {
      await apiFetch(`/api/v1/ministries/${ministryId}/members/${userId}`, {
        method: "PATCH",
        token,
        body: patch,
      });
      await load();
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  async function removeMember(userId: string) {
    if (!token || !isAdmin) return;
    setError(null);
    try {
      await apiFetch(`/api/v1/ministries/${ministryId}/members/${userId}`, {
        method: "DELETE",
        token,
      });
      await load();
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  const myMembership = useMemo(() => {
    if (!detail || isAdmin) return null;
    return detail.members[0] ?? null;
  }, [detail, isAdmin]);

  if (status === "loading" || loading) {
    return (
      <PageShell title="Ministry" description="Loading…">
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (error && !detail) {
    return (
      <PageShell title="Ministry" description="Ministry details">
        <ContentCard>
          <p className="text-sm text-red-800">{error}</p>
          <Link href="/ministries" className="mt-4 inline-block text-sm font-medium text-slate-800 underline">
            ← Back to ministries
          </Link>
        </ContentCard>
      </PageShell>
    );
  }

  if (!detail) {
    return null;
  }

  return (
    <PageShell title={detail.name} description="Ministry / group details and membership.">
      <div className="mb-4">
        <Link href="/ministries" className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline">
          ← All ministries
        </Link>
      </div>

      {error ? (
        <ContentCard className="mb-4">
          <p className="text-sm text-red-800">{error}</p>
        </ContentCard>
      ) : null}

      {!isAdmin && myMembership ? (
        <ContentCard className="mb-4">
          <p className="text-sm text-slate-700">
            You are a <span className="font-medium capitalize">{formatRole(myMembership.role_in_ministry)}</span> in
            this ministry{!detail.is_active ? " (this ministry is currently inactive)." : "."}
          </p>
        </ContentCard>
      ) : null}

      {isAdmin ? (
        <ContentCard className="mb-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-900">Edit ministry</h2>
          <form onSubmit={onSaveMinistry} className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Name</label>
                <input value={editName} onChange={(e) => setEditName(e.target.value)} className={inputCls} />
              </div>
              <label className="flex items-center gap-2 pt-6 md:pt-0">
                <input
                  type="checkbox"
                  checked={editActive}
                  onChange={(e) => setEditActive(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Ministry active</span>
              </label>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-800">Description</label>
              <textarea
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                className={`${inputCls} min-h-[88px] resize-y`}
              />
            </div>
            <button
              type="submit"
              disabled={savingMinistry || !editName.trim()}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-60"
            >
              {savingMinistry ? "Saving…" : "Save changes"}
            </button>
          </form>
          {!detail.is_active ? (
            <p className="text-xs text-amber-800">
              This ministry is inactive: you can still update memberships for cleanup, but new members cannot be added
              until the ministry is active again.
            </p>
          ) : null}
        </ContentCard>
      ) : null}

      {isAdmin ? (
        <ContentCard className="mb-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-900">Add member</h2>
          <form onSubmit={onAddMember} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="min-w-0 flex-1 space-y-1.5">
              <label className="text-sm font-medium text-slate-800">Email</label>
              <input
                type="email"
                value={addEmail}
                onChange={(e) => setAddEmail(e.target.value)}
                className={inputCls}
                placeholder="member@parish.org"
                disabled={!detail.is_active}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-800">Role in ministry</label>
              <select
                value={addRole}
                onChange={(e) => setAddRole(e.target.value as MinistryRoleInMinistry)}
                className={inputCls}
              >
                {ROLE_OPTIONS.map((r) => (
                  <option key={r} value={r}>
                    {formatRole(r)}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              disabled={adding || !addEmail.trim() || !detail.is_active}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-60"
            >
              {adding ? "Adding…" : "Add"}
            </button>
          </form>

          <div className="border-t border-slate-100 pt-4">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Directory lookup</h3>
            <form onSubmit={searchDirectory} className="mt-2 flex flex-wrap gap-2">
              <input
                value={memberSearch}
                onChange={(e) => setMemberSearch(e.target.value)}
                className={`${inputCls} max-w-md`}
                placeholder="Search members by name or email"
              />
              <button
                type="submit"
                disabled={searching}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800"
              >
                {searching ? "Searching…" : "Search"}
              </button>
            </form>
            {searchHits.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {searchHits.map((h) => (
                  <li
                    key={h.member_id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50/50 px-3 py-2 text-sm"
                  >
                    <span>
                      {h.full_name} · {h.email}
                    </span>
                    <button
                      type="button"
                      onClick={() => quickAddUserId(h.member_id)}
                      disabled={!detail.is_active}
                      className="text-slate-900 underline disabled:opacity-50"
                    >
                      Add to ministry
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </ContentCard>
      ) : null}

      <ContentCard className="overflow-hidden p-0">
        <div className="border-b border-slate-100 bg-slate-50/80 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-900">
            {isAdmin ? "Members" : "Your membership"}
          </h2>
          {!isAdmin ? (
            <p className="text-xs text-slate-500">Other members are not shown on this page.</p>
          ) : null}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                {isAdmin ? <th className="px-4 py-3">Actions</th> : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {detail.members.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 5 : 4} className="px-4 py-8 text-center text-slate-600">
                    No members yet.
                  </td>
                </tr>
              ) : (
                detail.members.map((m: MinistryMemberRow) => (
                  <tr key={m.membership_id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{m.full_name}</td>
                    <td className="px-4 py-3 text-slate-700">{m.email}</td>
                    <td className="px-4 py-3">
                      {isAdmin ? (
                        <select
                          value={m.role_in_ministry}
                          onChange={(e) =>
                            patchMembership(m.user_id, {
                              role_in_ministry: e.target.value as MinistryRoleInMinistry,
                            })
                          }
                          className={`${inputCls} !py-1`}
                        >
                          {ROLE_OPTIONS.map((r) => (
                            <option key={r} value={r}>
                              {formatRole(r)}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span className="capitalize">{formatRole(m.role_in_ministry)}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">{m.is_active ? "Active" : "Removed"}</td>
                    {isAdmin ? (
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          {m.is_active ? (
                            <button
                              type="button"
                              onClick={() => removeMember(m.user_id)}
                              className="text-xs font-medium text-red-700 underline"
                            >
                              Remove
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => patchMembership(m.user_id, { is_active: true })}
                              className="text-xs font-medium text-slate-800 underline"
                            >
                              Reactivate
                            </button>
                          )}
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </ContentCard>
    </PageShell>
  );
}
