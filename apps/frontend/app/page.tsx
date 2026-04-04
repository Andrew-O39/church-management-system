import Link from "next/link";

import ShepherdLogo from "components/brand/ShepherdLogo";
import { btnPrimary, btnSecondary, notificationChannelClass } from "lib/ui";

function FeatureCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-300/90 bg-white p-6 shadow-md shadow-slate-900/[0.04] ring-1 ring-slate-200/70">
      <h3 className="text-lg font-bold text-slate-900">{title}</h3>
      <p className="mt-2 text-base leading-relaxed text-slate-700">{description}</p>
    </div>
  );
}

export default function HomePage() {
  return (
    <section className="mx-auto max-w-6xl space-y-16 py-10 sm:py-16">
      <div className="grid gap-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div className="space-y-6">
          <div className="inline-flex items-center gap-3 rounded-full border border-indigo-200 bg-white px-4 py-2 text-sm font-semibold text-indigo-800 shadow-sm">
            <ShepherdLogo className="h-8 w-8" />
            Shepherd
          </div>

          <div className="space-y-4">
            <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              Care for your church community with clarity and confidence.
            </h1>
            <p className="max-w-2xl text-lg leading-relaxed text-slate-700">
              Shepherd helps your church manage app users, events, volunteers, attendance, reminders,
              and communication in one calm, organised workspace.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <Link href="/login" className={`${btnPrimary} px-6 py-3 text-base shadow-md shadow-indigo-900/20`}>
              Sign in
            </Link>
            <Link href="/register" className={`${btnSecondary} px-6 py-3 text-base`}>
              Create account
            </Link>
          </div>

          <div className="flex flex-wrap gap-2 pt-1 text-sm">
            <span className={notificationChannelClass("in_app")}>In-app notifications</span>
            <span className={notificationChannelClass("sms")}>SMS messaging</span>
            <span className={notificationChannelClass("whatsapp")}>WhatsApp messaging</span>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-300/90 bg-white p-6 shadow-lg shadow-slate-900/[0.06] ring-1 ring-slate-200/70">
          <div className="space-y-5">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-indigo-700">Why Shepherd</p>
              <h2 className="mt-2 text-2xl font-bold text-slate-900">Built for churches that want to stay connected.</h2>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Keep everyone organised</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">
                  Manage events, ministries, volunteers, and reminders without losing track of people.
                </p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Communicate clearly</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">
                  Send messages in-app, by SMS, or by WhatsApp to the right app users at the right time.
                </p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Stay prepared</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">
                  Schedule reminders before events so volunteers and participants are not left behind.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="shepherd-section-title">Everything your church needs to stay coordinated</h2>
          <p className="max-w-3xl text-base leading-relaxed text-slate-700">
            Shepherd keeps your operational work focused on app users while preserving a separate parish
            registry for archival church records.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <FeatureCard
            title="App users"
            description="Manage the people who use the app, update their details, and keep account records organised."
          />
          <FeatureCard
            title="Events and reminders"
            description="Create events, configure reminder rules, and keep everyone informed before things begin."
          />
          <FeatureCard
            title="Volunteers and attendance"
            description="Coordinate service roles and record attendance with clear, practical workflows."
          />
          <FeatureCard
            title="Notifications"
            description="Send messages by in-app notification, SMS, or WhatsApp and keep track of delivery."
          />
        </div>
      </div>

      <div className="rounded-3xl border border-indigo-200 bg-indigo-50/80 p-8 shadow-sm">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-bold text-slate-900">Ready to get started?</h2>
            <p className="mt-2 text-base leading-relaxed text-slate-700">
              Sign in to continue your work, or create an account to join your church’s workspace.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link href="/login" className={`${btnPrimary} px-5 py-3 text-base`}>
              Sign in
            </Link>
            <Link href="/register" className={`${btnSecondary} px-5 py-3 text-base`}>
              Create account
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}