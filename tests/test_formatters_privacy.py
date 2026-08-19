import unittest
from types import SimpleNamespace

from bot.formatters import balance_text, cabinet_text, meter_intro_text, report_caption


def abonent_fixture() -> SimpleNamespace:
    return SimpleNamespace(
        account="1251050256",
        fio="Axadov Shavkat Jamalovich",
        phone="+998901234567",
        original_phone="+998971112233",
        edited_phone="+998901234567",
        address="Mahalla: Zakovat, Ko'cha: Olimlar, Uy: 51, Xonadon: 12",
        area="39",
        inspector_fio="Inspektor Xizmatov",
        inspector_phone="712625581",
        updated_at="01.06.2026",
        debit="100000",
        credit="0",
        has_meter="+",
        last_meter_value="20",
        last_meter_date="01.06.2026",
    )


class FormatterPrivacyTests(unittest.TestCase):
    def assert_consumer_pii_hidden(self, text: str) -> None:
        self.assertNotIn("1251050256", text)
        self.assertNotIn("Axadov Shavkat Jamalovich", text)
        self.assertNotIn("+998901234567", text)

    def test_cabinet_masks_all_consumer_identity_fields(self) -> None:
        text = cabinet_text(abonent_fixture(), "uz")
        self.assert_consumer_pii_hidden(text)
        self.assertIn("A... Sh... J...", text)
        self.assertIn("+998 90 *** * 567", text)
        self.assertNotIn("Uy: 51", text)
        self.assertNotIn("Xonadon: 12", text)

    def test_balance_masks_account_and_name(self) -> None:
        text = balance_text(abonent_fixture(), "ru", "02.06.2026")
        self.assert_consumer_pii_hidden(text)
        self.assertIn("100000", text)

    def test_meter_intro_masks_account(self) -> None:
        text = meter_intro_text(abonent_fixture(), "uz_cyrl")
        self.assertNotIn("1251050256", text)
        self.assertIn("*******256", text)

    def test_report_caption_is_masked_by_default(self) -> None:
        text = report_caption(abonent_fixture())
        self.assert_consumer_pii_hidden(text)

    def test_authorized_staff_caption_can_be_full(self) -> None:
        text = report_caption(abonent_fixture(), masked=False)
        self.assertIn("1251050256", text)
        self.assertIn("Axadov Shavkat Jamalovich", text)
        self.assertIn("+998901234567", text)

    def test_stored_phone_is_masked_in_channel_caption(self) -> None:
        text = report_caption(abonent_fixture(), stored_phone="+998935556677")
        self.assertNotIn("+998935556677", text)
        self.assertIn("+998 93 *** * 677", text)


if __name__ == "__main__":
    unittest.main()
