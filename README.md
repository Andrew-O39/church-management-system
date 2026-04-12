# Shepherd — Church Management System
> Built to help parishes care for their people with clarity, order, and trust.
## Short product description

**Shepherd** is a web application for parish administration and day-to-day church operations. 
Shepherd brings together two essential parts of parish life:

- **Official parish records** — membership, sacraments, and demographics  
- **Day-to-day operations** — events, volunteers, attendance, and communication

All in one clear and structured system.

Administrators manage registry data and app accounts; members and leaders use the same product for profiles, events, ministries, volunteers, and their notification inbox.

## Who this is for

- **Parish administrators** — manage records, events, volunteers, and communication  
- **Church members and leaders** — view events, serve in ministries, and receive notifications  

Shepherd is designed to be simple enough for daily parish use, while still supporting structured record keeping.

## Key concept: app users vs parish registry

Shepherd deliberately separates two ideas:

| | **Parish registry** | **App users** |
|---|---------------------|----------------|
| **What it is** | Official church office records (membership status, sacramental fields, registration numbers, etc.). | Accounts with email and password that **sign in** to Shepherd. |
| **Typical use** | Canonical records for the parish; CSV and print exports from the **Parish registry** area. | Identity for events, attendance, volunteers, in-app and external notifications (SMS/WhatsApp where configured). |
| **Relationship** | Adding or editing a registry row **does not** create a login. Linking a person’s registry record to an app user is **optional** and done by administrators when needed. | Operational features primarily use app users; registry and exports for registry data are maintained as a distinct concern. |

Understanding this split is essential for correct use of Shepherd and for interpreting exports (registry vs operational).

## Core features (grouped)
The system is organised around practical parish needs:
### Parish registry

- Search, filter, and paginate member records; **date-of-birth** and **sacramental date ranges** (baptism, first communion, confirmation, marriage).
- **Saved filter presets** (save, load, rename, remove) for repeat searches.
- CSV download and browser **print view** (Save as PDF via the print dialog).
- Registration numbers with validation and uniqueness rules.

### Events & operations

- Events (types, visibility, ministry scope), volunteer assignments and roles, per-event attendance for eligible app users.
- **Event reminders** (rules, channels, optional scheduler worker in Docker).
- Ministries (membership and roles).

### Notifications

- In-app inbox; admin tools to send notifications and run due reminders (globally or in event context).
- Optional **SMS** and **WhatsApp** delivery (provider integration and profile-based routing as implemented in the backend).

### Dashboard & exports

- Admin **dashboard** with operational summaries.
- **Audit log** (admin-only): a searchable history of important administrative and security-related actions (for example sign-ins, exports, registry and settings changes, notifications, events, attendance, and volunteer actions). It is stored in the database and supports **accountability** and basic **traceability** in the parish office—not a full analytics or compliance system.
- **Exports** page for operational CSV/print (attendance, volunteers, app users); registry exports remain on **Parish registry**.

### UX features

- Advanced filtering on registry and elsewhere as implemented per page.
- **Saved filters** on the parish registry list.
- **Collapsible sections** on long pages (e.g. registry, events, notifications, dashboard, exports) to reduce scrolling without changing business logic.

## Documentation

| Resource | Description |
|----------|-------------|
| [`USER_GUIDE.md`](USER_GUIDE.md) | Canonical **end-user** handbook (members and administrators). |
| [`SECURITY.md`](SECURITY.md) | Security and data-protection overview (plain language). |
| **In-app** | **`/guide`** — User Guide rendered in the Next.js app (content aligned with `USER_GUIDE.md`). **`/security`** — Security & Data Protection page (aligned with `SECURITY.md`). |

## Project structure

Repository layout (representative):

```
church-management-system/
  USER_GUIDE.md
  SECURITY.md
  README.md
  .env.example
  docker-compose.yml
  apps/
    backend/
      app/
        main.py
        api/
        core/
        db/
          models/
        modules/          # auth, members, church_registry, events, ministries,
                          # volunteers, attendance, notifications, event_reminders,
                          # exports, reports, registry_saved_filters, church_profile, audit_logs, users, ...
      alembic/
        versions/
      tests/
      pyproject.toml
      requirements.txt
      requirements-dev.txt
      Dockerfile
    frontend/
      app/                # Next.js App Router (routes include /, /members, /events, /guide, /security, …)
      components/
      lib/
      package.json
```

## Local development (Docker)

1. Copy environment file: `cp .env.example .env` and adjust secrets and passwords for your machine.
2. Build and start services:

   ```bash
   docker compose up --build
   ```

   This starts **PostgreSQL**, the **backend** API, the **frontend**, and a **reminder scheduler** worker (periodic check for due event reminders; configurable via `.env`).

3. **Apply database migrations** (first run and after schema changes):

   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. Verify:

   - Backend health: `http://localhost:8000/healthz`
   - API docs: `http://localhost:8000/docs`
   - Frontend: `http://localhost:3000`

### Useful commands when iterating

