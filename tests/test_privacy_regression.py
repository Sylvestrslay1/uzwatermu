import unittest
from pathlib import Path

from bot.masking import masked_row


ROOT = Path(__file__).resolve().parents[1]


class PrivacyRegressionTests(unittest.TestCase):
    def test_channel_caption_default_remains_masked(self) -> None:
        source = (ROOT / "bot" / "formatters.py").read_text(encoding="utf-8")
        self.assertIn("masked: bool = True", source)

    def test_private_report_channel_explicitly_uses_full_details(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(source.count("masked=False"), 5)
        registration = source.split("def notify_registration", 1)[1].split(
            "def approval_request_text", 1
        )[0]
        phone_update = source.split("def save_phone", 1)[1].split(
            "def handle_meter_photo", 1
        )[0]
        meter_photo = source.split("def notify_meter_submission", 1)[1].split(
            "def notify_error", 1
        )[0]
        self.assertIn("masked=False", registration)
        self.assertIn("masked=False", phone_update)
        self.assertIn("masked=False", meter_photo)

    def test_approval_callback_identifies_specific_account(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.assertIn('callback_data=f"approve:{telegram_id}:{account}"', source)
        self.assertIn('callback_data=f"reject:{telegram_id}:{account}"', source)
        self.assertIn("transition_account_status(", source)

    def test_only_telegram_owners_contact_is_accepted(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        verification = source.split("def verify_account_phone", 1)[1].split(
            "def show_linked_accounts", 1
        )[0]
        self.assertIn("contact.user_id", verification)
        self.assertIn("message.from_user.id", verification)

    def test_admin_panel_is_private_and_session_limited(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.assertIn("def is_private_chat", source)
        self.assertIn("def require_admin_session", source)
        self.assertIn("admin_session_until", source)
        self.assertIn("admin_access_attempt", source)

    def test_operator_removal_requires_explicit_confirmation(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        prepare = source.split("def admin_remove_operator", 1)[1].split(
            "def admin_confirm_remove_operator", 1
        )[0]
        confirm = source.split("def admin_confirm_remove_operator", 1)[1].split(
            "def admin_add_inspector_flow", 1
        )[0]
        self.assertNotIn("storage.remove_operator", prepare)
        self.assertIn("REMOVE_OPERATOR_CONFIRM", confirm)
        self.assertIn("storage.remove_operator", confirm)

    def test_consumer_formatters_use_masking_helpers(self) -> None:
        source = (ROOT / "bot" / "formatters.py").read_text(encoding="utf-8")
        for required_call in (
            "mask_account(abonent.account)",
            "mask_name(abonent.fio)",
            "mask_phone(phone)",
            "mask_address(abonent.address)",
        ):
            self.assertIn(required_call, source)

    def test_all_sensitive_export_types_use_masking(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(source.count("[masked_row(row) for row in"), 4)

    def test_export_masking_removes_raw_pii(self) -> None:
        row = {
            "telegram_id": "8599528273",
            "account": "1251050256",
            "fio": "Axadov Shavkat Jamalovich",
            "phone": "+998901234567",
            "address": "Olimlar ko'chasi 51-uy",
        }
        exported = "|".join(str(value) for value in masked_row(row).values())
        for secret in row.values():
            self.assertNotIn(secret, exported)

    def test_audit_storage_sanitizes_details(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.assertIn(
            "storage.add_audit_log(actor_id, action, sanitize_audit_details(details)[:2000])",
            source,
        )

    def test_admin_back_is_handled_before_state_input(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        function = source.split("def handle_admin_state", 1)[1].split(
            "def reload_excel", 1
        )[0]
        self.assertLess(
            function.index("if message.text == ADMIN_BACK:"),
            function.index("state = current.get(\"state\")"),
        )


if __name__ == "__main__":
    unittest.main()
