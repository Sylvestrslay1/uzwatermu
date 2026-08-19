from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from bot.encryption import (
    EncryptionError,
    InvalidPasswordOrData,
    decrypt_bytes,
    decrypt_file,
    encrypt_bytes,
    encrypt_file,
    encrypted_file_info,
)


PASSWORD = "Correct-Horse-Battery-Staple-2026!"


class EncryptionUnitTests(unittest.TestCase):
    def test_aes_256_gcm_round_trip(self) -> None:
        plaintext = b"abonent account=123456789 phone=998901234567"
        payload = encrypt_bytes(
            plaintext,
            PASSWORD,
            label="database",
            original_name="bot.sqlite3",
        )

        restored, info = decrypt_bytes(payload, PASSWORD)

        self.assertEqual(plaintext, restored)
        self.assertEqual("database", info.label)
        self.assertEqual("bot.sqlite3", info.original_name)
        self.assertNotIn(plaintext, payload)
        self.assertNotIn(PASSWORD.encode("utf-8"), payload)

    def test_random_salt_and_nonce_make_ciphertexts_unique(self) -> None:
        first = encrypt_bytes(b"same", PASSWORD, label="test")
        second = encrypt_bytes(b"same", PASSWORD, label="test")
        self.assertNotEqual(first, second)

    def test_wrong_password_is_rejected(self) -> None:
        payload = encrypt_bytes(b"secret", PASSWORD, label="test")
        with self.assertRaises(InvalidPasswordOrData):
            decrypt_bytes(payload, "Wrong-password-that-is-long-enough!")

    def test_modified_ciphertext_is_rejected(self) -> None:
        payload = bytearray(encrypt_bytes(b"secret", PASSWORD, label="test"))
        payload[-1] ^= 1
        with self.assertRaises(InvalidPasswordOrData):
            decrypt_bytes(bytes(payload), PASSWORD)

    def test_short_password_is_rejected(self) -> None:
        with self.assertRaises(EncryptionError):
            encrypt_bytes(b"secret", "short", label="test")


class EncryptionFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/encryption") / self._testMethodName
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_file_round_trip_and_label_validation(self) -> None:
        source = self.root / "abonents.xlsx"
        encrypted = self.root / "abonents.xlsx.uwenc"
        restored = self.root / "restored.xlsx"
        source.write_bytes(b"example excel bytes")

        encrypt_file(source, encrypted, PASSWORD, label="abonents")
        info = encrypted_file_info(encrypted)
        decrypt_file(
            encrypted,
            restored,
            PASSWORD,
            expected_label="abonents",
        )

        self.assertEqual(source.read_bytes(), restored.read_bytes())
        self.assertEqual("abonents", info.label)
        self.assertEqual(source.name, info.original_name)

    def test_wrong_expected_label_is_rejected(self) -> None:
        source = self.root / "data.bin"
        encrypted = self.root / "data.uwenc"
        source.write_bytes(b"secret")
        encrypt_file(source, encrypted, PASSWORD, label="database")

        with self.assertRaises(EncryptionError):
            decrypt_file(
                encrypted,
                self.root / "restored.bin",
                PASSWORD,
                expected_label="abonents",
            )


if __name__ == "__main__":
    unittest.main()
