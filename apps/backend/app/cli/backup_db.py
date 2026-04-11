"""Run a PostgreSQL logical backup (pg_dump) and apply retention. Intended for cron / manual ops."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.core.backup_logic import (
    backup_file_name,
    files_to_remove_for_retention,
    list_sql_backups,
    parse_database_url_for_pg_dump,
)
from app.core.settings import settings

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if not settings.BACKUP_ENABLED:
        logger.info("backup skipped BACKUP_ENABLED=false")
        sys.exit(0)

    backup_root = Path(settings.BACKUP_DIR).expanduser().resolve()
    try:
        backup_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("backup failed cannot_create_dir path=%s error=%s", backup_root, e)
        sys.exit(1)

    if shutil.which("pg_dump") is None:
        logger.error(
            "backup failed pg_dump_not_found install postgresql-client "
            "(e.g. apt install postgresql-client) or run from an image that includes it"
        )
        sys.exit(1)

    try:
        target = parse_database_url_for_pg_dump(settings.DATABASE_URL)
    except ValueError as e:
        logger.error("backup failed invalid_database_url error=%s", e)
        sys.exit(1)

    prefix = settings.BACKUP_FILE_PREFIX.strip() or "shepherd_pg"
    fname = backup_file_name(prefix, datetime.now(timezone.utc))
    out_path = backup_root / fname

    env = os.environ.copy()
    env["PGPASSWORD"] = target.password

    cmd = [
        "pg_dump",
        "-h",
        target.host,
        "-p",
        str(target.port),
        "-U",
        target.user,
        "-d",
        target.database,
        "-F",
        "p",
        "--no-owner",
        "--no-acl",
        "-f",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(
            "backup failed pg_dump_exit=%s stderr=%s stdout=%s",
            e.returncode,
            (e.stderr or "")[:2000],
            (e.stdout or "")[:500],
        )
        if out_path.exists():
            try:
                out_path.unlink()
            except OSError:
                pass
        sys.exit(e.returncode or 1)

    logger.info(
        "backup ok path=%s size_bytes=%s retention_keep=%s",
        out_path,
        out_path.stat().st_size,
        settings.BACKUP_RETENTION_COUNT,
    )

    existing = list_sql_backups(backup_root, prefix)
    to_delete = files_to_remove_for_retention(existing, settings.BACKUP_RETENTION_COUNT)
    for p in to_delete:
        try:
            p.unlink()
            logger.info("backup retention removed path=%s", p)
        except OSError as e:
            logger.warning("backup retention unlink_failed path=%s error=%s", p, e)


if __name__ == "__main__":
    main()
