import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bot.main as main
from bot.buttons import (
    ADMIN_INSPECTORS,
    ADMIN_SECTION_BROADCAST,
    ADMIN_SECTION_EXCEL,
    ADMIN_SECTION_OPERATORS,
    ADMIN_SECTION_REPORTS,
    ADMIN_SECTION_REQUESTS,
    ADMIN_SECTION_SERVICE,
    ADMIN_SECTION_TABLE_REPORTS,
    ADMIN_TABLE_BACK,
    ADMIN_TABLE_DISTRICT_PASSPORT,
    ADMIN_TABLE_TEMPLATES,
    ADMIN_TABLE_UPLOAD_F3,
    ADMIN_TEMPLATE_THREE_MONTHS,
    INSPECTOR_EXIT,
)


ROOT = Path(__file__).resolve().parents[1]


def keyboard_texts(markup) -> list[str]:
    texts: list[str] = []
    for row in getattr(markup, "keyboard", []):
        for button in row:
            if isinstance(button, dict):
                texts.append(str(button.get("text") or ""))
            else:
                texts.append(str(getattr(button, "text", button)))
    return texts


class RoleInterfaceTests(unittest.TestCase):
    def test_operator_home_contains_only_allowed_sections(self) -> None:
        fake_config = SimpleNamespace(admin_ids={111})
        with patch.object(main, "config", fake_config, create=True):
            texts = keyboard_texts(main.admin_keyboard(222))

        self.assertIn(ADMIN_SECTION_EXCEL, texts)
        self.assertIn(ADMIN_SECTION_REQUESTS, texts)
        self.assertNotIn(ADMIN_SECTION_OPERATORS, texts)
        self.assertNotIn(ADMIN_SECTION_BROADCAST, texts)
        self.assertNotIn(ADMIN_SECTION_REPORTS, texts)
        self.assertNotIn(ADMIN_SECTION_TABLE_REPORTS, texts)
        self.assertNotIn(ADMIN_INSPECTORS, texts)
        self.assertNotIn(ADMIN_SECTION_SERVICE, texts)

    def test_super_admin_home_contains_management_sections(self) -> None:
        fake_config = SimpleNamespace(admin_ids={111})
        with patch.object(main, "config", fake_config, create=True):
            texts = keyboard_texts(main.admin_keyboard(111))

        for required in (
            ADMIN_SECTION_OPERATORS,
            ADMIN_SECTION_BROADCAST,
            ADMIN_SECTION_REPORTS,
            ADMIN_SECTION_TABLE_REPORTS,
            ADMIN_INSPECTORS,
            ADMIN_SECTION_SERVICE,
        ):
            self.assertIn(required, texts)

    def test_inspector_panel_has_exit_and_exit_returns_start_keyboard(self) -> None:
        fake_bot = Mock()
        message = SimpleNamespace(
            text=INSPECTOR_EXIT,
            chat=SimpleNamespace(id=555),
            from_user=SimpleNamespace(id=555),
        )
        inspector = {"telegram_id": 555, "fio": "Test", "area": "1"}

        self.assertIn(INSPECTOR_EXIT, keyboard_texts(main.inspector_keyboard()))
        with (
            patch.object(main, "bot", fake_bot, create=True),
            patch.object(main, "clear_session") as clear_session,
        ):
            main.handle_inspector_message(message, inspector)

        clear_session.assert_called_once_with(message)
        self.assertIn("paneli yopildi", fake_bot.send_message.call_args.args[1])

    def test_service_keyboard_does_not_show_removed_district_address_button(self) -> None:
        texts = keyboard_texts(main.service_keyboard("uz"))
        self.assertNotIn(main.TEXTS["uz"]["district_address"], texts)

    def test_hidden_district_address_branch_is_removed_from_consumer_menu(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        consumer = source.split(
            "if message_text == text[\"back\"]:", 1
        )[1].split("def handle_edited_inspector_location", 1)[0]
        self.assertNotIn('message_text == text["district_address"]', consumer)

    def test_operator_cannot_open_hidden_super_admin_table_report_actions(self) -> None:
        fake_config = SimpleNamespace(admin_ids={111})
        restricted_buttons = [
            ADMIN_SECTION_TABLE_REPORTS,
            ADMIN_TABLE_BACK,
            ADMIN_TABLE_TEMPLATES,
            ADMIN_TEMPLATE_THREE_MONTHS,
            ADMIN_TABLE_UPLOAD_F3,
            ADMIN_TABLE_DISTRICT_PASSPORT,
        ]

        for button in restricted_buttons:
            with self.subTest(button=button):
                fake_bot = Mock()
                message = SimpleNamespace(
                    text=button,
                    chat=SimpleNamespace(id=222),
                    from_user=SimpleNamespace(id=222),
                )
                with (
                    patch.object(main, "config", fake_config, create=True),
                    patch.object(main, "bot", fake_bot, create=True),
                ):
                    handled = main.handle_admin_menu(message, {})

                self.assertTrue(handled)
                self.assertIn("faqat super admin", fake_bot.send_message.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
