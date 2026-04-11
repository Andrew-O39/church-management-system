"use client";

import { useEffect } from "react";
import Link from "next/link";

import PageShell, { ContentCard } from "components/layout/PageShell";
import UserGuideArticle from "./UserGuideArticle";

const toc = [
  { href: "#purpose-of-shepherd", label: "Purpose of Shepherd" },
  { href: "#getting-started", label: "Getting started" },
  { href: "#navigation-overview", label: "Navigation overview" },
  {
    href: "#user-guide-normal-members-and-leaders",
    label: "User guide — normal members and leaders",
  },
  {
    href: "#user-guide-parish-administrators",
    label: "User guide — parish administrators",
  },
  { href: "#page-by-page-quick-reference", label: "Page-by-page quick reference" },
  { href: "#common-tasks", label: "Common tasks" },
  { href: "#tips-and-troubleshooting", label: "Tips and troubleshooting" },
  { href: "#current-limitations", label: "Current limitations" },
  { href: "#glossary", label: "Glossary" },
];

export default function GuidePage() {
  useEffect(() => {
    document.documentElement.setAttribute("data-user-guide-doc", "1");
    return () => document.documentElement.removeAttribute("data-user-guide-doc");
  }, []);

  return (
    <PageShell title="User Guide" description="How to use Shepherd">
      <p className="no-print max-w-4xl rounded-lg border border-slate-200/90 bg-slate-50/80 px-4 py-3 text-sm leading-relaxed text-slate-700">
        This guide explains how to use Shepherd as an admin or normal user.
      </p>

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

      <ContentCard className="user-guide-doc-print max-w-4xl print:border-0 print:shadow-none print:ring-0">
        <UserGuideArticle />
      </ContentCard>
    </PageShell>
  );
}
