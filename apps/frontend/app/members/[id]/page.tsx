"use client";

import { useEffect, useMemo, useState } from "react";
import type { ApiError } from "lib/api";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import type {
  MemberAdminPatch,
  MemberDetailResponse,
  MaritalStatus,
  PreferredChannel,
  UserRole,
  MeResponse,
} from "lib/types";
import Link from "next/link";
import type { FormEvent } from "react";

function toErrorMessage(err: unknown) {
  if (typeof err === "object" && err && "status" in err) {
    const e = err as ApiError;
    if (e.detail) return e.detail;
    return `Request failed (${e.status})`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

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
  const token = getAccessToken();
  const memberId = params.id;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [me, setMe] = useState<MeResponse | null>(null);
  const isAdmin = me?.role === "admin";

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
    if (!token) {
      setError("Not authenticated. Please log in again.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setSuccess(null);

    Promise.all([
      apiFetch<MeResponse>("/api/v1/auth/me", { method: "GET", token }),
      apiFetch<MemberDetailResponse>(`/api/v1/members/${memberId}`, { method: "GET", token }),
    ])
      .then(([meRes, detail]) => {
        if (cancelled) return;
        setMe(meRes);
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
  }, [memberId, token]);

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
    setSuccess(null);

    try {
      const updated = await apiFetch<MemberDetailResponse>(
        `/api/v1/members/${memberId}`,
        { method: "PATCH", body: patchPreview as MemberAdminPatch, token },
      );
      setOriginal(updated);
      setSuccess("Member updated successfully.");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  const canSave = !!patchPreview && !submitting && !!original;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">Member Details</h1>
          <p className="text-sm text-slate-600">
            Admin-only member detail and edit flow.
          </p>
        </div>

        <Link href="/members" className="text-sm font-medium text-slate-700 hover:underline">
          Back to directory
        </Link>
      </div>

      {loading ? <p className="text-sm text-slate-600">Loading...</p> : null}

      {error ? (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      {success ? (
        <div className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800">
          {success}
        </div>
      ) : null}

      {!loading && original && !isAdmin ? (
        <div className="rounded border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-900">Access denied</h2>
          <p className="mt-1 text-sm text-slate-600">
            Your role is <span className="font-medium text-slate-900">{me?.role}</span>. Admin access is required.
          </p>
        </div>
      ) : null}

      {!loading && original && isAdmin ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="rounded border border-slate-200 bg-white p-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Full name</label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Login email</label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                />
                <span className="text-sm font-medium text-slate-800">Active</span>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                >
                  <option value="admin">admin</option>
                  <option value="group_leader">group_leader</option>
                  <option value="member">member</option>
                </select>
                <p className="text-xs text-slate-500">
                  Backend enforces safety (no self-demote; cannot remove last admin).
                </p>
              </div>
            </div>
          </div>

          <div className="rounded border border-slate-200 bg-white p-4">
            <div className="text-sm font-semibold text-slate-900">Profile fields</div>

            <div className="mt-3 grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Phone number</label>
                <input
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Contact email</label>
                <input
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  type="email"
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1 md:col-span-2">
                <label className="text-sm font-medium text-slate-800">Address</label>
                <textarea
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="h-24 w-full resize-none rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Marital status</label>
                <select
                  value={maritalStatus}
                  onChange={(e) => setMaritalStatus(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                >
                  <option value="">(unspecified)</option>
                  <option value="single">single</option>
                  <option value="married">married</option>
                  <option value="widowed">widowed</option>
                  <option value="divorced">divorced</option>
                  <option value="separated">separated</option>
                  <option value="prefer_not_to_say">prefer_not_to_say</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Preferred channel</label>
                <select
                  value={preferredChannel}
                  onChange={(e) => setPreferredChannel(e.target.value as PreferredChannel)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                >
                  <option value="whatsapp">whatsapp</option>
                  <option value="sms">sms</option>
                  <option value="email">email</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Date of birth</label>
                <input
                  type="date"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Baptism date</label>
                <input
                  type="date"
                  value={baptismDate}
                  onChange={(e) => setBaptismDate(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Confirmation date</label>
                <input
                  type="date"
                  value={confirmationDate}
                  onChange={(e) => setConfirmationDate(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-800">Join date</label>
                <input
                  type="date"
                  value={joinDate}
                  onChange={(e) => setJoinDate(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
                />
              </div>

              <div className="flex items-center gap-3 md:col-span-2">
                <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
                  <input
                    type="checkbox"
                    checked={whatsappEnabled}
                    onChange={(e) => setWhatsappEnabled(e.target.checked)}
                  />
                  <span className="text-sm font-medium text-slate-800">WhatsApp</span>
                </label>

                <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
                  <input
                    type="checkbox"
                    checked={smsEnabled}
                    onChange={(e) => setSmsEnabled(e.target.checked)}
                  />
                  <span className="text-sm font-medium text-slate-800">SMS</span>
                </label>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={!canSave}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {submitting ? "Saving..." : "Save changes"}
            </button>
            <p className="text-xs text-slate-500">
              Forbidden fields are enforced by the backend (including password and role safety rules).
            </p>
          </div>
        </form>
      ) : null}
    </div>
  );
}

