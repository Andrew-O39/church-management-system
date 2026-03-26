import type { ReactNode } from "react";

type PageShellProps = {
  title: string;
  description?: string;
  children: ReactNode;
};

export default function PageShell({ title, description, children }: PageShellProps) {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {description ? (
          <p className="max-w-2xl text-sm text-slate-600">{description}</p>
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
      className={["rounded-xl border border-slate-200/80 bg-white p-6 shadow-sm", className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
