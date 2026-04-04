import type { ReactNode } from "react";
import { Source_Sans_3 } from "next/font/google";

import "./globals.css";
import AppHeader from "../components/layout/AppHeader";
import { Providers } from "./providers";

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata = {
  title: "Shepherd",
  description:
    "Shepherd helps churches care for people well—member directory, events, volunteers, and notifications in one calm, modern workspace.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={sourceSans.variable}>
      <body>
        <Providers>
          <AppHeader />

          <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
