import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AdminBroadcastFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")

    def test_broadcast_section_immediately_starts_text_collection(self) -> None:
        section = self.source.split(
            "if message_text == ADMIN_SECTION_BROADCAST:", 1
        )[1].split("if message_text == ADMIN_SECTION_SERVICE:", 1)[0]
        self.assertIn(
            'current["state"] = states.ADMIN_BROADCAST_UZ',
            section,
        )
        self.assertIn('current.pop("broadcast_texts", None)', section)
        self.assertIn("O'zbek lotin tilidagi xabar matnini kiriting", section)
        self.assertIn("reply_markup=admin_input_keyboard()", section)

    def test_unknown_staff_text_cannot_fall_through_to_consumer_flow(self) -> None:
        handler = self.source.split(
            "def handle_message(message: types.Message)", 1
        )[1].split("def choose_language", 1)[0]
        staff_block = handler.split("if is_staff(message):", 1)[1].split(
            "saved_user = storage.get_user(message.from_user.id)", 1
        )[0]
        self.assertIn("Admin paneldagi tugmalardan birini tanlang", staff_block)
        self.assertRegex(staff_block, r"\n\s*return\s*$")

    def test_broadcast_input_keyboard_does_not_repeat_send_button(self) -> None:
        keyboard = self.source.split(
            "def admin_input_keyboard()", 1
        )[1].split("def service_admin_keyboard", 1)[0]
        self.assertIn("CANCEL", keyboard)
        self.assertIn("ADMIN_BACK", keyboard)
        self.assertNotIn("ADMIN_BROADCAST", keyboard)


if __name__ == "__main__":
    unittest.main()
