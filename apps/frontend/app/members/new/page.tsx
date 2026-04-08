"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
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
  ChurchMemberCreateBody,
  ChurchMemberDetailResponse,
  ChurchMembershipStatus,
  Gender,
  MaritalStatus,
} from "lib/types";
import PageShell, { ContentCard } from "components/layout/PageShell";
import { btnPrimary, fieldInput } from "lib/ui";

const inputCls = fieldInput;

function optStr(s: string): string | undefined {
  const t = s.trim();
  return t === "" ? undefined : t;
}

function optDate(s: string): string | undefined {
  const t = s.trim();
  return t === "" ? undefined : t;
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

function buildCreateBody(f: {
  first_name: string;
  middle_name: string;
  last_name: string;
  gender: Gender;
  date_of_birth: string;
  phone: string;
  email: string;
  address: string;
  nationality: string;
  occupation: string;
  marital_status: string;
  preferred_language: string;
  registration_number: string;
  membership_status: ChurchMembershipStatus;
  joined_at_local: string;
  is_active: boolean;
  is_baptized: boolean;
  baptism_date: string;
  baptism_place: string;
  is_communicant: boolean;
  first_communion_date: string;
  first_communion_place: string;
  is_confirmed: boolean;
  confirmation_date: string;
  confirmation_place: string;
  is_married: boolean;
  marriage_date: string;
  marriage_place: string;
  spouse_name: string;
  father_name: string;
  mother_name: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  is_deceased: boolean;
  date_of_death: string;
  funeral_date: string;
  burial_place: string;
  cause_of_death: string;
  notes: string;
}): ChurchMemberCreateBody {
  const body: ChurchMemberCreateBody = {
    first_name: f.first_name.trim(),
    last_name: f.last_name.trim(),
    gender: f.gender,
    membership_status: f.membership_status,
    is_active: f.is_active,
    is_baptized: f.is_baptized,
    is_communicant: f.is_communicant,
    is_confirmed: f.is_confirmed,
    is_married: f.is_married,
    is_deceased: f.is_deceased,
  };
  const m = optStr(f.middle_name);
  if (m !== undefined) body.middle_name = m;
  const dob = optDate(f.date_of_birth);
  if (dob !== undefined) body.date_of_birth = dob;
  const ph = optStr(f.phone);
  if (ph !== undefined) body.phone = ph;
  const em = optStr(f.email);
  if (em !== undefined) body.email = em;
  const ad = optStr(f.address);
  if (ad !== undefined) body.address = ad;
  const nat = optStr(f.nationality);
  if (nat !== undefined) body.nationality = nat;
  const oc = optStr(f.occupation);
  if (oc !== undefined) body.occupation = oc;
  if (f.marital_status) body.marital_status = f.marital_status as MaritalStatus;
  const pl = optStr(f.preferred_language);
  if (pl !== undefined) body.preferred_language = pl;
  const rn = optStr(f.registration_number);
  if (rn !== undefined) body.registration_number = rn;
  if (f.joined_at_local.trim()) {
    const d = new Date(f.joined_at_local);
    if (!isNaN(d.getTime())) body.joined_at = d.toISOString();
  }
  const bd = optDate(f.baptism_date);
  if (bd !== undefined) body.baptism_date = bd;
  const bp = optStr(f.baptism_place);
  if (bp !== undefined) body.baptism_place = bp;
  const fcd = optDate(f.first_communion_date);
  if (fcd !== undefined) body.first_communion_date = fcd;
  const fcp = optStr(f.first_communion_place);
  if (fcp !== undefined) body.first_communion_place = fcp;
  const cfd = optDate(f.confirmation_date);
  if (cfd !== undefined) body.confirmation_date = cfd;
  const cp = optStr(f.confirmation_place);
  if (cp !== undefined) body.confirmation_place = cp;
  const md = optDate(f.marriage_date);
  if (md !== undefined) body.marriage_date = md;
  const mp = optStr(f.marriage_place);
  if (mp !== undefined) body.marriage_place = mp;
  const sn = optStr(f.spouse_name);
  if (sn !== undefined) body.spouse_name = sn;
  const fn = optStr(f.father_name);
  if (fn !== undefined) body.father_name = fn;
  const mn = optStr(f.mother_name);
  if (mn !== undefined) body.mother_name = mn;
  const ecn = optStr(f.emergency_contact_name);
  if (ecn !== undefined) body.emergency_contact_name = ecn;
  const ecp = optStr(f.emergency_contact_phone);
  if (ecp !== undefined) body.emergency_contact_phone = ecp;
  const dod = optDate(f.date_of_death);
  if (dod !== undefined) body.date_of_death = dod;
  const fd = optDate(f.funeral_date);
  if (fd !== undefined) body.funeral_date = fd;
  const bp2 = optStr(f.burial_place);
  if (bp2 !== undefined) body.burial_place = bp2;
  const cod = optStr(f.cause_of_death);
  if (cod !== undefined) body.cause_of_death = cod;
  const nt = optStr(f.notes);
  if (nt !== undefined) body.notes = nt;
  return body;
}

export default function CreateChurchMemberPage() {
  const router = useRouter();
  const token = getAccessToken();
  const { user, status, isAdmin } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [gender, setGender] = useState<Gender>("unknown");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [nationality, setNationality] = useState("");
  const [occupation, setOccupation] = useState("");
  const [maritalStatus, setMaritalStatus] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState("");
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [membershipStatus, setMembershipStatus] = useState<ChurchMembershipStatus>("active");
  const [joinedAtLocal, setJoinedAtLocal] = useState("");
  const [isActive, setIsActive] = useState(true);

  const [isBaptized, setIsBaptized] = useState(false);
  const [baptismDate, setBaptismDate] = useState("");
  const [baptismPlace, setBaptismPlace] = useState("");
  const [isCommunicant, setIsCommunicant] = useState(false);
  const [firstCommunionDate, setFirstCommunionDate] = useState("");
  const [firstCommunionPlace, setFirstCommunionPlace] = useState("");
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [confirmationDate, setConfirmationDate] = useState("");
  const [confirmationPlace, setConfirmationPlace] = useState("");
  const [isMarried, setIsMarried] = useState(false);
  const [marriageDate, setMarriageDate] = useState("");
  const [marriagePlace, setMarriagePlace] = useState("");
  const [spouseName, setSpouseName] = useState("");
  const [fatherName, setFatherName] = useState("");
  const [motherName, setMotherName] = useState("");
  const [emergencyContactName, setEmergencyContactName] = useState("");
  const [emergencyContactPhone, setEmergencyContactPhone] = useState("");

  const [isDeceased, setIsDeceased] = useState(false);
  const [dateOfDeath, setDateOfDeath] = useState("");
  const [funeralDate, setFuneralDate] = useState("");
  const [burialPlace, setBurialPlace] = useState("");
  const [causeOfDeath, setCauseOfDeath] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (status === "authenticated" && user && !isAdmin) {
      router.replace("/profile?notice=admin_only");
    }
  }, [status, user, isAdmin, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !firstName.trim() || !lastName.trim()) {
      setError("First and last name are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    const payload = buildCreateBody({
      first_name: firstName,
      middle_name: middleName,
      last_name: lastName,
      gender,
      date_of_birth: dateOfBirth,
      phone,
      email,
      address,
      nationality,
      occupation,
      marital_status: maritalStatus,
      preferred_language: preferredLanguage,
      registration_number: registrationNumber,
      membership_status: membershipStatus,
      joined_at_local: joinedAtLocal,
      is_active: isActive,
      is_baptized: isBaptized,
      baptism_date: baptismDate,
      baptism_place: baptismPlace,
      is_communicant: isCommunicant,
      first_communion_date: firstCommunionDate,
      first_communion_place: firstCommunionPlace,
      is_confirmed: isConfirmed,
      confirmation_date: confirmationDate,
      confirmation_place: confirmationPlace,
      is_married: isMarried,
      marriage_date: marriageDate,
      marriage_place: marriagePlace,
      spouse_name: spouseName,
      father_name: fatherName,
      mother_name: motherName,
      emergency_contact_name: emergencyContactName,
      emergency_contact_phone: emergencyContactPhone,
      is_deceased: isDeceased,
      date_of_death: dateOfDeath,
      funeral_date: funeralDate,
      burial_place: burialPlace,
      cause_of_death: causeOfDeath,
      notes,
    });
    try {
      const created = await apiFetch<ChurchMemberDetailResponse>("/api/v1/church-members/", {
        method: "POST",
        token,
        body: payload,
      });
      router.replace(`/members/${created.church_member_id}`);
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

  if (status === "loading" || (status === "authenticated" && user && !isAdmin)) {
    return (
      <PageShell title="Create member" description="">
        <ContentCard>
          <div className="text-sm text-slate-600">Loading…</div>
        </ContentCard>
      </PageShell>
    );
  }

  if (!isAdmin || status !== "authenticated") {
    return (
      <PageShell title="Create member" description="">
        <ContentCard>
          <p className="text-sm text-slate-600">Sign in as an administrator to add parish records.</p>
        </ContentCard>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="New parish record"
      description="Creates an official parish registry entry only — no app login. Software accounts are separate."
    >
      <div className="mb-4">
        <Link href="/members" className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline">
          ← Back to registry
        </Link>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        {error ? (
          <ContentCard>
            <p className="text-sm text-red-800">{error}</p>
          </ContentCard>
        ) : null}

        <ContentCard className="space-y-6">
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Identity</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">First name *</label>
                <input
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Middle name</label>
                <input value={middleName} onChange={(e) => setMiddleName(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Last name *</label>
                <input
                  required
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Gender</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value as Gender)}
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
                <input type="date" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Phone</label>
                <input value={phone} onChange={(e) => setPhone(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-sm font-medium text-slate-800">Email (registry, not login)</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5 md:col-span-3">
                <label className="text-sm font-medium text-slate-800">Address</label>
                <textarea value={address} onChange={(e) => setAddress(e.target.value)} className={`${inputCls} min-h-[72px]`} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Nationality</label>
                <input value={nationality} onChange={(e) => setNationality(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Occupation</label>
                <input value={occupation} onChange={(e) => setOccupation(e.target.value)} className={inputCls} />
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
                <label className="text-sm font-medium text-slate-800">Preferred language</label>
                <input
                  value={preferredLanguage}
                  onChange={(e) => setPreferredLanguage(e.target.value)}
                  className={inputCls}
                />
              </div>
            </div>
          </section>

          <section className="border-t border-slate-100 pt-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Membership</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Registration #</label>
                <input
                  value={registrationNumber}
                  onChange={(e) => setRegistrationNumber(e.target.value)}
                  className={inputCls}
                />
                <p className="text-xs text-slate-500">
                  Optional. Leave blank to auto-generate (example: 2026-0001).
                </p>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Membership status</label>
                <select
                  value={membershipStatus}
                  onChange={(e) => setMembershipStatus(e.target.value as ChurchMembershipStatus)}
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
                  value={joinedAtLocal}
                  onChange={(e) => setJoinedAtLocal(e.target.value)}
                  className={inputCls}
                />
                <p className="text-xs text-slate-500">Leave blank to use server time.</p>
              </div>
              <label className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Active in registry</span>
              </label>
            </div>
          </section>

          <section className="border-t border-slate-100 pt-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Sacramental</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="flex items-center gap-2 md:col-span-3">
                <input
                  type="checkbox"
                  checked={isBaptized}
                  onChange={(e) => setIsBaptized(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Baptized</span>
              </label>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Baptism date</label>
                <input type="date" value={baptismDate} onChange={(e) => setBaptismDate(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-sm font-medium text-slate-800">Baptism place</label>
                <input value={baptismPlace} onChange={(e) => setBaptismPlace(e.target.value)} className={inputCls} />
              </div>
              <label className="flex items-center gap-2 md:col-span-3">
                <input
                  type="checkbox"
                  checked={isCommunicant}
                  onChange={(e) => setIsCommunicant(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Communicant</span>
              </label>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">First communion date</label>
                <input
                  type="date"
                  value={firstCommunionDate}
                  onChange={(e) => setFirstCommunionDate(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-sm font-medium text-slate-800">First communion place</label>
                <input
                  value={firstCommunionPlace}
                  onChange={(e) => setFirstCommunionPlace(e.target.value)}
                  className={inputCls}
                />
              </div>
              <label className="flex items-center gap-2 md:col-span-3">
                <input
                  type="checkbox"
                  checked={isConfirmed}
                  onChange={(e) => setIsConfirmed(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Confirmed</span>
              </label>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Confirmation date</label>
                <input
                  type="date"
                  value={confirmationDate}
                  onChange={(e) => setConfirmationDate(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-sm font-medium text-slate-800">Confirmation place</label>
                <input
                  value={confirmationPlace}
                  onChange={(e) => setConfirmationPlace(e.target.value)}
                  className={inputCls}
                />
              </div>
              <label className="flex items-center gap-2 md:col-span-3">
                <input
                  type="checkbox"
                  checked={isMarried}
                  onChange={(e) => setIsMarried(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Married (sacramental)</span>
              </label>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Marriage date</label>
                <input type="date" value={marriageDate} onChange={(e) => setMarriageDate(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-sm font-medium text-slate-800">Marriage place</label>
                <input value={marriagePlace} onChange={(e) => setMarriagePlace(e.target.value)} className={inputCls} />
              </div>
            </div>
          </section>

          <section className="border-t border-slate-100 pt-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Family / contacts</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Spouse name</label>
                <input value={spouseName} onChange={(e) => setSpouseName(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Father&apos;s name</label>
                <input value={fatherName} onChange={(e) => setFatherName(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Mother&apos;s name</label>
                <input value={motherName} onChange={(e) => setMotherName(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Emergency contact name</label>
                <input
                  value={emergencyContactName}
                  onChange={(e) => setEmergencyContactName(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Emergency contact phone</label>
                <input
                  value={emergencyContactPhone}
                  onChange={(e) => setEmergencyContactPhone(e.target.value)}
                  className={inputCls}
                />
              </div>
            </div>
          </section>

          <section className="border-t border-slate-100 pt-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Death / memorial</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex items-center gap-2 md:col-span-2">
                <input
                  type="checkbox"
                  checked={isDeceased}
                  onChange={(e) => setIsDeceased(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm font-medium text-slate-800">Deceased</span>
              </label>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Date of death</label>
                <input type="date" value={dateOfDeath} onChange={(e) => setDateOfDeath(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Funeral date</label>
                <input type="date" value={funeralDate} onChange={(e) => setFuneralDate(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Burial place</label>
                <input value={burialPlace} onChange={(e) => setBurialPlace(e.target.value)} className={inputCls} />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-800">Cause of death</label>
                <input value={causeOfDeath} onChange={(e) => setCauseOfDeath(e.target.value)} className={inputCls} />
              </div>
            </div>
          </section>

          <section className="border-t border-slate-100 pt-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Notes</h2>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className={`${inputCls} min-h-[100px]`}
              placeholder="Internal notes (optional)"
            />
          </section>

          <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-6">
            <button
              type="submit"
              disabled={submitting}
              className={btnPrimary}
            >
              {submitting ? "Saving…" : "Create parish record"}
            </button>
            <Link
              href="/members"
              className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
            >
              Cancel
            </Link>
          </div>
        </ContentCard>
      </form>
    </PageShell>
  );
}
