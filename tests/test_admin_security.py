import gc
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import bot.main as main
from bot.security import (
    ADMIN_BLOCK_MINUTES,
    ADMIN_FAILURE_LIMIT,
    ADMIN_SESSION_MINUTES,
    admin_access_blocked,
    register_denied_attempt,
    session_deadline,
)
from bot.storage import BotStorage


class ParseTelegramIdTests(unittest.TestCase):
    def test_valid_positive_id(self) -> None:
        self.assertEqual(main._parse_telegram_id("123456789"), 123456789)

    def test_negative_id_returns_none(self) -> None:
        self.assertIsNone(main._parse_telegram_id("-1001234567890"))

    def test_whitespace_is_stripped(self) -> None:
        self.assertEqual(main._parse_telegram_id("  987654321  "), 987654321)

    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(main._parse_telegram_id(""))

    def test_alphabetic_returns_none(self) -> None:
        self.assertIsNone(main._parse_telegram_id("abc"))

    def test_alphanumeric_returns_none(self) -> None:
        self.assertIsNone(main._parse_telegram_id("123abc"))

    def test_username_returns_none(self) -> None:
        self.assertIsNone(main._parse_telegram_id("@uzwatermu"))


class AdminSecurityUnitTests(unittest.TestCase):
    def test_fifth_denied_attempt_blocks_access(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, 0)
        state = {}
        for offset in range(ADMIN_FAILURE_LIMIT):
            state = register_denied_attempt(
                state,
                now + timedelta(seconds=offset),
            )

        self.assertTrue(state["just_blocked"])
        self.assertTrue(admin_access_blocked(state, now + timedelta(minutes=1)))
        self.assertFalse(
            admin_access_blocked(
                state,
                now + timedelta(minutes=ADMIN_BLOCK_MINUTES + 1),
            )
        )

    def test_old_failure_window_is_reset(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, 0)
        old_state = {
            "failed_count": 4,
            "window_started": (now - timedelta(minutes=11)).isoformat(),
        }

        result = register_denied_attempt(old_state, now)

        self.assertEqual(result["failed_count"], 1)
        self.assertFalse(result["just_blocked"])

    def test_admin_session_deadline_is_thirty_minutes(self) -> None:
        now = datetime(2026, 6, 11, 12, 0, 0)
        deadline = datetime.fromtimestamp(session_deadline(now))
        self.assertEqual(deadline - now, timedelta(minutes=ADMIN_SESSION_MINUTES))


class AdminSecurityStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        test_dir = Path("work") / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = test_dir / f"admin_security_{uuid4().hex}.sqlite3"
        self.storage = BotStorage(str(self.database_path))

    def tearDown(self) -> None:
        gc.collect()
        self.database_path.unlink(missing_ok=True)

    def test_access_attempt_is_persisted_and_cleared(self) -> None:
        self.storage.save_admin_access_attempt(
            123456789,
            4,
            "2026-06-11T12:00:00",
            "",
            "2026-06-11T12:01:00",
        )
        state = self.storage.admin_access_attempt(123456789)
        self.assertEqual(state["failed_count"], 4)

        self.storage.clear_admin_access_attempts(123456789)
        cleared = self.storage.admin_access_attempt(123456789)
        self.assertEqual(cleared["failed_count"], 0)


if __name__ == "__main__":
    unittest.main()
