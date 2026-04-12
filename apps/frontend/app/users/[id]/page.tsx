"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type { MemberAdminPatch, MemberDetailResponse, PreferredChannel, UserRole } from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { btnPrimary, fieldInput, fieldLabel, fieldTextarea, surfaceError, surfaceSuccess } from "lib/ui";

const inputCls = fieldInput;

function optString(v: string) {
  const s = v.trim();
  return s === "" ? null : s;
}

function roleLabel(r: UserRole): string {
  switch (r) {
    case "admin":
      return "Administrator access (full church settings & registry)";
    case "group_leader":
      return "Group leader";
    default:
      return "Member";
  }
}

export default function AppUserDetailPage({ params }: { params: { id: string } }) {
  const userId = params.id;
  const router = useRouter();
  const token = getAccessToken();
  const { user, status, isAdmin } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [data, setData] = useState<MemberDetailResponse | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [role, setRole] = useState<UserRole>("member");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [address, setAddress] = useState("");
  const [whatsappEnabled, setWhatsappEnabled] = useState(true);
  const [smsEnabled, setSmsEnabled] = useState(true);
  const [preferredChannel, setPreferredChannel] = useState<PreferredChannel>("whatsapp");

  useEffect(() => {
    if (status === "authenticated" && user && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, user, isAdmin, router]);

  useEffect(() => {
    if (status === "loading") return;
    if (!token || status !== "authenticated" || !isAdmin) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    apiFetch<MemberDetailResponse>(`/api/v1/members/${encodeURIComponent(userId)}`, {
      method: "GET",
      token,
    })
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setFullName(res.full_name);
        setEmail(res.email);
        setIsActive(res.is_active);
        setRole(res.role);
        setPhoneNumber(res.profile.phone_number ?? "");
        setContactEmail(res.profile.contact_email ?? "");
        setAddress(res.profile.address ?? "");
        setWhatsappEnabled(res.profile.whatsapp_enabled);
        setSmsEnabled(res.profile.sms_enabled);
        setPreferredChannel(res.profile.preferred_channel);
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
        setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, status, userId, isAdmin, router]);

  const canSubmit = useMemo(
    () => !submitting && fullName.trim().length > 0 && email.trim().length > 0,
    [fullName, email, submitting],
  );

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !canSubmit) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    const patch: MemberAdminPatch = {
      full_name: fullName.trim(),
      email: email.trim(),
      is_active: isActive,
      role,
      phone_number: optString(phoneNumber),
      contact_email: optString(contactEmail),
      address: optString(address),
      whatsapp_enabled: whatsappEnabled,
      sms_enabled: smsEnabled,
      preferred_channel: preferredChannel,
    };

    try {
      const updated = await apiFetch<MemberDetailResponse>(
        `/api/v1/members/${encodeURIComponent(userId)}`,
        { method: "PATCH", body: patch, token },
      );
      setData(updated);
      setSuccess(true);
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
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="App user"
      description={
        <>
          <Link href="/users" className="text-slate-600 underline-offset-2 hover:underline">
            ← App users
          </Link>
          <span className="text-slate-400"> · </span>
          <span className="text-slate-600">
            Manage login account and app profile. Parish sacramental records live under{" "}
            <Link href="/members" className="font-medium text-slate-900 underline-offset-2 hover:underline">
              Parish registry
            </Link>
            .
          </span>
        </>
      }
    >
      {loading ? (
        <ContentCard>
          <p className="text-sm text-slate-600">Loading…</p>
        </ContentCard>
      ) : null}

      {!loading && error && !data ? <div className={surfaceError}>{error}</div> : null}

      {!loading && data ? (
        <ContentCard>
          {success ? <div className={"mb-4 " + surfaceSuccess}>Changes saved.</div> : null}
          {error ? <div className={"mb-4 " + surfaceError}>{error}</div> : null}

          <form onSubmit={onSubmit} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <label className={fieldLabel}>Full name</label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className={inputCls}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Login email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputCls}
                  required
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className={fieldLabel}>Role / access level</label>
                <p className="mb-2 text-xs text-slate-600">
                  Parishes can have several administrators—each person should use their own login. Use{" "}
                  <strong>Promote</strong> (choose Administrator access) or <strong>Remove admin access</strong> (choose
                  Member or Group leader) as needed. Shepherd blocks changes that would leave no active administrator.
                </p>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className={inputCls}
                  aria-describedby="role-help"
                >
                  <option value="member">Member</option>
                  <option value="group_leader">Group leader</option>
                  <option value="admin">Administrator access — full parish tools</option>
                </select>
                <p id="role-help" className="mt-1.5 text-xs text-slate-500">
                  Current: <span className="font-medium text-slate-700">{roleLabel(data.role)}</span>
                </p>
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className={fieldLabel}>Account status</label>
                <label className="flex items-center gap-2 text-sm text-slate-800">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="rounded border-slate-300"
                  />
                  Active (can sign in)
                </label>
                <p className="mt-1 text-xs text-slate-500">
                  Deactivating the only remaining active administrator is blocked; you will see the server message if that
                  applies.
                </p>
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Phone</label>
                <input
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className={fieldLabel}>Contact email (optional)</label>
                <input
                  type="email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className={fieldLabel}>Address</label>
                <textarea value={address} onChange={(e) => setAddress(e.target.value)} className={fieldTextarea} />
              </div>
            </div>

            <div className="border-t border-slate-100 pt-6">
              <h2 className="shepherd-section-title mb-3">Notifications</h2>
              <div className="grid gap-4 md:grid-cols-3">
                <label className="flex items-center gap-3 rounded-lg border border-slate-300/90 bg-white px-3 py-2.5 shadow-sm shadow-slate-900/[0.03]">
                  <input
                    type="checkbox"
                    checked={whatsappEnabled}
                    onChange={(e) => setWhatsappEnabled(e.target.checked)}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm font-semibold text-slate-900">WhatsApp</span>
                </label>
                <label className="flex items-center gap-3 rounded-lg border border-slate-300/90 bg-white px-3 py-2.5 shadow-sm shadow-slate-900/[0.03]">
                  <input
                    type="checkbox"
                    checked={smsEnabled}
                    onChange={(e) => setSmsEnabled(e.target.checked)}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm font-semibold text-slate-900">SMS</span>
                </label>
                <div className="space-y-1.5">
                  <label className={fieldLabel}>Preferred channel</label>
                  <select
                    value={preferredChannel}
                    onChange={(e) => setPreferredChannel(e.target.value as PreferredChannel)}
                    className={inputCls}
                  >
                    <option value="whatsapp">WhatsApp</option>
                    <option value="sms">SMS</option>
                    <option value="email">Email</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 pt-6">
              <button type="submit" disabled={!canSubmit} className={btnPrimary}>
                {submitting ? "Saving…" : "Save changes"}
              </button>
              <span className="text-xs text-slate-500">
                Saved access: <span className="font-medium text-slate-700">{roleLabel(data.role)}</span>
              </span>
            </div>
          </form>
        </ContentCard>
      ) : null}
    </PageShell>
  );
}
