"use client";

import { useEffect } from "react";
import Link from "next/link";

import PageShell, { ContentCard } from "components/layout/PageShell";

const toc = [
  { href: "#section-1", label: "1. Our approach to security" },
  { href: "#section-2", label: "2. Who can access your data?" },
  { href: "#section-3", label: "3. Secure login and access control" },
  { href: "#section-4", label: "4. Separation of data" },
  { href: "#section-5", label: "5. Where is the data stored?" },
  { href: "#section-6", label: "6. Who can access the database?" },
  { href: "#section-7", label: "7. Protection against hackers" },
  { href: "#section-8", label: "8. Data integrity" },
  { href: "#section-9", label: "9. Backups and data safety" },
  { href: "#section-10", label: "10. Privacy and responsible use" },
  { href: "#section-11", label: "11. What Shepherd does NOT do" },
  { href: "#section-12", label: "12. Honest note about security" },
  { href: "#section-13", label: "13. Your role in keeping data safe" },
  { href: "#section-14", label: "14. Summary" },
];

export default function SecurityPage() {
  useEffect(() => {
    document.documentElement.setAttribute("data-security-doc", "1");
    return () => document.documentElement.removeAttribute("data-security-doc");
  }, []);

  return (
    <PageShell
      title="Security & Data Protection"
      description="How Shepherd protects parish data"
    >
      <nav
        aria-label="On this page"
        className="no-print max-w-4xl rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm shadow-slate-900/[0.04] ring-1 ring-slate-900/[0.04]"
      >
        <p className="text-sm font-semibold text-slate-900">On this page</p>
        <ul className="mt-3 columns-1 gap-x-8 text-sm leading-relaxed text-indigo-800 sm:columns-2">
          {toc.map((item) => (
            <li key={item.href} className="break-inside-avoid py-0.5">
              <Link href={item.href} className="underline-offset-2 hover:underline">
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <ContentCard className="security-doc-print max-w-4xl print:border-0 print:shadow-none print:ring-0">
        <article className="space-y-10 text-base leading-relaxed text-slate-800 print:space-y-8">
          <header className="space-y-3 border-b border-slate-200 pb-8 print:border-slate-300">
            <p className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
              Shepherd — Security &amp; Data Protection
            </p>
            <p>
              Shepherd is designed to help churches manage their work while keeping personal data
              safe, private, and controlled.
            </p>
            <p>This document explains, in simple terms, how your data is protected.</p>
          </header>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-1" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">1. Our approach to security</h2>
            <p>We understand that parish data is sensitive.</p>
            <p>This includes names, contact details, sacramental records, and internal church information.</p>
            <p>Our approach is simple:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Only the right people can access data</li>
              <li>Data is not publicly visible</li>
              <li>Systems are protected with multiple layers of security</li>
              <li>We follow responsible and widely accepted practices</li>
            </ul>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-2" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">2. Who can access your data?</h2>
            <h3 className="text-lg font-semibold text-slate-900">Administrators</h3>
            <p>Only authorised parish administrators can access:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Parish registry records</li>
              <li>Exports (CSV and print)</li>
              <li>App users</li>
              <li>Church settings</li>
            </ul>
            <h3 className="pt-2 text-lg font-semibold text-slate-900">Regular users</h3>
            <p>Regular members and volunteers:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Cannot access parish registry records</li>
              <li>Cannot access admin pages</li>
              <li>Can only see their own information and relevant event details</li>
            </ul>
            <p>If a non-admin tries to access restricted pages, they are redirected automatically.</p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-3" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">3. Secure login and access control</h2>
            <p>All users must sign in using:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Email</li>
              <li>Password</li>
            </ul>
            <p>Additional protections:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Sessions expire automatically after a period of inactivity</li>
              <li>Inactive accounts cannot access the system</li>
              <li>Sensitive actions require a valid logged-in session</li>
            </ul>
            <p>This prevents unauthorized access even if someone leaves a device unattended.</p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-4" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">
              4. Separation of data (important protection)
            </h2>
            <p>Shepherd keeps two types of data separate:</p>
            <h3 className="text-lg font-semibold text-slate-900">App users (people with logins)</h3>
            <p>Used for:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Events</li>
              <li>Attendance</li>
              <li>Volunteers</li>
              <li>Notifications</li>
            </ul>
            <h3 className="text-lg font-semibold text-slate-900">Parish registry (official church records)</h3>
            <p>Used for:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Sacraments</li>
              <li>Membership status</li>
              <li>Historical records</li>
            </ul>
            <p>
              <span aria-hidden="true">👉</span> These are not automatically linked.
            </p>
            <p>This separation reduces risk and protects sensitive archival data.</p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-5" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">5. Where is the data stored?</h2>
            <p>Your data is stored in a secure database system.</p>
            <p>Important points:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>It is not a public website</li>
              <li>It cannot be opened in a browser</li>
              <li>It cannot be searched online</li>
            </ul>
            <p>Only the Shepherd application can access it.</p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-6" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">6. Who can access the database?</h2>
            <p>The database is protected so that:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Only the Shepherd backend system can connect to it</li>
              <li>Secure credentials are required for access</li>
              <li>Direct access from the internet is blocked</li>
            </ul>
            <h3 className="text-lg font-semibold text-slate-900">About hosting providers</h3>
            <p>The system may be hosted on professional infrastructure providers.</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>They provide the servers and environment</li>
              <li>They do not use or access your data</li>
              <li>Access to systems is restricted and monitored</li>
            </ul>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-7" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">7. Protection against hackers</h2>
            <p>Shepherd uses several layers of protection:</p>
            <h3 className="text-lg font-semibold text-slate-900">Not publicly exposed</h3>
            <p>The database is not directly reachable from the internet.</p>
            <h3 className="text-lg font-semibold text-slate-900">Authentication required</h3>
            <p>Only valid users can access the system.</p>
            <h3 className="text-lg font-semibold text-slate-900">Backend enforcement</h3>
            <p>Security is enforced on the server, not just the interface.</p>
            <h3 className="text-lg font-semibold text-slate-900">Multiple safeguards</h3>
            <p>These include:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Login protection</li>
              <li>Server-level restrictions</li>
              <li>Database authentication</li>
              <li>Controlled access to endpoints</li>
            </ul>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-8" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">
              8. Data integrity (keeping records accurate)
            </h2>
            <p>The system prevents errors and inconsistencies:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Duplicate registration numbers are blocked</li>
              <li>Invalid data is rejected</li>
              <li>Controlled updates ensure records remain consistent</li>
            </ul>
            <p>This protects both accuracy and reliability.</p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-9" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">9. Backups and data safety</h2>
            <p>We plan and/or implement:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Regular backups of data</li>
              <li>Ability to restore data if needed</li>
            </ul>
            <p>This ensures that data is not lost due to technical issues.</p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-10" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">10. Privacy and responsible use</h2>
            <p>Shepherd is designed with privacy in mind:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Data is only visible to authorised users</li>
              <li>Data is not shared externally</li>
              <li>Personal information is handled responsibly</li>
            </ul>
            <p>
              Where applicable, the system aligns with general privacy expectations such as GDPR.
            </p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-11" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">11. What Shepherd does NOT do</h2>
            <p>To be clear:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>We do not make your data public</li>
              <li>We do not sell or share your data</li>
              <li>We do not allow unrestricted access to records</li>
            </ul>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-12" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">12. Honest note about security</h2>
            <p>No system in the world can guarantee zero risk.</p>
            <p>However:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Shepherd uses established and responsible practices</li>
              <li>Access is controlled and monitored</li>
              <li>Risks are minimized through multiple layers of protection</li>
            </ul>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-13" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">13. Your role in keeping data safe</h2>
            <p>Security is shared responsibility.</p>
            <p>Users should:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Keep passwords private</li>
              <li>Log out on shared devices</li>
              <li>Use trusted devices when possible</li>
              <li>Inform administrators of suspicious activity</li>
            </ul>
            <p>Administrators should:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Limit admin access to trusted individuals</li>
              <li>Keep contact details accurate</li>
              <li>Review user access periodically</li>
            </ul>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <section id="section-14" className="scroll-mt-28 space-y-4">
            <h2 className="shepherd-section-title text-xl sm:text-2xl">14. Summary</h2>
            <p>Shepherd protects parish data by:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Restricting access to authorised users</li>
              <li>Keeping data separate and controlled</li>
              <li>Using secure systems and infrastructure</li>
              <li>Preventing direct access to databases</li>
              <li>Applying multiple layers of protection</li>
            </ul>
            <p>The goal is simple:</p>
            <p>
              <span aria-hidden="true">👉</span> To provide a safe, reliable, and respectful environment for
              managing church records.
            </p>
          </section>

          <hr className="border-slate-200 print:border-slate-300" />

          <footer className="space-y-2 border-t border-slate-200 pt-8 text-center print:border-slate-300">
            <h2 className="text-xl font-bold text-slate-900">Shepherd</h2>
            <p className="text-slate-700">Helping your church stay organised, connected, and secure.</p>
          </footer>
        </article>
      </ContentCard>
    </PageShell>
  );
}
