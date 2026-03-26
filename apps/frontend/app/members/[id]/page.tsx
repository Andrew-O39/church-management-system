"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import { toErrorMessage, isUnauthorized, isInactiveAccountError } from "lib/errors";
import type {
  MemberAdminPatch,
  MemberDetailResponse,
  MaritalStatus,
  PreferredChannel,
  UserRole,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";

function optString(v: string) {
  const s = v.trim();
  return s === "" ? null : s;
}

function optDate(v: string) {
  const s = v.trim();
  return s === "" ? null : s;
}

function optMarital(v: string) {
  const s = v.trim();
  return s === "" ? null : (s as MaritalStatus);
}

export default function MemberDetailPage({
  params,
}: {
  params: {
    id: string;
  };
}) {
  const router = useRouter();
  const token = getAccessToken();
  const memberId = params.id;
  const { user, status, isAdmin } = useAuth();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [original, setOriginal] = useState<MemberDetailResponse | null>(null);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [role, setRole] = useState<UserRole>("member");

  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [address, setAddress] = useState("");
  const [maritalStatus, setMaritalStatus] = useState<string>("");

  const [dateOfBirth, setDateOfBirth] = useState("");
  const [baptismDate, setBaptismDate] = useState("");
  const [confirmationDate, setConfirmationDate] = useState("");
  const [joinDate, setJoinDate] = useState("");

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

    if (status !== "authenticated" || !user || !isAdmin) {
      if (status === "unauthenticated") {
        setError("You need to sign in to view this page.");
      }
      setLoading(false);
      setOriginal(null);
      return;
    }

    if (!token) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setSuccess(false);

    (async () => {
      try {
        const detail = await apiFetch<MemberDetailResponse>(
          `/api/v1/members/${memberId}`,
          { method: "GET", token },
        );
        if (cancelled) return;
        setOriginal(detail);

        setFullName(detail.full_name);
        setEmail(detail.email);
        setIsActive(detail.is_active);
        setRole(detail.role);

        setPhoneNumber(detail.profile.phone_number ?? "");
        setContactEmail(detail.profile.contact_email ?? "");
        setAddress(detail.profile.address ?? "");
        setMaritalStatus(detail.profile.marital_status ?? "");

        setDateOfBirth(detail.profile.date_of_birth ?? "");
        setBaptismDate(detail.profile.baptism_date ?? "");
        setConfirmationDate(detail.profile.confirmation_date ?? "");
        setJoinDate(detail.profile.join_date ?? "");

        setWhatsappEnabled(detail.profile.whatsapp_enabled);
        setSmsEnabled(detail.profile.sms_enabled);
        setPreferredChannel(detail.profile.preferred_channel);
      } catch (err) {
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
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [memberId, router, token, status, user, isAdmin]);

  const patchPreview = useMemo(() => {
    if (!original) return null;

    const payload: MemberAdminPatch = {};

    const full = fullName.trim();
    if (full && full !== original.full_name) payload.full_name = full;
    if (email.trim() && email.trim() !== original.email) payload.email = email.trim();
    if (isActive !== original.is_active) payload.is_active = isActive;
    if (role !== original.role) payload.role = role;

    const pn = optString(phoneNumber);
    if (pn !== original.profile.phone_number) payload.phone_number = pn;

    const ce = optString(contactEmail);
    if (ce !== original.profile.contact_email) payload.contact_email = ce;

    const addr = optString(address);
    if (addr !== original.profile.address) payload.address = addr;

    const ms = optMarital(maritalStatus);
    if (ms !== original.profile.marital_status) payload.marital_status = ms;

    const dob = optDate(dateOfBirth);
    if (dob !== original.profile.date_of_birth) payload.date_of_birth = dob;

    const bd = optDate(baptismDate);
    if (bd !== original.profile.baptism_date) payload.baptism_date = bd;

    const cd = optDate(confirmationDate);
    if (cd !== original.profile.confirmation_date) payload.confirmation_date = cd;

    const jd = optDate(joinDate);
    if (jd !== original.profile.join_date) payload.join_date = jd;

    if (whatsappEnabled !== original.profile.whatsapp_enabled)
      payload.whatsapp_enabled = whatsappEnabled;
    if (smsEnabled !== original.profile.sms_enabled) payload.sms_enabled = smsEnabled;
    if (preferredChannel !== original.profile.preferred_channel)
      payload.preferred_channel = preferredChannel;

    return Object.keys(payload).length === 0 ? null : payload;
  }, [
    address,
    baptismDate,
    contactEmail,
    confirmationDate,
    dateOfBirth,
    email,
    fullName,
    isActive,
    joinDate,
    maritalStatus,
    original,
    phoneNumber,
    preferredChannel,
    role,
    smsEnabled,
    whatsappEnabled,
  ]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !patchPreview) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const updated = await apiFetch<MemberDetailResponse>(
        `/api/v1/members/${memberId}`,
        { method: "PATCH", body: patchPreview as MemberAdminPatch, token },
      );
      setOriginal(updated);
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

  const canSave = !!patchPreview && !submitting && !!original && isAdmin;

  const inputCls =
    "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400";

  if (status === "loading") {
    return (
      <PageShell
        title="Member"
        description="View and update this person’s account and parish profile."
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
        title="Member"
        description="View and update this person’s account and parish profile."
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
        title="Member"
        description="View and update this person’s account and parish profile."
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
      title={original ? fullName || original.full_name : "Member"}
      description="View and update this person’s account and parish profile."
    >
      <div className="mb-4 flex justify-end">
        <Link
          href="/members"
          className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline"
        >
          ← Back to members
        </Link>
      </div>

      {loading ? (
        <ContentCard>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            Loading…
          </div>
        </ContentCard>
      ) : null}

      {error && !original ? (
        <ContentCard>
          <p className="text-sm text-red-800">{error}</p>
        </ContentCard>
      ) : null}

      {!loading && original && isAdmin ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <ContentCard className="space-y-6">
            {success ? (
              <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                Changes saved.
              </div>
            ) : null}

            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                {error}
              </div>
            ) : null}

            <section className="space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Account
              </h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Full name</label>
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className={inputCls}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Login email</label>
                  <input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    type="email"
                    className={inputCls}
                  />
                </div>
                <label className="flex items-center gap-2 pt-6 md:pt-0">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm font-medium text-slate-800">Account active</span>
                </label>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as UserRole)}
                    className={inputCls}
                  >
                    <option value="admin">Admin</option>
                    <option value="group_leader">Group leader</option>
                    <option value="member">Member</option>
                  </select>
                </div>
              </div>
            </section>

            <section className="space-y-4 border-t border-slate-100 pt-6">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Directory profile
              </h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Phone</label>
                  <input
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className={inputCls}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Contact email</label>
                  <input
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    type="email"
                    className={inputCls}
                  />
                </div>
                <div className="space-y-1.5 md:col-span-2">
                  <label className="text-sm font-medium text-slate-800">Address</label>
                  <textarea
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className={`${inputCls} h-24 resize-none`}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Marital status</label>
                  <select
                    value={maritalStatus}
                    onChange={(e) => setMaritalStatus(e.target.value)}
                    className={inputCls}
                  >
                    <option value="">—</option>
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="widowed">Widowed</option>
                    <option value="divorced">Divorced</option>
                    <option value="separated">Separated</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Preferred channel</label>
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
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Date of birth</label>
                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className={inputCls}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Baptism date</label>
                  <input
                    type="date"
                    value={baptismDate}
                    onChange={(e) => setBaptismDate(e.target.value)}
                    className={inputCls}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Confirmation date</label>
                  <input
                    type="date"
                    value={confirmationDate}
                    onChange={(e) => setConfirmationDate(e.target.value)}
                    className={inputCls}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-800">Join date</label>
                  <input
                    type="date"
                    value={joinDate}
                    onChange={(e) => setJoinDate(e.target.value)}
                    className={inputCls}
                  />
                </div>
                <div className="flex flex-wrap gap-4 md:col-span-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={whatsappEnabled}
                      onChange={(e) => setWhatsappEnabled(e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm text-slate-800">WhatsApp</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={smsEnabled}
                      onChange={(e) => setSmsEnabled(e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm text-slate-800">SMS</span>
                  </label>
                </div>
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 pt-6">
              <button
                type="submit"
                disabled={!canSave}
                className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-60"
              >
                {submitting ? "Saving…" : "Save changes"}
              </button>
              {!patchPreview ? (
                <span className="text-sm text-slate-500">Change a field to enable saving.</span>
              ) : null}
            </div>
          </ContentCard>
        </form>
      ) : null}
    </PageShell>
  );
}
