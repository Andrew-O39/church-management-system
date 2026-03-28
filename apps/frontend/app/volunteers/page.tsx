"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { useAuth } from "components/providers/AuthProvider";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { apiFetch } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { fetchAllListPages } from "lib/api-pagination";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import { getAccessToken } from "lib/session";
import type {
  MinistryListResponse,
  MyVolunteerAssignmentsResponse,
  VolunteerRoleListItem,
  VolunteerRoleListResponse,
} from "lib/types";

const inputCls =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400";

function formatDateTime(iso: string) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

export default function VolunteersPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [myAssignments, setMyAssignments] = useState<MyVolunteerAssignmentsResponse["items"]>([]);

  const [roleItems, setRoleItems] = useState<VolunteerRoleListResponse["items"]>([]);
  const [rolesTotal, setRolesTotal] = useState(0);
  const [rolePage, setRolePage] = useState(1);
  const rolePageSize = 20;
  const [showInactiveRoles, setShowInactiveRoles] = useState(false);
  const [ministries, setMinistries] = useState<MinistryListResponse["items"]>([]);

  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleDesc, setNewRoleDesc] = useState("");
  const [newRoleMinistryId, setNewRoleMinistryId] = useState<string>("none");
  const [creatingRole, setCreatingRole] = useState(false);
  const [roleMutationError, setRoleMutationError] = useState<string | null>(null);

  const [editingRoleId, setEditingRoleId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editMinistryId, setEditMinistryId] = useState<string>("none");
  const [editSaving, setEditSaving] = useState(false);

  const load = useCallback(async () => {
    if (!token || status !== "authenticated") {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const mine = await apiFetch<MyVolunteerAssignmentsResponse>("/api/v1/volunteers/me", {
        method: "GET",
        token,
      });
      setMyAssignments(mine.items);

      if (isAdmin) {
        const params = new URLSearchParams({
          page: String(rolePage),
          page_size: String(rolePageSize),
        });
        if (!showInactiveRoles) params.set("is_active", "true");
        const roles = await apiFetch<VolunteerRoleListResponse>(
          `/api/v1/volunteers/roles?${params.toString()}`,
          { method: "GET", token },
        );
        setRoleItems(roles.items);
        setRolesTotal(roles.total);

        const mins = await fetchAllListPages({
          fetchPage: async (page, pageSize) => {
            const qs = new URLSearchParams({
              is_active: "true",
              page: String(page),
              page_size: String(pageSize),
            });
            return apiFetch<MinistryListResponse>(`/api/v1/ministries/?${qs.toString()}`, {
              method: "GET",
              token,
            });
          },
        });
        setMinistries(mins);
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
  }, [token, status, isAdmin, rolePage, rolePageSize, showInactiveRoles, router]);

  useEffect(() => {
    if (status === "loading") return;
    void load();
  }, [load, status]);

  function openEdit(role: VolunteerRoleListItem) {
    setRoleMutationError(null);
    setEditingRoleId(role.id);
    setEditName(role.name);
    setEditDesc(role.description ?? "");
    setEditMinistryId(role.ministry_id ?? "none");
  }

  function cancelEdit() {
    setEditingRoleId(null);
    setEditSaving(false);
  }

  async function onSaveEdit(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !editingRoleId || !editName.trim()) return;
    setEditSaving(true);
    setRoleMutationError(null);
    try {
      await apiFetch(`/api/v1/volunteers/roles/${editingRoleId}`, {
        method: "PATCH",
        token,
        body: {
          name: editName.trim(),
          description: editDesc.trim() || null,
          ministry_id: editMinistryId === "none" ? null : editMinistryId,
        },
      });
      cancelEdit();
      await load();
    } catch (err) {
      setRoleMutationError(toErrorMessage(err));
    } finally {
      setEditSaving(false);
    }
  }

  async function onToggleRoleActive(role: VolunteerRoleListItem, nextActive: boolean) {
    if (!token || !isAdmin) return;
    const msg = nextActive
      ? `Reactivate volunteer role "${role.name}"? It will be available for new assignments again.`
      : `Deactivate volunteer role "${role.name}"? It will no longer be available for new assignments (existing assignments stay as-is).`;
    if (!window.confirm(msg)) return;
    setRoleMutationError(null);
    try {
      await apiFetch(`/api/v1/volunteers/roles/${role.id}`, {
        method: "PATCH",
        token,
        body: { is_active: nextActive },
      });
      if (editingRoleId === role.id) cancelEdit();
      await load();
    } catch (err) {
      setRoleMutationError(toErrorMessage(err));
    }
  }

  async function onCreateRole(e: FormEvent) {
    e.preventDefault();
    if (!token || !isAdmin || !newRoleName.trim()) return;
    setCreatingRole(true);
    setRoleMutationError(null);
    try {
      await apiFetch("/api/v1/volunteers/roles", {
        method: "POST",
        token,
        body: {
          name: newRoleName.trim(),
          description: newRoleDesc.trim() || null,
          ministry_id: newRoleMinistryId === "none" ? null : newRoleMinistryId,
          is_active: true,
        },
      });
      setNewRoleName("");
      setNewRoleDesc("");
      setNewRoleMinistryId("none");
      await load();
    } catch (err) {
      setRoleMutationError(toErrorMessage(err));
    } finally {
      setCreatingRole(false);
    }
  }

  if (status === "loading" || loading) {
    return (
      <PageShell title="Volunteers" description="Loading…">
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  const roleTotalPages = Math.max(1, Math.ceil(rolesTotal / rolePageSize));

  return (
    <PageShell
      title="Volunteers"
      description={isAdmin ? "Your assignments and church-wide volunteer roles" : "Your volunteer assignments"}
    >
      <div className="space-y-4">
        {error ? (
          <ContentCard>
            <p className="text-sm text-red-800">{error}</p>
          </ContentCard>
        ) : null}

        <ContentCard className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-900">My assignments</h2>
          {myAssignments.length === 0 ? (
            <p className="text-sm text-slate-600">You have no volunteer assignments on upcoming or past visible events.</p>
          ) : (
            <ul className="space-y-3">
              {myAssignments.map((a) => (
                <li
                  key={a.assignment_id}
                  className="rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2 text-sm"
                >
                  <Link
                    href={`/events/${a.event_id}`}
                    className="font-medium text-slate-900 underline-offset-2 hover:underline"
                  >
                    {a.event_title}
                  </Link>
                  <p className="text-slate-600">
                    {formatDateTime(a.start_at)} · {a.location}
                  </p>
                  <p className="text-slate-800">
                    Role: <span className="font-medium">{a.role_name}</span>
                  </p>
                  {a.notes ? <p className="text-xs text-slate-600">Note: {a.notes}</p> : null}
                </li>
              ))}
            </ul>
          )}
        </ContentCard>

        {isAdmin ? (
          <ContentCard className="space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">Volunteer roles (admin)</h2>
            <p className="text-xs text-slate-600">
              Church-wide roles apply to any event. Ministry-scoped roles can only be used on events for that same
              ministry.
            </p>

            <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={showInactiveRoles}
                onChange={(e) => {
                  setShowInactiveRoles(e.target.checked);
                  setRolePage(1);
                }}
                className="rounded border-slate-300"
              />
              Show inactive roles
            </label>

            {roleMutationError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                {roleMutationError}
              </div>
            ) : null}

            <form onSubmit={onCreateRole} className="space-y-3 rounded-lg border border-slate-100 bg-white p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">New role</p>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">Name</label>
                  <input
                    value={newRoleName}
                    onChange={(e) => setNewRoleName(e.target.value)}
                    className={inputCls}
                    placeholder="e.g. Usher, Lector"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">Ministry (optional)</label>
                  <select
                    value={newRoleMinistryId}
                    onChange={(e) => setNewRoleMinistryId(e.target.value)}
                    className={inputCls}
                  >
                    <option value="none">Church-wide role</option>
                    {ministries.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700">Description (optional)</label>
                <input
                  value={newRoleDesc}
                  onChange={(e) => setNewRoleDesc(e.target.value)}
                  className={inputCls}
                  placeholder="Short description"
                />
              </div>
              <button
                type="submit"
                disabled={creatingRole || !newRoleName.trim()}
                className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
              >
                {creatingRole ? "Creating…" : "Create role"}
              </button>
            </form>

            {editingRoleId ? (
              <form
                onSubmit={onSaveEdit}
                className="space-y-3 rounded-lg border border-amber-200 bg-amber-50/40 p-3"
              >
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Edit role</p>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-700">Name</label>
                    <input value={editName} onChange={(e) => setEditName(e.target.value)} className={inputCls} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-700">Ministry</label>
                    <select
                      value={editMinistryId}
                      onChange={(e) => setEditMinistryId(e.target.value)}
                      className={inputCls}
                    >
                      <option value="none">Church-wide</option>
                      {ministries.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700">Description</label>
                  <input value={editDesc} onChange={(e) => setEditDesc(e.target.value)} className={inputCls} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="submit"
                    disabled={editSaving || !editName.trim()}
                    className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
                  >
                    {editSaving ? "Saving…" : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}

            {roleItems.length === 0 ? (
              <p className="text-sm text-slate-600">No roles yet. Create one above or from event scheduling.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-slate-100 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-2 py-2">Name</th>
                      <th className="px-2 py-2">Scope</th>
                      <th className="px-2 py-2">Description</th>
                      <th className="px-2 py-2">Status</th>
                      <th className="px-2 py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {roleItems.map((r) => (
                      <tr key={r.id} className={!r.is_active ? "bg-slate-50/80" : undefined}>
                        <td className="px-2 py-2 font-medium text-slate-900">{r.name}</td>
                        <td className="px-2 py-2 text-slate-700">
                          {r.ministry_name ? r.ministry_name : "Church-wide"}
                        </td>
                        <td className="px-2 py-2 text-slate-600">{r.description ?? "—"}</td>
                        <td className="px-2 py-2">
                          {r.is_active ? (
                            <span className="text-xs font-medium text-green-800">Active</span>
                          ) : (
                            <span className="text-xs font-medium text-slate-500">Inactive</span>
                          )}
                        </td>
                        <td className="px-2 py-2">
                          <div className="flex flex-wrap gap-1">
                            <button
                              type="button"
                              onClick={() => openEdit(r)}
                              disabled={editingRoleId !== null && editingRoleId !== r.id}
                              className="rounded border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-50"
                            >
                              Edit
                            </button>
                            {r.is_active ? (
                              <button
                                type="button"
                                onClick={() => void onToggleRoleActive(r, false)}
                                className="rounded border border-amber-200 bg-white px-2 py-0.5 text-xs font-medium text-amber-900 hover:bg-amber-50"
                              >
                                Deactivate
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={() => void onToggleRoleActive(r, true)}
                                className="rounded border border-green-200 bg-white px-2 py-0.5 text-xs font-medium text-green-900 hover:bg-green-50"
                              >
                                Reactivate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {rolesTotal > rolePageSize ? (
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <button
                  type="button"
                  disabled={rolePage <= 1}
                  onClick={() => setRolePage((p) => Math.max(1, p - 1))}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1 disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-slate-600">
                  Page {rolePage} / {roleTotalPages}
                </span>
                <button
                  type="button"
                  disabled={rolePage >= roleTotalPages}
                  onClick={() => setRolePage((p) => p + 1)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            ) : null}
          </ContentCard>
        ) : null}
      </div>
    </PageShell>
  );
}
