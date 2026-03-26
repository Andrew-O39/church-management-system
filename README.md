# Church Management System (CMS)

This repository is a production-minded scaffold for a multi-denomination Church Management System.

## What’s inside

- `apps/backend`: FastAPI app with modular domain structure, PostgreSQL + SQLAlchemy (async), Alembic migrations, JWT auth (Step 2+).
- `apps/frontend`: Next.js (App Router) + TypeScript + Tailwind landing page + placeholder future routes.
- `docker-compose.yml`: runs `frontend`, `backend`, and `postgres`.
- `alembic`: database migrations live under `apps/backend/alembic/`.

## Folder structure (high level)

```
church-management-system/
  apps/
    backend/
      app/
        core/
        db/
          models/
        modules/
        api/
        main.py
      alembic/
        versions/
      pyproject.toml
      requirements.txt
      tests/
    frontend/
      app/
      package.json
  docker-compose.yml
  .env.example
  README.md
```

## Local run (Docker)

1. Copy env example: `cp .env.example .env`
2. Build and start: `docker compose up --build`
3. **Apply database migrations** (first time / after schema changes):

   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. Verify:
   - Backend health: `http://localhost:8000/healthz`
   - API docs: `http://localhost:8000/docs`
   - Frontend: `http://localhost:3000`

### Auth endpoints (Step 2)

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (Bearer token)
- `GET /api/v1/auth/admin/ping` (admin only — RBAC smoke test)

## Local run (without Docker)

Requires **PostgreSQL** and matching `DATABASE_URL` in `apps/backend/.env` (see `apps/backend/.env.example`).

**Backend**

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for pytest / linters
cp .env.example .env && edit .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (optional for this step)

```bash
cd apps/frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

## Tests (backend)

```bash
cd apps/backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Architectural notes

- **Domains** are organized under `app/modules/<domain>/` (router/schemas/services).
- **Persistence models** live in `app/db/models/` and are registered on `Base.metadata` for Alembic.
- **Health vs readiness**: `/healthz` is soft; `/readyz` checks DB connectivity.
- **Single-tenant MVP** with `TENANCY_MODE` / `TENANT_ID` placeholders for later SaaS evolution.

## Next manual steps (when iterating)

- Rebuild backend image after dependency changes: `docker compose build backend`
- Create/adjust migrations after model edits: `alembic revision --autogenerate -m "..."` then review, then `alembic upgrade head`
