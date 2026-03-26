# Church Management System — Backend

FastAPI service for the church CMS monorepo.

## Tech stack

- FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic
- PostgreSQL (asyncpg) in Docker; SQLite (aiosqlite) in tests
- JWT auth (HS256), passlib/bcrypt

## Local setup

1. Install dependencies (Poetry recommended):

   ```bash
   cd apps/backend
   poetry install
   ```

2. Configure `.env` (optional; defaults exist in `app/core/settings.py`). Important variables:

   - `DATABASE_URL` — async SQLAlchemy URL, e.g. `postgresql+asyncpg://user:pass@localhost:5432/dbname`
   - `JWT_SECRET` — set to a strong secret outside local dev
   - `BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` — optional; see below

3. Run migrations:

   ```bash
   poetry run alembic upgrade head
   ```

4. **Bootstrap first admin (development)** — after migrations, with env vars set:

   ```bash
   export BOOTSTRAP_ADMIN_EMAIL=admin@example.com
   export BOOTSTRAP_ADMIN_PASSWORD='your-secure-password-here'
   poetry run bootstrap-admin
   ```

   Idempotent: re-running does not create a second admin for the same email (skips if already admin; promotes an existing non-admin user with that email).

5. Run the API:

   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Tests

```bash
cd apps/backend
poetry run pytest tests/ -v
```

Tests use an in-memory SQLite database and override the FastAPI DB session dependency (`tests/conftest.py`).

## API overview (Step 3)

All JSON routes are under `API_PREFIX` (default `/api/v1`).

### Auth (Step 2)

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET /auth/admin/ping` — admin-only smoke test

### Members / directory (Step 3)

- `GET /members/` — **admin only** — paginated directory (`page`, `page_size`, optional `search`, `role`, `is_active`)
- `GET /members/{member_id}` — **admin only** — detail (`member_id` is the **user** UUID)
- `PATCH /members/{member_id}` — **admin only** — update account + profile fields (see OpenAPI schema)
- `GET /members/me/profile` — **authenticated** — current user detail
- `PATCH /members/me/profile` — **authenticated** — self-service fields only (`MemberSelfPatch`; extra fields → 422)

Canonical login email is always `User.email` (normalized: lowercased, stripped). Optional directory email is `MemberProfile.contact_email`.

## Docker

From repo root: `docker compose up --build` — backend uses `DATABASE_URL` pointing at the `postgres` service. Run Alembic and `bootstrap-admin` inside the backend container when the DB is fresh.
