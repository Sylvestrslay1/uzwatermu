from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path

from bot.secret_store import (
    load_encryption_password,
    protect_secret,
    save_encryption_password,
    secret_path,
    unprotect_secret,
)


PASSWORD = "DPAPI-Test-Password-2026!"


@unittest.skipUnless(os.name == "nt", "Windows DPAPI testi")
class WindowsDpapiSecretStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/secret_store")
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True)
        self.path = self.root / "encryption_password.dpapi"

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_dpapi_round_trip(self) -> None:
        protected = protect_secret(PASSWORD)
        self.assertEqual(PASSWORD, unprotect_secret(protected))
        self.assertNotIn(PASSWORD.encode("utf-8"), protected)

    def test_secret_file_does_not_contain_plain_password(self) -> None:
        save_encryption_password(PASSWORD, self.path)

        self.assertEqual(PASSWORD, load_encryption_password(self.path))
        self.assertNotIn(PASSWORD.encode("utf-8"), self.path.read_bytes())

    def test_missing_secret_returns_none(self) -> None:
        self.assertIsNone(load_encryption_password(self.path))

    def test_secret_name_is_sanitized(self) -> None:
        result = secret_path("BOT_TOKEN")
        self.assertEqual(result.name, "bot_token.dpapi")
        self.assertTrue(result.is_absolute())


if __name__ == "__main__":
    unittest.main()
