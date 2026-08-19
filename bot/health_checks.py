from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from bot.backup_manager import latest_valid_backup, validate_excel, validate_sqlite


@dataclass(frozen=True)
class CheckResult:
    name: str
    level: str
    message: str


@dataclass(frozen=True)
class PreflightReport:
    checked_at: str
    status: str
    results: tuple[CheckResult, ...]

    @property
    def critical(self) -> bool:
        return any(item.level == "critical" for item in self.results)

    @property
    def warnings(self) -> int:
        return sum(item.level == "warning" for item in self.results)


def _run_check(
    name: str,
    callback: Callable[[], str],
    *,
    failure_level: str,
) -> CheckResult:
    try:
        return CheckResult(name, "ok", callback())
    except Exception as error:
        return CheckResult(name, failure_level, str(error))


def _required_file(path: Path, validator: Callable[[Path], None]) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Majburiy fayl topilmadi: {path}")
    if path.stat().st_size <= 0:
        raise RuntimeError(f"Fayl bo'sh: {path}")
    validator(path)
    return f"{path.name}: {path.stat().st_size} bayt"


def _disk_check(
    path: Path,
    minimum_free_gb: float,
    minimum_free_percent: float,
) -> str:
    usage = shutil.disk_usage(path.resolve().anchor or path)
    free_gb = usage.free / (1024**3)
    free_percent = usage.free / usage.total * 100
    if free_gb < minimum_free_gb or free_percent < minimum_free_percent:
        raise RuntimeError(
            f"Disk bo'sh joyi kam: {free_gb:.2f} GB "
            f"({free_percent:.1f}%). Minimum: {minimum_free_gb:g} GB "
            f"va {minimum_free_percent:g}%."
        )
    return f"{free_gb:.2f} GB bo'sh ({free_percent:.1f}%)"


def _backup_check(
    backup_dir: Path,
    encryption_password: str | None,
    maximum_age_hours: float,
) -> str:
    backup = latest_valid_backup(backup_dir, encryption_password)
    if backup is None:
        raise RuntimeError("Sog'lom backup topilmadi.")
    age = datetime.now() - backup.created_at
    if age > timedelta(hours=maximum_age_hours):
        raise RuntimeError(
            f"Oxirgi sog'lom backup eskirgan: "
            f"{backup.created_at.strftime('%d.%m.%Y %H:%M')}."
        )
    return (
        f"{backup.created_at.strftime('%d.%m.%Y %H:%M')}, "
        f"{len(backup.files)} fayl"
    )


def run_preflight_checks(
    *,
    database_file: str | Path,
    excel_file: str | Path,
    inspectors_file: str | Path,
    backup_dir: str | Path,
    encryption_password: str | None,
    backup_maximum_age_hours: float,
    minimum_free_gb: float,
    minimum_free_percent: float,
) -> PreflightReport:
    database = Path(database_file)
    abonents = Path(excel_file)
    inspectors = Path(inspectors_file)
    results = (
        _run_check(
            "database",
            lambda: _required_file(database, validate_sqlite),
            failure_level="critical",
        ),
        _run_check(
            "abonents_excel",
            lambda: _required_file(abonents, validate_excel),
            failure_level="critical",
        ),
        _run_check(
            "inspectors_excel",
            lambda: _required_file(inspectors, validate_excel),
            failure_level="critical",
        ),
        _run_check(
            "disk_space",
            lambda: _disk_check(
                database.parent,
                minimum_free_gb,
                minimum_free_percent,
            ),
            failure_level="warning",
        ),
        _run_check(
            "latest_backup",
            lambda: _backup_check(
                Path(backup_dir),
                encryption_password,
                backup_maximum_age_hours,
            ),
            failure_level="warning",
        ),
    )
    status = (
        "critical"
        if any(item.level == "critical" for item in results)
        else "warning"
        if any(item.level == "warning" for item in results)
        else "ok"
    )
    return PreflightReport(
        checked_at=datetime.now().isoformat(timespec="seconds"),
        status=status,
        results=results,
    )


def write_preflight_report(
    report: PreflightReport,
    path: str | Path,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "checked_at": report.checked_at,
        "status": report.status,
        "results": [asdict(item) for item in report.results],
    }
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def preflight_summary(report: PreflightReport) -> str:
    icons = {"ok": "✅", "warning": "⚠️", "critical": "❌"}
    lines = [f"Preflight: {report.status.upper()}"]
    for item in report.results:
        lines.append(
            f"{icons.get(item.level, '•')} {item.name}: {item.message}"
        )
    return "\n".join(lines)
