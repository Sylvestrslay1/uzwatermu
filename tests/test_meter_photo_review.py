import io
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

from bot.image_matching import (
    InvalidMeterImage,
    compare_photo_sets,
    fingerprint_image,
)
from bot.meter_vault import load_meter_photo, store_meter_photo
from bot.storage import BotStorage


PASSWORD = "meter-photo-test-password-123"


def make_test_image(*, offset: int = 0, inverted: bool = False) -> bytes:
    background = "white" if not inverted else "black"
    foreground = "black" if not inverted else "white"
    image = Image.new("RGB", (900, 700), background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((150 + offset, 120, 750 + offset, 580), outline=foreground, width=18)
    draw.ellipse((260 + offset, 190, 640 + offset, 520), outline=foreground, width=12)
    draw.text((370 + offset, 330), "12345", fill=foreground)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=92)
    return output.getvalue()


class MeterImageMatchingTests(unittest.TestCase):
    def test_same_meter_is_auto_approved(self) -> None:
        reference = fingerprint_image(make_test_image())
        submitted = fingerprint_image(make_test_image(offset=3))
        result = compare_photo_sets([submitted], [reference])
        self.assertEqual(result.decision, "approve")
        self.assertGreaterEqual(result.score, 0.88)

    def test_different_meter_is_not_auto_approved(self) -> None:
        reference = fingerprint_image(make_test_image())
        submitted = fingerprint_image(make_test_image(inverted=True))
        result = compare_photo_sets([submitted], [reference])
        self.assertNotEqual(result.decision, "approve")

    def test_count_mismatch_requires_review(self) -> None:
        fingerprint = fingerprint_image(make_test_image())
        result = compare_photo_sets([fingerprint, fingerprint], [fingerprint])
        self.assertEqual(result.decision, "review")

    def test_invalid_bytes_are_rejected(self) -> None:
        with self.assertRaises(InvalidMeterImage):
            fingerprint_image(b"not-an-image")


class MeterVaultTests(unittest.TestCase):
    def test_photo_is_encrypted_and_integrity_checked(self) -> None:
        payload = make_test_image()
        temp = Path("work") / f"meter_vault_test_{uuid4().hex}"
        temp.mkdir(parents=True)
        try:
            path, digest = store_meter_photo(payload, PASSWORD, root=temp)
            encrypted = Path(path).read_bytes()
            self.assertNotIn(payload[:100], encrypted)
            # load_meter_photo intentionally only permits the production vault.
            production_root = Path("encrypted_vault/meter_photos")
            production_root.mkdir(parents=True, exist_ok=True)
            production_path = production_root / Path(path).name
            production_path.write_bytes(encrypted)
            try:
                self.assertEqual(
                    load_meter_photo(production_path, PASSWORD, digest),
                    payload,
                )
                with self.assertRaises(Exception):
                    load_meter_photo(production_path, PASSWORD, "0" * 64)
            finally:
                production_path.unlink(missing_ok=True)
        finally:
            shutil.rmtree(temp, ignore_errors=True)


class MeterReviewStorageTests(unittest.TestCase):
    def test_only_first_operator_can_decide_and_approval_creates_reference(self) -> None:
        temp = Path("work") / f"meter_storage_test_{uuid4().hex}"
        temp.mkdir(parents=True)
        try:
            storage = BotStorage(str(temp / "bot.sqlite3"))
            submission_id = storage.save_meter_submission(
                100,
                "123456",
                "uz",
                "Inspector",
                "pending_review",
                [
                    {
                        "telegram_file_id": "file-1",
                        "encrypted_path": "photo.uwenc",
                        "sha256": "a" * 64,
                        "fingerprint": fingerprint_image(make_test_image()),
                    }
                ],
            )
            self.assertTrue(
                storage.transition_meter_submission(
                    submission_id,
                    "pending_review",
                    "approved",
                    200,
                    "operator_approved",
                    create_references=True,
                )
            )
            self.assertFalse(
                storage.transition_meter_submission(
                    submission_id,
                    "pending_review",
                    "rejected",
                    201,
                    "operator_rejected",
                )
            )
            self.assertEqual(
                len(storage.meter_reference_fingerprints("123456")),
                1,
            )
        finally:
            shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
