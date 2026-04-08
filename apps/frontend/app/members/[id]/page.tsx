"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useAuth } from "components/providers/AuthProvider";
import { apiFetch } from "lib/api";
import { getAccessToken } from "lib/session";
import { clearSessionAndRedirect } from "lib/auth";
import {
  getApiErrorDetail,
  isConflictError,
  isInactiveAccountError,
  isUnauthorized,
  toErrorMessage,
} from "lib/errors";
import type {
  ChurchMemberDetailResponse,
  ChurchMemberPatchBody,
  ChurchMembershipStatus,
  Gender,
  MaritalStatus,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { btnPrimary, fieldInput } from "lib/ui";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const inputCls = fieldInput;

function isUuid(s: string) {
  return UUID_RE.test(s.trim());
}

function buildPatch(o: ChurchMemberDetailResponse, f: ChurchMemberDetailResponse): ChurchMemberPatchBody {
  const p: ChurchMemberPatchBody = {};
  if (f.first_name !== o.first_name) p.first_name = f.first_name;
  if (f.middle_name !== o.middle_name) p.middle_name = f.middle_name;
  if (f.last_name !== o.last_name) p.last_name = f.last_name;
  if (f.gender !== o.gender) p.gender = f.gender;
  if (f.date_of_birth !== o.date_of_birth) p.date_of_birth = f.date_of_birth;
  if (f.phone !== o.phone) p.phone = f.phone;
  if (f.email !== o.email) p.email = f.email;
  if (f.address !== o.address) p.address = f.address;
  if (f.nationality !== o.nationality) p.nationality = f.nationality;
  if (f.occupation !== o.occupation) p.occupation = f.occupation;
  if (f.marital_status !== o.marital_status) p.marital_status = f.marital_status;
  if (f.preferred_language !== o.preferred_language) p.preferred_language = f.preferred_language;
  if (f.registration_number !== o.registration_number) p.registration_number = f.registration_number;
  if (f.membership_status !== o.membership_status) p.membership_status = f.membership_status;
  if (f.joined_at !== o.joined_at) p.joined_at = f.joined_at;
  if (f.is_active !== o.is_active) p.is_active = f.is_active;
  if (f.is_baptized !== o.is_baptized) p.is_baptized = f.is_baptized;
  if (f.baptism_date !== o.baptism_date) p.baptism_date = f.baptism_date;
  if (f.baptism_place !== o.baptism_place) p.baptism_place = f.baptism_place;
  if (f.is_communicant !== o.is_communicant) p.is_communicant = f.is_communicant;
  if (f.first_communion_date !== o.first_communion_date) p.first_communion_date = f.first_communion_date;
  if (f.first_communion_place !== o.first_communion_place) p.first_communion_place = f.first_communion_place;
  if (f.is_confirmed !== o.is_confirmed) p.is_confirmed = f.is_confirmed;
  if (f.confirmation_date !== o.confirmation_date) p.confirmation_date = f.confirmation_date;
  if (f.confirmation_place !== o.confirmation_place) p.confirmation_place = f.confirmation_place;
  if (f.is_married !== o.is_married) p.is_married = f.is_married;
  if (f.marriage_date !== o.marriage_date) p.marriage_date = f.marriage_date;
  if (f.marriage_place !== o.marriage_place) p.marriage_place = f.marriage_place;
  if (f.spouse_name !== o.spouse_name) p.spouse_name = f.spouse_name;
  if (f.father_name !== o.father_name) p.father_name = f.father_name;
  if (f.mother_name !== o.mother_name) p.mother_name = f.mother_name;
  if (f.emergency_contact_name !== o.emergency_contact_name) p.emergency_contact_name = f.emergency_contact_name;
  if (f.emergency_contact_phone !== o.emergency_contact_phone) p.emergency_contact_phone = f.emergency_contact_phone;
  if (f.is_deceased !== o.is_deceased) p.is_deceased = f.is_deceased;
  if (f.date_of_death !== o.date_of_death) p.date_of_death = f.date_of_death;
  if (f.funeral_date !== o.funeral_date) p.funeral_date = f.funeral_date;
  if (f.burial_place !== o.burial_place) p.burial_place = f.burial_place;
  if (f.cause_of_death !== o.cause_of_death) p.cause_of_death = f.cause_of_death;
  if (f.notes !== o.notes) p.notes = f.notes;
  return p;
}

/** Map API detail to editable draft (dates as YYYY-MM-DD for inputs, joined_at as datetime-local slice) */
function detailToDraft(d: ChurchMemberDetailResponse): ChurchMemberDetailResponse {
  return { ...d };
}

function dateInput(v: string | null): string {
  if (!v) return "";
  return v.length >= 10 ? v.slice(0, 10) : v;
}

function joinedLocalInput(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromDateInput(s: string): string | null {
  const t = s.trim();
  return t === "" ? null : t;
}

function fromJoinedLocal(s: string): string | null {
  const t = s.trim();
  if (!t) return null;
  const d = new Date(t);
  if (isNaN(d.getTime())) return null;
  return d.toISOString();
}

function registryValidationMessage(err: unknown): string {
  const detail = (getApiErrorDetail(err) ?? "").toLowerCase();
  if (isConflictError(err) && detail.includes("registration number")) {
    return "This registration number is already in use.";
  }
  if (detail.includes("registration number already exists")) {
    return "This registration number is already in use.";
  }
  return toErrorMessage(err);
}

export default function ChurchMemberDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const token = getAccessToken();
  const memberId = params.id;
  const { user, status, isAdmin } = useAuth();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [original, setOriginal] = useState<ChurchMemberDetailResponse | null>(null);
  const [draft, setDraft] = useState<ChurchMemberDetailResponse | null>(null);
  const [joinedLocal, setJoinedLocal] = useState("");
  /** Avoid spurious joined_at patches when round-tripping datetime-local vs ISO. */
  const [joinedLocalInitial, setJoinedLocalInitial] = useState("");

  const invalidId = !isUuid(memberId);

  useEffect(() => {
    if (status === "authenticated" && user && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, user, isAdmin, router]);

  useEffect(() => {
    if (invalidId) {
      setLoading(false);
      return;
    }
    if (status === "loading") return;
    if (status !== "authenticated" || !user || !isAdmin) {
      if (status === "unauthenticated") setError("You need to sign in.");
      setLoading(false);
      return;
    }
    if (!token) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    apiFetch<ChurchMemberDetailResponse>(`/api/v1/church-members/${memberId}`, { method: "GET", token })
      .then((d) => {
        if (cancelled) return;
        const dr = detailToDraft(d);
        setOriginal(dr);
        setDraft(dr);
        const jl = joinedLocalInput(dr.joined_at);
        setJoinedLocal(jl);
        setJoinedLocalInitial(jl);
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
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [memberId, token, router, status, user, isAdmin, invalidId]);

  const patchPreview = useMemo(() => {
    if (!original || !draft) return null;
    const mergedJoinedAt =
      joinedLocal === joinedLocalInitial
        ? original.joined_at
        : (fromJoinedLocal(joinedLocal) ?? draft.joined_at);
    const merged: ChurchMemberDetailResponse = {
      ...draft,
      joined_at: mergedJoinedAt,
    };
    const p = buildPatch(original, merged);
    return Object.keys(p).length === 0 ? null : p;
  }, [original, draft, joinedLocal, joinedLocalInitial]);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!token || !patchPreview || !draft) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      const updated = await apiFetch<ChurchMemberDetailResponse>(
        `/api/v1/church-members/${memberId}`,
        { method: "PATCH", body: patchPreview, token },
      );
      const dr = detailToDraft(updated);
      setOriginal(dr);
      setDraft(dr);
      const jl = joinedLocalInput(dr.joined_at);
      setJoinedLocal(jl);
      setJoinedLocalInitial(jl);
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
      setError(registryValidationMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  function setField<K extends keyof ChurchMemberDetailResponse>(key: K, value: ChurchMemberDetailResponse[K]) {
    setDraft((d) => (d ? { ...d, [key]: value } : d));
  }

  if (status === "loading") {
    return (
      <PageShell title="Parish registry" description="">
        <ContentCard>
          <div className="text-sm text-slate-600">Checking access…</div>
        </ContentCard>
      </PageShell>
    );
  }

  if (invalidId) {
    return (
      <PageShell title="Parish registry" description="">
        <ContentCard>
          <p className="text-sm text-red-800">Invalid record id.</p>
          <Link href="/members" className="mt-2 inline-block text-sm text-slate-700 underline">
            ← Registry
          </Link>
        </ContentCard>
      </PageShell>
    );
  }

  if (status === "authenticated" && user && !isAdmin) {
    return (
      <PageShell title="Parish registry" description="">
        <ContentCard>
          <div className="text-sm text-slate-600">Redirecting…</div>
        </ContentCard>
      </PageShell>
    );
  }

  const d = draft;

  return (
    <PageShell
      title={d?.full_name ?? "Parish registry"}
      description="Official parish registry record. App login accounts are separate from this list."
    >
      <div className="mb-4 flex flex-wrap justify-between gap-2">
        <Link href="/members" className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline">
          ← Parish registry
        </Link>
        {d?.church_member_id ? (
          <span className="text-xs text-slate-500">ID: {d.church_member_id}</span>
        ) : null}
      </div>

      {loading ? (
        <ContentCard>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            Loading…
          </div>
        </ContentCard>
      ) : null}

      {error && !d ? (
        <ContentCard>
          <p className="text-sm text-red-800">{error}</p>
        </ContentCard>
      ) : null}

      {d && isAdmin ? (
        <div className="space-y-4">
          <form onSubmit={onSave} className="space-y-4">
            <ContentCard className="space-y-6">
              {success ? (
                <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                  Saved.
                </div>
              ) : null}
              {error ? (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>
              ) : null}

              <section>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Identity</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">First name</label>
                    <input
                      value={d.first_name}
                      onChange={(e) => setField("first_name", e.target.value)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Middle name</label>
                    <input
                      value={d.middle_name ?? ""}
                      onChange={(e) => setField("middle_name", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Last name</label>
                    <input value={d.last_name} onChange={(e) => setField("last_name", e.target.value)} className={inputCls} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Gender</label>
                    <select
                      value={d.gender}
                      onChange={(e) => setField("gender", e.target.value as Gender)}
                      className={inputCls}
                    >
                      <option value="unknown">Unknown</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                      <option value="prefer_not_to_say">Prefer not to say</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Date of birth</label>
                    <input
                      type="date"
                      value={dateInput(d.date_of_birth)}
                      onChange={(e) => setField("date_of_birth", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Phone</label>
                    <input value={d.phone ?? ""} onChange={(e) => setField("phone", e.target.value || null)} className={inputCls} />
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <label className="text-sm font-medium text-slate-800">Registry email</label>
                    <input
                      type="email"
                      value={d.email ?? ""}
                      onChange={(e) => setField("email", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5 md:col-span-3">
                    <label className="text-sm font-medium text-slate-800">Address</label>
                    <textarea
                      value={d.address ?? ""}
                      onChange={(e) => setField("address", e.target.value || null)}
                      className={`${inputCls} min-h-[72px]`}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Nationality</label>
                    <input
                      value={d.nationality ?? ""}
                      onChange={(e) => setField("nationality", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Occupation</label>
                    <input
                      value={d.occupation ?? ""}
                      onChange={(e) => setField("occupation", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Marital status</label>
                    <select
                      value={d.marital_status ?? ""}
                      onChange={(e) =>
                        setField("marital_status", (e.target.value || null) as MaritalStatus | null)
                      }
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
                    <label className="text-sm font-medium text-slate-800">Preferred language</label>
                    <input
                      value={d.preferred_language ?? ""}
                      onChange={(e) => setField("preferred_language", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                </div>
              </section>

              <section className="border-t border-slate-100 pt-6">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Membership</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Registration #</label>
                    <input
                      value={d.registration_number ?? ""}
                      onChange={(e) => setField("registration_number", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Membership status</label>
                    <select
                      value={d.membership_status}
                      onChange={(e) => setField("membership_status", e.target.value as ChurchMembershipStatus)}
                      className={inputCls}
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="visitor">Visitor</option>
                      <option value="transferred">Transferred</option>
                      <option value="deceased">Deceased</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Joined (local)</label>
                    <input
                      type="datetime-local"
                      value={joinedLocal}
                      onChange={(e) => setJoinedLocal(e.target.value)}
                      className={inputCls}
                    />
                  </div>
                  <label className="flex items-center gap-2 md:col-span-3">
                    <input
                      type="checkbox"
                      checked={d.is_active}
                      onChange={(e) => setField("is_active", e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm font-medium text-slate-800">Active in registry</span>
                  </label>
                </div>
              </section>

              <section className="border-t border-slate-100 pt-6">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Sacramental</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="flex items-center gap-2 md:col-span-3">
                    <input
                      type="checkbox"
                      checked={d.is_baptized}
                      onChange={(e) => setField("is_baptized", e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm font-medium">Baptized</span>
                  </label>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Baptism date</label>
                    <input
                      type="date"
                      value={dateInput(d.baptism_date)}
                      onChange={(e) => setField("baptism_date", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <label className="text-sm font-medium text-slate-800">Baptism place</label>
                    <input
                      value={d.baptism_place ?? ""}
                      onChange={(e) => setField("baptism_place", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <label className="flex items-center gap-2 md:col-span-3">
                    <input
                      type="checkbox"
                      checked={d.is_communicant}
                      onChange={(e) => setField("is_communicant", e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm font-medium">Communicant</span>
                  </label>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">First communion date</label>
                    <input
                      type="date"
                      value={dateInput(d.first_communion_date)}
                      onChange={(e) => setField("first_communion_date", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <label className="text-sm font-medium text-slate-800">First communion place</label>
                    <input
                      value={d.first_communion_place ?? ""}
                      onChange={(e) => setField("first_communion_place", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <label className="flex items-center gap-2 md:col-span-3">
                    <input
                      type="checkbox"
                      checked={d.is_confirmed}
                      onChange={(e) => setField("is_confirmed", e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm font-medium">Confirmed</span>
                  </label>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Confirmation date</label>
                    <input
                      type="date"
                      value={dateInput(d.confirmation_date)}
                      onChange={(e) => setField("confirmation_date", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <label className="text-sm font-medium text-slate-800">Confirmation place</label>
                    <input
                      value={d.confirmation_place ?? ""}
                      onChange={(e) => setField("confirmation_place", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <label className="flex items-center gap-2 md:col-span-3">
                    <input
                      type="checkbox"
                      checked={d.is_married}
                      onChange={(e) => setField("is_married", e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm font-medium">Married (sacramental)</span>
                  </label>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Marriage date</label>
                    <input
                      type="date"
                      value={dateInput(d.marriage_date)}
                      onChange={(e) => setField("marriage_date", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <label className="text-sm font-medium text-slate-800">Marriage place</label>
                    <input
                      value={d.marriage_place ?? ""}
                      onChange={(e) => setField("marriage_place", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                </div>
              </section>

              <section className="border-t border-slate-100 pt-6">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Family / contacts</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Spouse name</label>
                    <input
                      value={d.spouse_name ?? ""}
                      onChange={(e) => setField("spouse_name", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Father&apos;s name</label>
                    <input
                      value={d.father_name ?? ""}
                      onChange={(e) => setField("father_name", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Mother&apos;s name</label>
                    <input
                      value={d.mother_name ?? ""}
                      onChange={(e) => setField("mother_name", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Emergency contact name</label>
                    <input
                      value={d.emergency_contact_name ?? ""}
                      onChange={(e) => setField("emergency_contact_name", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Emergency contact phone</label>
                    <input
                      value={d.emergency_contact_phone ?? ""}
                      onChange={(e) => setField("emergency_contact_phone", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                </div>
              </section>

              <section className="border-t border-slate-100 pt-6">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Death / memorial</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="flex items-center gap-2 md:col-span-2">
                    <input
                      type="checkbox"
                      checked={d.is_deceased}
                      onChange={(e) => setField("is_deceased", e.target.checked)}
                      className="rounded border-slate-300"
                    />
                    <span className="text-sm font-medium">Deceased</span>
                  </label>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Date of death</label>
                    <input
                      type="date"
                      value={dateInput(d.date_of_death)}
                      onChange={(e) => setField("date_of_death", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Funeral date</label>
                    <input
                      type="date"
                      value={dateInput(d.funeral_date)}
                      onChange={(e) => setField("funeral_date", fromDateInput(e.target.value))}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Burial place</label>
                    <input
                      value={d.burial_place ?? ""}
                      onChange={(e) => setField("burial_place", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-800">Cause of death</label>
                    <input
                      value={d.cause_of_death ?? ""}
                      onChange={(e) => setField("cause_of_death", e.target.value || null)}
                      className={inputCls}
                    />
                  </div>
                </div>
              </section>

              <section className="border-t border-slate-100 pt-6">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Notes</h3>
                <textarea
                  value={d.notes ?? ""}
                  onChange={(e) => setField("notes", e.target.value || null)}
                  className={`${inputCls} min-h-[100px]`}
                />
              </section>

              <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-6">
                <button
                  type="submit"
                  disabled={!patchPreview || submitting}
                  className={btnPrimary}
                >
                  {submitting ? "Saving…" : "Save changes"}
                </button>
                {success && !patchPreview ? (
                  <span className="text-sm text-green-700">Changes saved.</span>
                ) : !patchPreview ? (
                  <span className="text-sm text-slate-500">No changes to save.</span>
                ) : null}
              </div>
            </ContentCard>
          </form>
        </div>
      ) : null}
    </PageShell>
  );
}
