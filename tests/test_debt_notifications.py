import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import bot.main as main
from bot.debt_texts import debt_warning_text


ROOT = Path(__file__).resolve().parents[1]


class DebtNotificationTests(unittest.TestCase):
    def test_all_languages_include_account_date_amount_and_group_two(self) -> None:
        group_two = {
            "uz": "II guruh",
            "uz_cyrl": "II гуруҳ",
            "ru": "II группы",
        }
        for language, phrase in group_two.items():
            with self.subTest(language=language):
                text = debt_warning_text(
                    language,
                    "100\u00a0000",
                    "03.06.2026",
                    "*******256",
                )
                self.assertIn("*******256", text)
                self.assertIn("03.06.2026", text)
                self.assertIn("100\u00a0000", text)
                self.assertIn(phrase, text)
                self.assertLess(len(text), 4096)

    def test_money_is_formatted_for_humans(self) -> None:
        self.assertEqual(main.format_money("100000"), "100\u00a0000")
        self.assertEqual(main.format_money("50670,16"), "50\u00a0670,16")
        self.assertEqual(main.format_money("0"), "0")

    def test_next_calendar_date_is_calculated(self) -> None:
        # 13-da → keyingi sana 25-iyun
        self.assertEqual(
            main.next_debt_calendar_date(
                datetime(2026, 6, 13, 12, 0)
            ).strftime("%d.%m.%Y"),
            "25.06.2026",
        )
        # 26-da (25 o'tib ketgan) → keyingi oy 10-iyul
        self.assertEqual(
            main.next_debt_calendar_date(
                datetime(2026, 6, 26, 12, 0)
            ).strftime("%d.%m.%Y"),
            "10.07.2026",
        )
        # Dekabr 26 → yanvar 10
        self.assertEqual(
            main.next_debt_calendar_date(
                datetime(2026, 12, 26, 12, 0)
            ).strftime("%d.%m.%Y"),
            "10.01.2027",
        )
        # 10-da soat 9 dan keyin → 25-ga
        self.assertEqual(
            main.next_debt_calendar_date(
                datetime(2026, 6, 10, 12, 0)
            ).strftime("%d.%m.%Y"),
            "25.06.2026",
        )

    def test_second_send_job_is_rejected_while_one_is_running(self) -> None:
        acquired = main.debt_job_lock.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            with patch.object(
                main,
                "excel_statement_date",
                return_value="03.06.2026",
            ):
                result = main.run_debt_analysis(send_messages=True)
        finally:
            main.debt_job_lock.release()

        self.assertEqual(result["busy"], 1)
        self.assertEqual(result["sent"], 0)

    def test_manual_send_uses_background_job_without_force_duplicates(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        function = source.split(
            "def admin_debt_send", 1
        )[1].split("def admin_restore_backup", 1)[0]
        self.assertIn("start_debt_warning_job(", function)
        self.assertIn("force=False", function)
        self.assertIn("fon rejimida", function)

    def test_job_progress_is_persisted(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        core = source.split(
            "def _run_debt_analysis_core", 1
        )[1].split("def run_debt_analysis", 1)[0]
        self.assertIn('"debt_job_status"', core)
        self.assertIn('"debt_job_progress"', core)
        self.assertIn('"debt_job_result"', core)

    def test_interrupted_job_is_resumed_after_restart(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        worker = source.split(
            "def debt_analysis_worker", 1
        )[1].split("def start_debt_analysis_worker", 1)[0]
        self.assertIn('"debt_job_status"', worker)
        self.assertIn('"recovered_after_restart"', worker)
        self.assertIn("calendar_only=not interrupted", worker)
        self.assertIn('"debt_job_run_id"', worker)
        self.assertIn("run_id=interrupted_run_id", worker)

    def test_completed_accounts_are_skipped_when_same_run_resumes(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        core = source.split(
            "def _run_debt_analysis_core", 1
        )[1].split("def run_debt_analysis", 1)[0]
        self.assertIn("debt_warning_succeeded_in_run", core)
        self.assertIn('"debt_job_run_id"', core)

    def test_excel_upload_only_sends_on_calendar_day(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        function = source.split(
            "def admin_confirm_excel_upload", 1
        )[1].split("def admin_broadcast_collect", 1)[0]
        self.assertIn(
            "due_today = debt_calendar_due(datetime.now())",
            function,
        )
        self.assertIn("calendar_only=True", function)
        self.assertNotIn("calendar_only=False", function)

    def test_manual_send_confirmation_contains_dry_run_preview(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8-sig"
        )
        menu = source.split(
            "def handle_admin_menu", 1
        )[1].split("def handle_admin_state", 1)[0]
        section = menu.split(
            "if message_text == ADMIN_DEBT_SEND:", 1
        )[1].split("if message_text == ADMIN_EXIT:", 1)[0]
        self.assertIn("run_debt_analysis(send_messages=False)", section)
        self.assertIn("Qarzdor hisoblar", section)
        self.assertIn("takroran yuborilmaydi", section)


if __name__ == "__main__":
    unittest.main()
