import type { ReactNode } from "react";

import "./globals.css";
import TopNav from "../components/layout/TopNav";

export const metadata = {
  title: "Church Management System",
  description: "A modern church admin platform (foundation scaffold)",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b bg-white">
          <TopNav />
        </header>

        <main className="mx-auto max-w-5xl p-6">{children}</main>
      </body>
    </html>
  );
}

