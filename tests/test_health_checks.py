from __future__ import annotations

import shutil
import sqlite3
import unittest
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook

from bot.backup_manager import BackupFile, create_backup_set
from bot.health_checks import (
    preflight_summary,
    run_preflight_checks,
    write_preflight_report,
)


class HealthCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/health_checks") / self._testMethodName
        shutil.rmtree(self.root, ignore_errors=True)
        self.data = self.root / "data"
        self.storage = self.root / "storage"
        self.backups = self.root / "backups"
        self.data.mkdir(parents=True)
        self.storage.mkdir()
        self.database = self.storage / "bot.sqlite3"
        self.abonents = self.data / "abonents.xlsx"
        self.inspectors = self.data / "inspectors.xlsx"

        with closing(sqlite3.connect(self.database)) as database:
            database.execute("create table users (id integer primary key)")
            database.commit()
        self._excel(self.abonents, "account")
        self._excel(self.inspectors, "area")
        self._backup(datetime.now())

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def _excel(path: Path, header: str) -> None:
        workbook = Workbook()
        workbook.active["A1"] = header
        workbook.active["A2"] = "test"
        workbook.save(path)
        workbook.close()

    def _backup(self, now: datetime) -> None:
        create_backup_set(
            self.backups,
            [
                BackupFile("database", self.database, "bot.sqlite3"),
                BackupFile("abonents", self.abonents, "abonents.xlsx"),
                BackupFile("inspectors", self.inspectors, "inspectors.xlsx"),
            ],
            "health_test",
            now=now,
        )

    def _run(
        self,
        *,
        minimum_free_gb: float = 0,
        backup_maximum_age_hours: float = 48,
    ):
        return run_preflight_checks(
            database_file=self.database,
            excel_file=self.abonents,
            inspectors_file=self.inspectors,
            backup_dir=self.backups,
            encryption_password=None,
            backup_maximum_age_hours=backup_maximum_age_hours,
            minimum_free_gb=minimum_free_gb,
            minimum_free_percent=0,
        )

    def test_healthy_files_return_ok(self) -> None:
        report = self._run()
        self.assertEqual("ok", report.status)
        self.assertFalse(report.critical)
        self.assertEqual(0, report.warnings)

    def test_missing_database_is_critical_and_not_recreated(self) -> None:
        self.database.unlink()
        report = self._run()
        self.assertEqual("critical", report.status)
        self.assertTrue(report.critical)
        self.assertFalse(self.database.exists())

    def test_corrupted_excel_is_critical(self) -> None:
        self.abonents.write_bytes(b"not an xlsx file")
        report = self._run()
        result = next(
            item
            for item in report.results
            if item.name == "abonents_excel"
        )
        self.assertEqual("critical", result.level)

    def test_old_backup_is_warning(self) -> None:
        shutil.rmtree(self.backups)
        self._backup(datetime.now() - timedelta(days=5))
        report = self._run(backup_maximum_age_hours=48)
        self.assertEqual("warning", report.status)
        self.assertFalse(report.critical)

    def test_low_disk_space_is_warning(self) -> None:
        report = self._run(minimum_free_gb=10**9)
        disk = next(
            item for item in report.results if item.name == "disk_space"
        )
        self.assertEqual("warning", disk.level)

    def test_report_is_written_as_json(self) -> None:
        report = self._run()
        path = self.root / "logs" / "preflight.json"
        write_preflight_report(report, path)
        content = path.read_text(encoding="utf-8")
        self.assertIn('"status": "ok"', content)
        self.assertIn("✅ database", preflight_summary(report))


class HealthCheckRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Path("bot/main.py").read_text(encoding="utf-8")

    def test_preflight_runs_before_storage_initialization(self) -> None:
        main_start = self.source.index("def main() -> int:")
        source = self.source[main_start:]
        self.assertLess(
            source.index("startup_report = run_system_preflight()"),
            source.index("storage = BotStorage(config.database_file)"),
        )

    def test_critical_preflight_stops_startup(self) -> None:
        self.assertIn("if startup_report.critical:", self.source)
        self.assertIn("raise RuntimeError(preflight_summary", self.source)

    def test_periodic_integrity_monitor_is_started(self) -> None:
        self.assertIn("def integrity_monitor_worker()", self.source)
        self.assertIn("start_integrity_monitor_worker()", self.source)


if __name__ == "__main__":
    unittest.main()
