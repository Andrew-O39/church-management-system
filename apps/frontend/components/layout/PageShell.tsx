import type { ReactNode } from "react";

type PageShellProps = {
  title: string;
  description?: ReactNode;
  children: ReactNode;
};

export default function PageShell({ title, description, children }: PageShellProps) {
  return (
    <div className="space-y-8">
      <header className="space-y-2 border-b border-slate-200/80 pb-6">
        <h1 className="shepherd-page-title">{title}</h1>
        {description ? (
          <div className="max-w-2xl text-base font-medium leading-relaxed text-slate-700">{description}</div>
        ) : null}
      </header>
      {children}
    </div>
  );
}

type ContentCardProps = {
  children: ReactNode;
  className?: string;
};

export function ContentCard({ children, className = "" }: ContentCardProps) {
  return (
    <div
      className={[
        "rounded-2xl border border-slate-300/95 bg-white p-6 shadow-md shadow-slate-900/[0.07] ring-1 ring-slate-900/[0.06] sm:p-7",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