- Rebuild backend image after dependency changes: `docker compose build backend`
- Create migrations after model edits (from a shell with the app and DB configured): `alembic revision --autogenerate -m "..."` — review the migration, then `alembic upgrade head`

### Database backups (PostgreSQL)

Shepherd includes a **`pg_dump`-based backup CLI** (plain SQL, timestamped files, configurable retention).

**Client / server version:** `pg_dump` and `psql` should be the **same major version** as your PostgreSQL server (or compatible—typically match majors). Mismatch (e.g. client 17 with server 16) can cause restore errors such as unrecognized server parameters in the dump. The backend Docker image installs **`postgresql-client-16`** to align with the **`postgres:16`** service in `docker-compose.yml`. If you upgrade the database image to PostgreSQL 17, bump the client package in `apps/backend/Dockerfile` accordingly. On bare-metal installs, install the matching `postgresql-client` major from your OS or [PostgreSQL’s APT/YUM repos](https://www.postgresql.org/download/).

- **Configuration** (environment variables, see `apps/backend/.env.example`):
  - `BACKUP_ENABLED` — set `false` to skip runs (default `true`).
  - `BACKUP_DIR` — directory for dump files (Docker Compose defaults to `/backups` with a named volume `shepherd_backups`).
  - `BACKUP_RETENTION_COUNT` — how many recent backups to keep; older files are deleted after each successful run.
  - `BACKUP_FILE_PREFIX` — filename prefix (e.g. `shepherd_pg` → `shepherd_pg_20260410T120000Z.sql`).

- **Run a backup (Docker)** — with the stack up:

  ```bash
  docker compose exec backend poetry run backup-db
  ```

  The backend image includes PostgreSQL **16** client tools (see Dockerfile). Logs include `backup ok` with path and size on success.

- **Run a backup (local venv)** — install **`postgresql-client`** for the **same major** as your server (e.g. `postgresql-client-16` on Debian/Ubuntu via PGDG), then from `apps/backend`:

  ```bash
  poetry run backup-db
  # or, with pip + PYTHONPATH:
  python -m app.cli.backup_db
  ```

- **Restore** — backups are **logical SQL** dumps. Use `psql` against an **empty or disposable** database. See `apps/backend/scripts/restore_db.sh` and the comments inside it. **Always test restores on a copy**; restoring over production data is destructive.

- **Automation** — schedule `backup-db` with **cron**, **systemd timers**, or your host’s job runner; this repo does not ship a separate backup container by default.

**Production:** set `ENVIRONMENT=production` (or `staging`), a **long random `JWT_SECRET`**, explicit **`CORS_ORIGINS`** (no `*`), and optionally **`TRUSTED_HOSTS`** (comma-separated hostnames) so the API can validate the `Host` header. The backend **refuses to start** if production/staging secrets look like placeholders.

**Auth endpoints** apply a **simple per-IP rate limit** on `/auth/login` and `/auth/register` (in-memory, per server process).

## Local development (without Docker)

Requires **PostgreSQL** and a `DATABASE_URL` compatible with the backend (see `apps/backend/.env.example`).

**Backend**

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env   # edit DATABASE_URL and secrets
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd apps/frontend
npm install
cp .env.example .env.local   # e.g. NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

**Event reminders in development:** Without Docker, there is no separate scheduler container; use the API’s reminder job endpoint or run the CLI entrypoint defined in `pyproject.toml` if you need periodic processing locally.

## Tests

**Backend** (pytest):

```bash
cd apps/backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

The frontend uses `npm run lint` for static checks; add automated UI tests as the project evolves.

## Architecture notes

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), **SQLAlchemy 2** (async) with **asyncpg**, **Alembic** migrations, **JWT**-based auth and role checks, modular packages under `app/modules/<domain>/`.
- **Frontend:** [Next.js 14](https://nextjs.org/) (App Router), **TypeScript**, **Tailwind CSS**, client-side API calls to the backend using configured `NEXT_PUBLIC_API_BASE_URL`.
- **Health:** `/healthz` (liveness); `/readyz` includes database connectivity where implemented.
- **Single-tenant** deployment with optional placeholders (`TENANCY_MODE` / `TENANT_ID`) for future multi-tenant evolution—see backend settings.

## Security summary

Shepherd is designed with data protection in mind.

- Access is limited to authorised users through secure sign-in  
- Sensitive areas (such as the parish registry) are protected on the **server**, not just in the interface  
- Data is stored securely and is **not publicly accessible**  
- The system separates operational users from official registry records to reduce risk  

For a full, plain-language explanation, see [`SECURITY.md`](SECURITY.md) or visit **/security** in the app.

## Possible next steps

- Production hardening (HTTPS termination, secrets management, off-site backup copies, monitoring).
- Deeper reporting and analytics as parish needs grow.
- Broader automated test coverage (API integration tests, frontend E2E).
- Multi-tenant or multi-parish models only if product direction requires them.

These items depend on product and hosting choices—not fixed commitments.
