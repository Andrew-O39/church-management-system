import Link from "next/link";

import { btnPrimary, btnSecondary } from "lib/ui";

export default function HomePage() {
  return (
    <section className="space-y-10">
      <div className="space-y-3">
        <h1 className="shepherd-page-title">Shepherd</h1>
        <p className="max-w-2xl text-base font-medium leading-relaxed text-slate-700">
          A calm workspace for your church—profiles, events, volunteers, and staying in touch with your
          people.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link href="/login" className={btnPrimary}>
          Sign in
        </Link>
        <Link href="/register" className={btnSecondary}>
          Create account
        </Link>
      </div>
    </section>
  );
}
