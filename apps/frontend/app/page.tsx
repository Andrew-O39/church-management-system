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
    <section className="mx-auto max-w-6xl space-y-20 pt-4 pb-12 sm:pt-6 sm:pb-20">
      <div className="grid gap-12 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div className="space-y-8">
          <div className="flex items-center gap-4">
            <div className="rounded-3xl border border-indigo-200 bg-white p-3 shadow-sm">
              <ShepherdLogo className="h-14 w-14 sm:h-16 sm:w-16" />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-indigo-700">
                Shepherd
              </p>
              <p className="text-sm text-slate-600">Church management workspace</p>
            </div>
          </div>

          <div className="space-y-5">
            <h1 className="max-w-4xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Serve and care for your parish with clarity, order, and trust.
            </h1>
            <p className="max-w-2xl text-lg leading-relaxed text-slate-700 sm:text-xl">
              Shepherd helps your church care for its people by bringing together official parish
              records, events, volunteers, attendance, and communication in one calm and organised
              workspace.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-sm">
            <span className={notificationChannelClass("in_app")}>In-app notifications</span>
            <span className={notificationChannelClass("sms")}>SMS messaging</span>
            <span className={notificationChannelClass("whatsapp")}>WhatsApp messaging</span>
          </div>
        </div>

        <div className="rounded-[2rem] border border-slate-300/90 bg-white p-7 shadow-lg shadow-slate-900/[0.06] ring-1 ring-slate-200/70">
          <div className="space-y-5">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-indigo-700">
                Why Shepherd
              </p>
              <h2 className="mt-2 text-2xl font-bold text-slate-900">
                Built for churches that want to stay connected and keep faithful records.
              </h2>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Keep parish life organised</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">
                  Manage events, ministries, volunteers, and reminders without losing track of
                  people.
                </p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Preserve official records</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">
                  Preserve your parish registry records for membership, sacraments, and administration
                  with care.
                </p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Communicate clearly</p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">
                  Reach the right people through in-app messages, SMS, and WhatsApp when needed.
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
            Shepherd supports both the daily life of the parish and the careful keeping of its
            records, helping your church serve people well without losing sight of its history.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <FeatureCard
            title="Parish registry"
            description="Keep official church records for membership, sacraments, demographics, and parish administration."
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

          <div className="flex flex-col items-stretch gap-3 sm:items-end">
            <div className="flex flex-wrap gap-3">
              <Link href="/login" className={`${btnPrimary} px-5 py-3 text-base`}>
                Sign in
              </Link>
              <Link href="/register" className={`${btnSecondary} px-5 py-3 text-base`}>
                Create account
              </Link>
            </div>
            <p className="text-center text-sm text-slate-600 sm:text-right">
              <Link
                href="/guide"
                className="font-medium text-indigo-800 underline-offset-2 hover:text-indigo-950 hover:underline"
              >
                Read the Shepherd user guide
              </Link>
              <span className="mx-2 text-slate-400" aria-hidden>
                ·
              </span>
              <Link
                href="/security"
                className="font-medium text-indigo-800 underline-offset-2 hover:text-indigo-950 hover:underline"
              >
                Learn how Shepherd protects parish data
              </Link>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}