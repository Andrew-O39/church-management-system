#!/usr/bin/env bash
# Restore a plain-SQL backup produced by `poetry run backup-db` (pg_dump -F p).
#
# Prerequisites:
#   - psql from a postgresql-client whose major version matches the server (mismatch can
#     cause errors such as unrecognized configuration parameters).
#   - a target database you are allowed to write to.
#
# Usage:
#   export DATABASE_URL='postgresql://USER:PASSWORD@HOST:PORT/DBNAME'
#   ./scripts/restore_db.sh /path/to/shepherd_pg_20260410T120000Z.sql
#
# Typical recovery flow:
#   1. Stop the Shepherd backend (and anything connected to the DB).
#   2. Create an empty database (or drop/recreate schemas) per your policy.
#   3. Run this script pointing at that database.
#   4. Run `alembic upgrade head` only if you need to reconcile migration history —
#      restoring a full dump usually already matches the schema at backup time.
#
# WARNING: Restoring over an existing database can destroy data. Test on a copy first.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: DATABASE_URL=postgresql://... $0 <backup.sql>" >&2
  exit 1
fi

SQL_FILE="$1"
if [[ ! -f "$SQL_FILE" ]]; then
  echo "error: file not found: $SQL_FILE" >&2
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "error: DATABASE_URL must be set (sync URL, e.g. postgresql://user:pass@host:5432/dbname)" >&2
  exit 1
fi

# Strip SQLAlchemy async driver if present
export DATABASE_URL
SYNC_URL="${DATABASE_URL#postgresql+asyncpg://}"
SYNC_URL="postgresql://${SYNC_URL#postgresql://}"

echo "Restoring from: $SQL_FILE"
psql "$SYNC_URL" -v ON_ERROR_STOP=1 -f "$SQL_FILE"
echo "Restore finished."
