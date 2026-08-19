from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from bot.encryption import decrypt_file
from tools.encrypt_data_snapshot import snapshot


PASSWORD = "Snapshot-Test-Password-2026!"


class EncryptedSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/encrypted_snapshot")
        shutil.rmtree(self.root, ignore_errors=True)
        self.source = self.root / "data"
        self.destination = self.root / "vault"
        self.source.mkdir(parents=True)
        (self.source / "abonents.xlsx").write_bytes(b"sensitive abonent data")
        nested = self.source / "nested"
        nested.mkdir()
        (nested / "inspectors.xlsx").write_bytes(b"sensitive inspector data")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_snapshot_encrypts_files_and_preserves_sources(self) -> None:
        snapshot([self.source], self.destination, PASSWORD)

        manifest = json.loads(
            (self.destination / "manifest.json").read_text(encoding="utf-8")
        )
        encrypted_abonents = (
            self.destination / "data" / "abonents.xlsx.uwenc"
        )
        restored = self.root / "restored.xlsx"
        decrypt_file(encrypted_abonents, restored, PASSWORD)

        self.assertEqual(2, len(manifest["files"]))
        self.assertTrue((self.source / "abonents.xlsx").exists())
        self.assertEqual(b"sensitive abonent data", restored.read_bytes())
        self.assertNotIn(
            b"sensitive abonent data",
            encrypted_abonents.read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
