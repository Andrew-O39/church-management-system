"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "lib/api";
import type { MemberDetailResponse, PreferredChannel } from "lib/types";
import { getAccessToken } from "lib/session";
import type { MemberSelfPatch } from "lib/types";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import PageShell, { ContentCard } from "components/layout/PageShell";
import {
  btnPrimary,
  fieldInput,
  fieldLabel,
  fieldTextarea,
  surfaceError,
  surfaceSuccess,
  surfaceWarning,
} from "lib/ui";

function optString(v: string) {
  const s = v.trim();
  return s === "" ? null : s;
}

function AdminDirectoryNotice() {
  const params = useSearchParams();
  if (params.get("notice") !== "admin_only") return null;
  return (
    <div className={"mb-4 " + surfaceWarning}>
      Parish registry and app user management are limited to administrators. You can still update your profile below.
    </div>
  );
}

function ProfilePageContent() {
  const router = useRouter();
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [data, setData] = useState<MemberDetailResponse | null>(null);

  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [address, setAddress] = useState("");
  const [whatsappEnabled, setWhatsappEnabled] = useState(true);
  const [smsEnabled, setSmsEnabled] = useState(true);
  const [preferredChannel, setPreferredChannel] = useState<PreferredChannel>("whatsapp");

  useEffect(() => {
    if (!token) {
      setError("You need to sign in to view this page.");
      setLoading(false);
      return;
    }

    apiFetch<MemberDetailResponse>("/api/v1/members/me/profile", {
      method: "GET",
      token,
    })
      .then((res) => {
        setData(res);
        setFullName(res.full_name);
        setPhoneNumber(res.profile.phone_number ?? "");
        setContactEmail(res.profile.contact_email ?? "");
        setAddress(res.profile.address ?? "");
        setWhatsappEnabled(res.profile.whatsapp_enabled);
        setSmsEnabled(res.profile.sms_enabled);
        setPreferredChannel(res.profile.preferred_channel);
      })
      .catch((err) => {
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
      .finally(() => setLoading(false));
  }, [router, token]);

  const canSubmit = useMemo(() => !submitting && fullName.trim().length > 0, [fullName, submitting]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    const payload: MemberSelfPatch = {
      full_name: fullName.trim(),
      phone_number: optString(phoneNumber),
      contact_email: optString(contactEmail),
      address: optString(address),
      whatsapp_enabled: whatsappEnabled,
      sms_enabled: smsEnabled,
      preferred_channel: preferredChannel,
    };

    try {
      const updated = await apiFetch<MemberDetailResponse>(
        "/api/v1/members/me/profile",
        { method: "PATCH", body: payload, token },
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
      title="Your profile"
      description="Update your app profile and contact preferences. Official parish sacramental records are maintained separately by parish staff."
    >
      <AdminDirectoryNotice />

      {loading ? (
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
            Loading your profile…
          </div>
        </ContentCard>
      ) : null}

      {!loading && error && !data ? <div className={surfaceError}>{error}</div> : null}

      {!loading && data ? (
        <ContentCard>
          {success ? <div className={"mb-4 " + surfaceSuccess}>Your changes were saved.</div> : null}

          {error ? <div className={"mb-4 " + surfaceError}>{error}</div> : null}

          <form onSubmit={onSubmit} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="pf-name" className={fieldLabel}>
                  Full name
                </label>
                <input
                  id="pf-name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className={fieldInput}
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="pf-login-email" className={fieldLabel}>
                  Login email
                </label>
                <input
                  id="pf-login-email"
                  value={data.email}
                  disabled
                  className="w-full cursor-not-allowed rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm text-slate-600"
                />
                <p className="text-xs text-slate-500">
                  To change your login email, ask an administrator.
                </p>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="pf-phone" className={fieldLabel}>
                  Phone number
                </label>
                <input
                  id="pf-phone"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className={fieldInput}
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="pf-contact-email" className={fieldLabel}>
                  Directory contact email{" "}
                  <span className="font-normal text-slate-500">(optional)</span>
                </label>
                <input
                  id="pf-contact-email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  type="email"
                  className={fieldInput}
                />
                <p className="text-xs text-slate-500">
                  Optional contact email for ministries and events if different from your login email.
                </p>
              </div>

              <div className="space-y-1.5 md:col-span-2">
                <label htmlFor="pf-address" className={fieldLabel}>
                  Address
                </label>
                <textarea
                  id="pf-address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className={fieldTextarea}
                />
              </div>
            </div>

            <div className="border-t border-slate-100 pt-6">
              <h2 className="shepherd-section-title mb-3">Notifications</h2>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2 md:col-span-2">
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
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="pf-channel" className={fieldLabel}>
                    Preferred channel
                  </label>
                  <select
                    id="pf-channel"
                    value={preferredChannel}
                    onChange={(e) => setPreferredChannel(e.target.value as PreferredChannel)}
                    className={fieldInput}
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
            </div>
          </form>
        </ContentCard>
      ) : null}
    </PageShell>
  );
}

export default function ProfilePage() {
  return (
    <Suspense
      fallback={
        <PageShell
          title="Your profile"
          description="Update your app profile and contact preferences. Official parish sacramental records are maintained separately by parish staff."
        >
          <ContentCard>
            <p className="text-sm text-slate-600">Loading…</p>
          </ContentCard>
        </PageShell>
      }
    >
      <ProfilePageContent />
    </Suspense>
  );
}
