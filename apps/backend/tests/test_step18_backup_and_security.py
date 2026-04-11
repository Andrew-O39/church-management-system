from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.backup_logic import (
    backup_file_name,
    files_to_remove_for_retention,
    list_sql_backups,
    parse_database_url_for_pg_dump,
)
from app.core.env_validation import validate_settings_for_environment
from app.core.rate_limit import SimpleWindowRateLimiter
from app.core.settings import Settings


def test_parse_database_url_for_pg_dump() -> None:
    t = parse_database_url_for_pg_dump(
        "postgresql+asyncpg://myuser:mypass@db.internal:5433/mydb",
    )
    assert t.host == "db.internal"
    assert t.port == 5433
    assert t.user == "myuser"
    assert t.password == "mypass"
    assert t.database == "mydb"


def test_parse_database_url_encoded_password() -> None:
    t = parse_database_url_for_pg_dump(
        "postgresql+asyncpg://u:p%40ss%3Aword@localhost:5432/db",
    )
    assert t.password == "p@ss:word"


def test_backup_file_name_format() -> None:
    ts = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)
    assert backup_file_name("pre", ts) == "pre_20260410T120000Z.sql"


def test_retention_deletes_oldest(tmp_path: Path) -> None:
    p = tmp_path
    for i in range(5):
        (p / f"shepherd_pg_2026040{i}T120000Z.sql").write_text("x")
    paths = sorted(p.glob("*.sql"), key=lambda x: x.stat().st_mtime)
    to_remove = files_to_remove_for_retention(paths, retention_count=2)
    assert len(to_remove) == 3


def test_list_sql_backups_filters_prefix(tmp_path: Path) -> None:
    (tmp_path / "shepherd_pg_20260410T120000Z.sql").write_text("a")
    (tmp_path / "other_20260410T120000Z.sql").write_text("b")
    found = list_sql_backups(tmp_path, "shepherd_pg")
    assert len(found) == 1


def test_rate_limiter_blocks_after_max() -> None:
    lim = SimpleWindowRateLimiter(3, window_seconds=60)
    assert lim.allow("a") is True
    assert lim.allow("a") is True
    assert lim.allow("a") is True
    assert lim.allow("a") is False


def test_production_requires_strong_jwt() -> None:
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="change_me_in_real_env",
        CORS_ORIGINS="https://app.example.com",
    )
    with pytest.raises(ValueError, match="JWT_SECRET"):
        validate_settings_for_environment(s)


def test_production_requires_long_jwt() -> None:
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="x" * 20,
        CORS_ORIGINS="https://app.example.com",
    )
    with pytest.raises(ValueError, match="32"):
        validate_settings_for_environment(s)


def test_production_rejects_wildcard_cors() -> None:
    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="x" * 40,
        CORS_ORIGINS="*,https://a.com",
    )
    with pytest.raises(ValueError, match="CORS"):
        validate_settings_for_environment(s)


def test_local_allows_dev_defaults() -> None:
    s = Settings(
        ENVIRONMENT="local",
        JWT_SECRET="change_me_in_real_env",
        CORS_ORIGINS="http://localhost:3000",
    )
    validate_settings_for_environment(s)
