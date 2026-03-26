import type { ReactNode } from "react";

import "./globals.css";
import AppHeader from "../components/layout/AppHeader";
import { Providers } from "./providers";

export const metadata = {
  title: "Church Management System",
  description: "Member directory, profiles, and church administration.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AppHeader />

          <main className="mx-auto max-w-5xl p-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}

