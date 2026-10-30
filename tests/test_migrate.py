import sqlite3

import pytest

from uzwatermu.db.migrate import SchemaError, available_migrations, current_version, migrate, verify


def test_migrate_creates_latest_schema(db_path):
    assert current_version(db_path) == len(available_migrations())
    verify(db_path)


def test_migrate_is_idempotent(db_path):
    before = current_version(db_path)
    assert migrate(db_path) == before


def test_verify_rejects_missing_database(tmp_path):
    with pytest.raises(SchemaError):
        verify(tmp_path / "yoq.sqlite3")


def test_verify_rejects_empty_database(tmp_path):
    # v1 dagi incident: bo'sh SQLite fayl bilan bot jim ishlayverdi.
    path = tmp_path / "bot.sqlite3"
    sqlite3.connect(path).close()
    with pytest.raises(SchemaError):
        verify(path)
