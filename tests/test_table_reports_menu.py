import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TableReportsMenuTests(unittest.TestCase):
    def test_required_menu_buttons_exist(self) -> None:
        source = (ROOT / "bot" / "buttons.py").read_text(encoding="utf-8")
        for label in (
            "📑 Jadval hisobotlari",
            "📋 Shablonlar",
            "📥 Yangi F3 jadvalni yuborish",
            "🏢 Tuman pasport ma'lumotlari",
        ):
            self.assertIn(label, source)

    def test_table_reports_menu_is_super_admin_only(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        handler = source.split(
            "if message_text == ADMIN_SECTION_TABLE_REPORTS:", 1
        )[1].split("if message_text == ADMIN_INSPECTORS:", 1)[0]
        self.assertIn("is_super_admin_id(message.from_user.id)", handler)
        self.assertIn("table_reports_admin_keyboard", handler)

    def test_report_workspace_directories_are_initialized(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        for directory in (
            "data/report_templates",
            "outputs/table_reports",
            "work/f3",
        ):
            self.assertIn(f'"{directory}"', source)

    def test_three_month_report_is_attached_to_templates_menu(self) -> None:
        buttons = (ROOT / "bot" / "buttons.py").read_text(encoding="utf-8")
        main = (ROOT / "bot" / "main.py").read_text(encoding="utf-8")
        self.assertIn("📆 3 oylik ko'rsatkich olinmaganlar", buttons)
        self.assertIn("ADMIN_TEMPLATE_THREE_MONTHS", main)
        self.assertIn("latest_three_month_report", main)
        self.assertIn("bot.send_document", main)


if __name__ == "__main__":
    unittest.main()
