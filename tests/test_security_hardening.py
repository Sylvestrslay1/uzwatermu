import io
import shutil
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from bot.config import _validate_config
from bot.code_integrity import (
    CodeIntegrityError,
    build_manifest,
    verify_code_integrity,
)
from bot.image_matching import InvalidMeterImage, fingerprint_image
from bot.rate_limit import RequestRateLimiter
from bot.security_hardening import (
    UnsafeOfficeFile,
    redact_sensitive_text,
    validate_safe_xlsx,
)
from tests.test_config_validation import valid_config


class SensitiveTextTests(unittest.TestCase):
    def test_tokens_passwords_and_project_path_are_redacted(self) -> None:
        token = "123456789:abcdefghijklmnopqrstuvwxyzABCDE"
        text = redact_sensitive_text(
            f"BOT_TOKEN={token} password=hunter2 {Path.cwd()}"
        )
        self.assertNotIn(token, text)
        self.assertNotIn("hunter2", text)
        self.assertNotIn(str(Path.cwd()), text)


class OfficeUploadSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/security") / self._testMethodName
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _xlsx(self, sheet_payload: bytes, extra: dict[str, bytes] | None = None) -> Path:
        path = self.root / "test.xlsx"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", b"<Types/>")
            archive.writestr("xl/workbook.xml", b"<workbook/>")
            archive.writestr("xl/worksheets/sheet1.xml", sheet_payload)
            for name, payload in (extra or {}).items():
                archive.writestr(name, payload)
        return path

    def test_external_links_are_rejected(self) -> None:
        path = self._xlsx(
            b"<worksheet/>",
            {"xl/externalLinks/externalLink1.xml": b"<externalLink/>"},
        )
        with self.assertRaises(UnsafeOfficeFile):
            validate_safe_xlsx(path)

    def test_dangerous_formula_is_rejected(self) -> None:
        path = self._xlsx(
            b'<worksheet><c><f>WEBSERVICE("https://example.test")</f></c></worksheet>'
        )
        with self.assertRaises(UnsafeOfficeFile):
            validate_safe_xlsx(path)

    def test_zip_bomb_ratio_is_rejected(self) -> None:
        path = self._xlsx(b"0" * (2 * 1024 * 1024))
        with self.assertRaises(UnsafeOfficeFile):
            validate_safe_xlsx(path)

    def test_real_workbooks_pass_archive_security(self) -> None:
        validate_safe_xlsx("data/abonents.xlsx")
        validate_safe_xlsx("data/inspectors.xlsx")


class ImageResourceSecurityTests(unittest.TestCase):
    def test_excessive_pixel_count_is_rejected_before_conversion(self) -> None:
        image = Image.new("1", (5000, 5000), 1)
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        with self.assertRaises(InvalidMeterImage):
            fingerprint_image(stream.getvalue())


class RuntimeSecurityTests(unittest.TestCase):
    def test_encryption_cannot_be_disabled_in_production_config(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "ENCRYPTION_ENABLED"):
            _validate_config(
                replace(
                    valid_config(),
                    encryption_enabled=False,
                    encryption_password=None,
                )
            )

    def test_rate_limiter_removes_stale_user_buckets(self) -> None:
        limiter = RequestRateLimiter(10, 60)
        limiter.check(1, 10, now=1)
        limiter.check(2, 10, now=200)
        self.assertNotIn(1, limiter._requests)
        self.assertIn(2, limiter._requests)


class CodeIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("work/tests/code_integrity") / self._testMethodName
        shutil.rmtree(self.root, ignore_errors=True)
        (self.root / "bot").mkdir(parents=True)
        (self.root / "tools").mkdir()
        (self.root / "bot" / "main.py").write_text("print('safe')\n", encoding="utf-8")
        (self.root / "requirements.txt").write_text("example==1\n", encoding="utf-8")
        self.key = "integrity-test-key-2026"
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(
            __import__("json").dumps(build_manifest(self.key, self.root)),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_valid_signed_manifest_passes(self) -> None:
        with patch("bot.code_integrity.load_secret", return_value=self.key):
            verify_code_integrity(self.root, self.manifest_path)

    def test_modified_code_is_blocked(self) -> None:
        (self.root / "bot" / "main.py").write_text(
            "print('modified')\n",
            encoding="utf-8",
        )
        with patch("bot.code_integrity.load_secret", return_value=self.key):
            with self.assertRaises(CodeIntegrityError):
                verify_code_integrity(self.root, self.manifest_path)


if __name__ == "__main__":
    unittest.main()
