"""Raqamlangan SQL migratsiyalar. Har fayl bir marta, tartib bilan qo'llanadi."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path

from uzwatermu.db.connection import connect

_NAME = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


class SchemaError(RuntimeError):
    pass


def available_migrations() -> list[tuple[int, str, str]]:
    folder = resources.files("uzwatermu.db") / "migrations"
    found = []
    for item in folder.iterdir():
        match = _NAME.match(item.name)
        if match:
            found.append((int(match.group(1)), item.name, item.read_text(encoding="utf-8")))
    found.sort()
    versions = [version for version, _, _ in found]
    if versions != list(range(1, len(versions) + 1)):
        raise SchemaError(f"Migratsiya raqamlari ketma-ket emas: {versions}")
    return found


def current_version(path: Path) -> int:
    with connect(path) as db:
        exists = db.execute(
            "select 1 from sqlite_master where type='table' and name='schema_version'"
        ).fetchone()
        if not exists:
            return 0
        row = db.execute("select max(version) from schema_version").fetchone()
        return int(row[0] or 0)


def migrate(path: Path) -> int:
    """Bazani eng so'nggi versiyaga olib chiqadi va versiyani qaytaradi."""
    path.parent.mkdir(parents=True, exist_ok=True)
    version = current_version(path)
    for number, _name, sql in available_migrations():
        if number <= version:
            continue
        with connect(path) as db:
            db.executescript(
                f"begin;\n{sql}\n"
                f"insert into schema_version(version) values ({int(number)});\ncommit;"
            )
        version = number
    return version


def verify(path: Path) -> None:
    """Startda chaqiriladi: baza mavjud va to'liq versiyada bo'lmasa ishga tushmaydi."""
    if not path.exists():
        raise SchemaError(f"Baza topilmadi: {path}. Avval `python -m uzwatermu migrate` bajaring.")
    expected = len(available_migrations())
    actual = current_version(path)
    if actual != expected:
        raise SchemaError(
            f"Baza sxemasi versiyasi {actual}, kutilgan {expected}. "
            "Baza bo'sh, eski yoki noto'g'ri fayl bo'lishi mumkin. "
            "`python -m uzwatermu migrate` bajaring yoki DATA_DIR ni tekshiring."
        )
