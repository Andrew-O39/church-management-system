export default async function HomePage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  let health: unknown = null;
  let ready: unknown = null;

  try {
    const healthRes = await fetch(`${apiBase}/healthz`, { cache: "no-store" });
    health = await healthRes.json();
  } catch (err) {
    health = { status: "error", message: err instanceof Error ? err.message : String(err) };
  }

  try {
    const readyRes = await fetch(`${apiBase}/readyz`, { cache: "no-store" });
    ready = await readyRes.json();
  } catch (err) {
    ready = { status: "error", message: err instanceof Error ? err.message : String(err) };
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Church Management System</h1>
        <p className="mt-1 text-slate-700">
          Step 1 foundation scaffold: verifies backend wiring via health-check endpoints.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-900">Backend</h2>
        <p className="text-sm text-slate-600">Base URL: {apiBase}</p>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div className="rounded border p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">/healthz</p>
            <pre className="mt-2 overflow-auto rounded bg-slate-50 p-2 text-xs">
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>

          <div className="rounded border p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">/readyz</p>
            <pre className="mt-2 overflow-auto rounded bg-slate-50 p-2 text-xs">
              {JSON.stringify(ready, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}

