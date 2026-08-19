import unittest
from types import SimpleNamespace

from bot.main import (
    account_phone_matches,
    normalized_phone,
    normalized_uzbek_phone,
)


def abonent_fixture(**overrides):
    values = {
        "phone": "901234567",
        "original_phone": "",
        "edited_phone": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class AccountVerificationTests(unittest.TestCase):
    def test_phone_normalization_uses_local_nine_digits(self) -> None:
        self.assertEqual(normalized_phone("+998 90 123 45 67"), "901234567")

    def test_telegram_contact_matches_excel_phone(self) -> None:
        self.assertTrue(
            account_phone_matches(
                abonent_fixture(),
                "+998901234567",
            )
        )

    def test_edited_excel_phone_can_verify_account(self) -> None:
        self.assertTrue(
            account_phone_matches(
                abonent_fixture(phone="", edited_phone="935556677"),
                "+998935556677",
            )
        )

    def test_different_phone_requires_operator(self) -> None:
        self.assertFalse(
            account_phone_matches(
                abonent_fixture(),
                "+998999999999",
            )
        )

    def test_missing_excel_phone_requires_operator(self) -> None:
        self.assertFalse(
            account_phone_matches(
                abonent_fixture(phone=""),
                "+998901234567",
            )
        )

    def test_uzbek_phone_is_stored_in_canonical_format(self) -> None:
        self.assertEqual(
            normalized_uzbek_phone("90 123 45 67"),
            "+998901234567",
        )
        self.assertEqual(
            normalized_uzbek_phone("+998 (90) 123-45-67"),
            "+998901234567",
        )

    def test_invalid_or_foreign_phone_is_rejected(self) -> None:
        self.assertIsNone(normalized_uzbek_phone("12345"))
        self.assertIsNone(normalized_uzbek_phone("+7 999 123 45 67"))


if __name__ == "__main__":
    unittest.main()
