import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";

export const metadata = {
  title: "Church Management System",
  description: "A modern church admin platform (foundation scaffold)",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b bg-white">
          <div className="mx-auto flex max-w-5xl items-center gap-3 p-4">
            <Link href="/" className="font-semibold text-slate-900">
              Church CMS
            </Link>
            <nav className="flex items-center gap-4 text-sm text-slate-700">
              <Link href="/dashboard" className="hover:text-slate-900">
                Dashboard
              </Link>
              <Link href="/members" className="hover:text-slate-900">
                Members
              </Link>
              <Link href="/profile" className="hover:text-slate-900">
                Profile
              </Link>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-5xl p-6">{children}</main>
      </body>
    </html>
  );
}

