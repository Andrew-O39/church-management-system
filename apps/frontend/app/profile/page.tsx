"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { apiFetch, type ApiError } from "lib/api";
import type { MemberDetailResponse, PreferredChannel } from "lib/types";
import { getAccessToken } from "lib/session";
import type { MemberSelfPatch } from "lib/types";

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

export default function ProfilePage() {
  const token = getAccessToken();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
      setError("Not authenticated. Please log in again.");
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
      .catch((err) => setError(toErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [token]);

  const canSubmit = useMemo(() => !submitting && fullName.trim().length > 0, [fullName, submitting]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);

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
      setSuccess("Profile updated successfully.");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">My Profile</h1>

      {loading ? <p className="text-sm text-slate-600">Loading...</p> : null}

      {!loading && error ? (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      {success ? (
        <div className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800">
          {success}
        </div>
      ) : null}

      {!loading && data ? (
        <form onSubmit={onSubmit} className="space-y-4">
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
              <label className="text-sm font-medium text-slate-800">Email (login)</label>
              <input
                value={data.email}
                disabled
                className="w-full cursor-not-allowed rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-slate-600"
              />
              <p className="text-xs text-slate-500">Members can only edit the optional directory contact email.</p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-800">Phone number</label>
              <input
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2"
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-800">
                Contact email (optional)
              </label>
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
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2 md:col-span-2">
              <div className="text-sm font-semibold text-slate-900">Notification preferences</div>

              <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
                <input
                  type="checkbox"
                  checked={whatsappEnabled}
                  onChange={(e) => setWhatsappEnabled(e.target.checked)}
                />
                <span className="text-sm text-slate-800">WhatsApp</span>
              </label>

              <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
                <input
                  type="checkbox"
                  checked={smsEnabled}
                  onChange={(e) => setSmsEnabled(e.target.checked)}
                />
                <span className="text-sm text-slate-800">SMS</span>
              </label>
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
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={!canSubmit}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {submitting ? "Saving..." : "Save changes"}
            </button>
            <p className="text-xs text-slate-500">Password changes are not supported in Step 4.</p>
          </div>
        </form>
      ) : null}
    </div>
  );
}


