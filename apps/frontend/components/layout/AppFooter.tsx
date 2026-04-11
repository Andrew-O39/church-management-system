import Link from "next/link";

export default function AppFooter() {
  return (
    <footer className="app-site-footer mt-auto border-t border-slate-200/90 bg-white py-6">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <nav
          className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm sm:justify-start"
          aria-label="Site information"
        >
          <Link
            href="/security"
            className="text-slate-600 underline-offset-2 hover:text-slate-900 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 focus-visible:ring-offset-2"
          >
            Security & Data Protection
          </Link>
        </nav>
      </div>
    </footer>
  );
}
