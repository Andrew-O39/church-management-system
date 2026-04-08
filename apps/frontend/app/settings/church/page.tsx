"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import PageShell, { ContentCard } from "components/layout/PageShell";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { clearSessionAndRedirect } from "lib/auth";
import { getAccessToken } from "lib/session";
import { isInactiveAccountError, isUnauthorized, toErrorMessage } from "lib/errors";
import type { ChurchProfileResponse, ChurchProfileUpdateRequest } from "lib/types";
import { btnPrimary, fieldInput, fieldLabel, fieldTextarea, surfaceError, surfaceInfo } from "lib/ui";

export default function ChurchSettingsPage() {
  const router = useRouter();
  const { isAdmin, status } = useAuth();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    church_name: "",
    short_name: "",
    address: "",
    phone: "",
    email: "",
  });

  const load = useCallback(async () => {
    if (!token || status !== "authenticated" || !isAdmin) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const p = await apiFetch<ChurchProfileResponse>("/api/v1/church-profile/", {
        method: "GET",
        token,
      });
      setForm({
        church_name: p.church_name ?? "",
        short_name: p.short_name ?? "",
        address: p.address ?? "",
        phone: p.phone ?? "",
        email: p.email ?? "",
      });
    } catch (e: unknown) {
      if (isUnauthorized(e)) {
        clearSessionAndRedirect(router);
        return;
      }
      if (isInactiveAccountError(e)) {
        clearSessionAndRedirect(router, "account_inactive");
        return;
      }
      setError(toErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [token, status, isAdmin, router]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (status === "authenticated" && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, isAdmin, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    const name = form.church_name.trim();
    if (!name) {
      setError("Church name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    const body: ChurchProfileUpdateRequest = {
      church_name: name,
      short_name: form.short_name.trim() || null,
      address: form.address.trim() || null,
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
    };
    try {
      await apiFetch<ChurchProfileResponse>("/api/v1/church-profile/", {
        method: "PUT",
        body,
        token,
      });
      await load();
    } catch (err: unknown) {
      if (isUnauthorized(err)) {
        clearSessionAndRedirect(router);
        return;
      }
      if (isInactiveAccountError(err)) {
        clearSessionAndRedirect(router, "account_inactive");
        return;
      }
      setError(toErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (!token || status === "unauthenticated") {
    return (
      <PageShell title="Church settings" description="Sign in to continue.">
        <ContentCard>
          <p className="text-slate-600">This page requires a signed-in administrator.</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (status === "loading") {
    return (
      <PageShell title="Church settings" description="Loading…">
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      </PageShell>
    );
  }

  if (!isAdmin) {
    return (
      <PageShell title="Church settings" description="Redirecting…">
        <ContentCard>
          <p className="text-sm text-slate-600">Administrators only.</p>
        </ContentCard>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Church settings"
      description="Organization name and contact details used in exports and print views. This is not parish registry data."
    >
      <div className={surfaceInfo + " mb-6"}>
        One profile for the whole app. Information here appears on printable exports (and in CSV filenames when saved from the browser).
      </div>

      {error ? <div className={`${surfaceError} mb-6`}>{error}</div> : null}

      <ContentCard>
        {loading ? (
          <p className="text-sm text-slate-600">Loading profile…</p>
        ) : (
          <form onSubmit={(e) => void onSubmit(e)} className="space-y-4">
            <div>
              <label className={fieldLabel} htmlFor="church_name">
                Church name <span className="text-red-600">*</span>
              </label>
              <input
                id="church_name"
                className={`${fieldInput} mt-1`}
                value={form.church_name}
                onChange={(e) => setForm({ ...form, church_name: e.target.value })}
                required
                autoComplete="organization"
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="short_name">
                Short name (optional)
              </label>
              <input
                id="short_name"
                className={`${fieldInput} mt-1`}
                value={form.short_name}
                onChange={(e) => setForm({ ...form, short_name: e.target.value })}
                placeholder="e.g. initials or common name"
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="address">
                Address (optional)
              </label>
              <textarea
                id="address"
                className={`${fieldTextarea} mt-1`}
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="phone">
                Phone (optional)
              </label>
              <input
                id="phone"
                type="tel"
                className={`${fieldInput} mt-1`}
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div>
              <label className={fieldLabel} htmlFor="email">
                Email (optional)
              </label>
              <input
                id="email"
                type="email"
                className={`${fieldInput} mt-1`}
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="pt-2">
              <button type="submit" className={btnPrimary} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </button>
            </div>
          </form>
        )}
      </ContentCard>
    </PageShell>
  );
}
