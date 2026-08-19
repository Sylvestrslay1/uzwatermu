import unittest
from pathlib import Path

from bot.texts import TEXTS


ROOT = Path(__file__).resolve().parents[1]


class LanguageConsistencyTests(unittest.TestCase):
    def test_all_languages_have_the_same_keys(self) -> None:
        expected = set(TEXTS["uz"])
        for language in ("uz_cyrl", "ru"):
            self.assertEqual(set(TEXTS[language]), expected)

    def test_user_errors_are_available_in_every_language(self) -> None:
        required = {
            "access_pending",
            "access_rejected",
            "operator_approved",
            "operator_rejected",
            "phone_invalid",
            "photo_count_limit",
            "photo_size_limit",
            "photo_delivery_failed",
            "photo_invalid",
            "photo_duplicate",
            "photo_storage_failed",
            "meter_review_pending",
            "meter_auto_approved",
            "meter_auto_rejected",
            "meter_operator_approved",
            "meter_operator_rejected",
        }
        for language in ("uz", "uz_cyrl", "ru"):
            self.assertTrue(required <= set(TEXTS[language]))
            for key in required:
                self.assertTrue(TEXTS[language][key].strip())

    def test_obsolete_meter_spelling_is_not_shown_to_users(self) -> None:
        for language in ("uz", "uz_cyrl"):
            combined = "\n".join(TEXTS[language].values())
            self.assertNotIn("ko'rsatgich", combined)
            self.assertNotIn("Telefon raqamni", combined)
            self.assertNotIn("Телефон рақамни", combined)
            self.assertNotIn("кўрсатгич", combined)

    def test_approval_callback_uses_the_users_language(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        callback = source.split(
            "def handle_approval_callback", 1
        )[1].split("def handle_message", 1)[0]
        self.assertIn('TEXTS[language]["operator_approved"]', callback)
        self.assertIn('TEXTS[language]["operator_rejected"]', callback)

    def test_meter_errors_use_localized_texts(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        handler = source.split(
            "def handle_meter_photo", 1
        )[1].split("def request_bot_shutdown", 1)[0]
        self.assertIn('text["photo_count_limit"]', handler)
        self.assertIn('text["photo_size_limit"]', handler)
        self.assertIn('text["photo_storage_failed"]', handler)
        self.assertIn('text["photo_invalid"]', handler)


if __name__ == "__main__":
    unittest.main()
