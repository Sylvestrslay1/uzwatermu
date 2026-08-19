from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

from bot.runtime import (
    AlreadyRunningError,
    ProcessLock,
    write_health_status,
)
from tools.windows_job import WindowsKillOnCloseJob


class ProcessLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/runtime") / self._testMethodName
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True)
        self.path = self.root / "bot.lock"

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_second_bot_instance_is_rejected(self) -> None:
        first = ProcessLock(self.path)
        second = ProcessLock(self.path)
        first.acquire()
        try:
            with self.assertRaises(AlreadyRunningError):
                second.acquire()
        finally:
            first.release()

    def test_lock_can_be_acquired_after_release(self) -> None:
        first = ProcessLock(self.path)
        first.acquire()
        first.release()

        second = ProcessLock(self.path)
        second.acquire()
        second.release()

    def test_lock_file_records_owner_pid(self) -> None:
        lock = ProcessLock(self.path)
        lock.acquire()
        lock.release()
        content = self.path.read_bytes()[1:].decode("utf-8")
        owner = json.loads(content)
        self.assertGreater(owner["pid"], 0)
        self.assertTrue(owner["started_at"])

    def test_lock_blocks_a_different_process(self) -> None:
        script = (
            "import sys;"
            "from bot.runtime import ProcessLock,AlreadyRunningError;"
            "lock=ProcessLock(sys.argv[1]);"
            "\ntry:\n lock.acquire(); print('ACQUIRED'); lock.release()"
            "\nexcept AlreadyRunningError:\n print('BLOCKED'); raise SystemExit(3)"
        )
        lock = ProcessLock(self.path)
        lock.acquire()
        try:
            result = subprocess.run(
                [sys.executable, "-c", script, str(self.path)],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=20,
            )
        finally:
            lock.release()
        self.assertEqual(3, result.returncode)
        self.assertIn("BLOCKED", result.stdout)


class HealthStatusTests(unittest.TestCase):
    def test_health_status_is_valid_json(self) -> None:
        path = Path("work/tests/runtime/health/status.json")
        shutil.rmtree(path.parents[1], ignore_errors=True)
        write_health_status(
            path,
            state="running",
            started_at="2026-06-13T14:00:00",
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("running", payload["state"])
        self.assertEqual("2026-06-13T14:00:00", payload["started_at"])
        self.assertGreater(payload["pid"], 0)


@unittest.skipUnless(os.name == "nt", "Windows Job Object testi")
class WindowsJobTests(unittest.TestCase):
    def test_closing_job_terminates_child_process(self) -> None:
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        job = WindowsKillOnCloseJob()
        try:
            job.assign(process._handle)
            job.close()
            process.wait(timeout=10)
            self.assertIsNotNone(process.returncode)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


class RuntimeRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main_source = Path("bot/main.py").read_text(encoding="utf-8")
        cls.supervisor_source = Path("tools/bot_supervisor.py").read_text(
            encoding="utf-8"
        )

    def test_main_uses_process_lock_and_shutdown_event(self) -> None:
        self.assertIn('ProcessLock("storage/uzwatermu.lock")', self.main_source)
        self.assertIn("install_shutdown_handlers(", self.main_source)
        self.assertIn("while not shutdown_event.is_set():", self.main_source)

    def test_workers_use_interruptible_wait(self) -> None:
        self.assertIn("shutdown_event.wait(check_seconds)", self.main_source)
        self.assertIn(
            "shutdown_event.wait(max((next_check - now).total_seconds(), 60))",
            self.main_source,
        )

    def test_supervisor_has_restart_backoff_and_rotating_log(self) -> None:
        self.assertIn("RotatingFileHandler(", self.supervisor_source)
        self.assertIn("min(delay * 2, 300)", self.supervisor_source)
        self.assertIn('return_code == 3', self.supervisor_source)
        self.assertIn("def notify_admins(", self.supervisor_source)
        self.assertIn("barqaror ishlamoqda", self.supervisor_source)
        self.assertIn("WindowsKillOnCloseJob", self.supervisor_source)
        self.assertIn("verify_code_integrity(ROOT)", self.supervisor_source)

    def test_startup_task_does_not_bypass_powershell_policy(self) -> None:
        source = Path("tools/install_startup_task.ps1").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("ExecutionPolicy Bypass", source)
        self.assertIn('-Argument "-m tools.bot_supervisor"', source)


if __name__ == "__main__":
    unittest.main()
