"""Pure helpers for PostgreSQL backup filenames, retention, and connection parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class PgDumpTarget:
    """Sync connection parameters for pg_dump (not asyncpg)."""

    host: str
    port: int
    user: str
    password: str
    database: str


def parse_database_url_for_pg_dump(database_url: str) -> PgDumpTarget:
    """
    Parse SQLAlchemy-style DATABASE_URL into parameters for pg_dump.

    Supports postgresql+asyncpg:// and postgresql:// URLs.
    """
    raw = database_url.strip()
    if "://" not in raw:
        msg = "DATABASE_URL must include a scheme"
        raise ValueError(msg)
    # Normalize driver to postgresql for urlparse
    normalized = re.sub(r"^postgresql\+[^/]+://", "postgresql://", raw, count=1)
    parsed = urlparse(normalized)
    if parsed.scheme != "postgresql" or not parsed.hostname:
        msg = "DATABASE_URL must be a PostgreSQL URL with a host"
        raise ValueError(msg)
    dbname = (parsed.path or "").lstrip("/")
    if not dbname:
        msg = "DATABASE_URL must include a database name in the path"
        raise ValueError(msg)
    user = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    if not user:
        msg = "DATABASE_URL must include a username"
        raise ValueError(msg)
    port = parsed.port or 5432
    host = parsed.hostname
    return PgDumpTarget(
        host=host,
        port=port,
        user=user,
        password=password,
        database=dbname,
    )


def backup_file_name(prefix: str, ts: datetime | None = None) -> str:
    """Return a timestamped filename like shepherd_pg_20260410T120000Z.sql."""
    t = ts or datetime.now(timezone.utc)
    safe_prefix = prefix.strip() or "shepherd_pg"
    stamp = t.strftime("%Y%m%dT%H%M%SZ")
    return f"{safe_prefix}_{stamp}.sql"


def list_sql_backups(backup_dir: Path, prefix: str) -> list[Path]:
    """Return backup files for this prefix, oldest first."""
    if not backup_dir.is_dir():
        return []
    safe = prefix.strip() or "shepherd_pg"
    pat = re.compile(rf"^{re.escape(safe)}_\d{{8}}T\d{{6}}Z\.sql$")
    files = [p for p in backup_dir.iterdir() if p.is_file() and pat.match(p.name)]
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def files_to_remove_for_retention(paths: list[Path], retention_count: int) -> list[Path]:
    """
    Given sorted paths (oldest first), return which files should be deleted
    to keep at most retention_count newest files.
    """
    if retention_count < 1:
        return list(paths)
    if len(paths) <= retention_count:
        return []
    excess = len(paths) - retention_count
    return paths[:excess]
