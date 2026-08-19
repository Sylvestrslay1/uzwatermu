import unittest

from bot.masking import (
    mask_account,
    mask_address,
    mask_name,
    mask_phone,
    mask_telegram_id,
    masked_row,
    sanitize_audit_details,
)


class MaskingUnitTests(unittest.TestCase):
    def test_name_uses_safe_initials(self) -> None:
        self.assertEqual(mask_name("Axadov Shavkat Jamalovich"), "A... Sh... J...")

    def test_cyrillic_name_is_supported(self) -> None:
        self.assertEqual(mask_name("Ахадов Шавкат Жамалович"), "А... Ша... Ж...")

    def test_empty_name(self) -> None:
        self.assertEqual(mask_name(""), "-")

    def test_uzbek_phone_with_country_code(self) -> None:
        self.assertEqual(mask_phone("+998 90 123 45 67"), "+998 90 *** * 567")

    def test_uzbek_phone_without_country_code(self) -> None:
        self.assertEqual(mask_phone("901234567"), "+998 90 *** * 567")

    def test_short_phone_does_not_leak(self) -> None:
        self.assertEqual(mask_phone("71"), "***")

    def test_account_keeps_only_last_three(self) -> None:
        self.assertEqual(mask_account("1251050256"), "*******256")

    def test_short_account_is_still_masked(self) -> None:
        self.assertEqual(mask_account("12"), "****2")

    def test_telegram_id_keeps_only_last_three(self) -> None:
        self.assertEqual(mask_telegram_id("-1003792541208"), "***********208")

    def test_address_hides_house_and_flat_labels(self) -> None:
        address = "Mahalla: Zakovat, Ko'cha: Olimlar, Uy: 51, Xonadon: 12"
        result = mask_address(address)
        self.assertNotIn("51", result)
        self.assertNotIn("12", result)
        self.assertIn("Olimlar", result)

    def test_address_hides_suffix_style_numbers(self) -> None:
        result = mask_address("Olimlar ko'chasi 51-uy, 12-xonadon")
        self.assertEqual(result, "Olimlar ko'chasi **-uy, **-xonadon")

    def test_masked_row_does_not_mutate_source(self) -> None:
        source = {
            "telegram_id": 8599528273,
            "account": "1251050256",
            "fio": "Axadov Shavkat Jamalovich",
            "phone": "901234567",
        }
        result = masked_row(source)
        self.assertEqual(source["fio"], "Axadov Shavkat Jamalovich")
        self.assertNotEqual(result["fio"], source["fio"])
        self.assertNotIn("1251050256", result.values())

    def test_audit_details_masks_identifiers(self) -> None:
        result = sanitize_audit_details(
            "telegram_id=8599528273; account=1251050256; phone=901234567"
        )
        self.assertNotIn("8599528273", result)
        self.assertNotIn("1251050256", result)
        self.assertNotIn("901234567", result)


if __name__ == "__main__":
    unittest.main()
