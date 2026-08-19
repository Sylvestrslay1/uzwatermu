import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FlowSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.message_handler = self.source.split(
            "def handle_message(message: types.Message)", 1
        )[1].split("def choose_language", 1)[0]

    def test_start_is_matched_exactly_in_generic_handler(self) -> None:
        self.assertIn(
            'message_text.strip().casefold() in {"/start", "start", "▶️ start"}',
            self.message_handler,
        )
        self.assertNotIn(
            '"start" in message_text.lower()',
            self.message_handler,
        )

    def test_invalid_public_service_input_cannot_fall_through(self) -> None:
        public_state = self.message_handler.split(
            "if state == states.PUBLIC_SERVICE:", 1
        )[1].split("if state == states.CHOOSING_OPERATOR_LANGUAGE:", 1)[0]
        self.assertIn("Quyidagi xizmat tugmalaridan birini tanlang", public_state)
        self.assertRegex(public_state, r"\n\s*return\s*$")

    def test_malformed_callback_telegram_id_is_rejected(self) -> None:
        callback = self.source.split(
            "def handle_approval_callback", 1
        )[1].split("def handle_message", 1)[0]
        self.assertIn("except (TypeError, ValueError):", callback)
        self.assertIn('bot.answer_callback_query(call.id, "Noto\'g\'ri so\'rov.")', callback)

    def test_unknown_admin_state_recovers_to_admin_menu(self) -> None:
        admin_state = self.source.split(
            "def handle_admin_state", 1
        )[1].split("def reload_excel", 1)[0]
        self.assertIn("Amal holati eskirgan", admin_state)
        self.assertIn("clear_admin_flow(message)", admin_state)

    def test_consumer_handlers_require_private_chat(self) -> None:
        start_handler = self.source.split(
            "def handle_start", 1
        )[1].split("def handle_myid", 1)[0]
        generic_handler = self.source.split(
            "def handle_message", 1
        )[1].split("def choose_language", 1)[0]
        self.assertIn("if not is_private_chat(message):", start_handler)
        self.assertIn("private_chat_required_text", start_handler)
        self.assertIn("if not is_private_chat(message):", generic_handler)
        self.assertIn("private_chat_required_text", generic_handler)

    def test_stale_excel_account_cannot_be_approved(self) -> None:
        callback = self.source.split(
            "def handle_approval_callback", 1
        )[1].split("def handle_message", 1)[0]
        self.assertIn(
            'if action == "approve" and not abonent:',
            callback,
        )
        self.assertIn('"stale_approval_blocked"', callback)


if __name__ == "__main__":
    unittest.main()
