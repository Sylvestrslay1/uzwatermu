import unittest
from pathlib import Path
from types import SimpleNamespace

import bot.main as main


ROOT = Path(__file__).resolve().parents[1]


class RuntimeFlowHardeningTests(unittest.TestCase):
    def tearDown(self) -> None:
        main.sessions.clear()
        main._user_message_locks_store.clear()

    def test_empty_session_is_removed_after_handler(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=987654321),
        )

        @main.serialized_message_handler
        def empty_handler(current_message) -> None:
            main.session(current_message)

        empty_handler(message)

        self.assertNotIn(987654321, main.sessions)

    def test_stateful_session_is_preserved_after_handler(self) -> None:
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=987654321),
        )

        @main.serialized_message_handler
        def stateful_handler(current_message) -> None:
            main.session(current_message)["state"] = "waiting"

        stateful_handler(message)

        self.assertEqual(
            main.sessions[987654321]["state"],
            "waiting",
        )

    def test_excel_replacement_has_rollback_path(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8"
        )
        function = source.split(
            "def admin_confirm_excel_upload", 1
        )[1].split("def admin_broadcast_collect", 1)[0]
        self.assertIn("replace.rollback", function)
        self.assertIn("rollback_path.replace(target)", function)
        self.assertIn("with maintenance_lock:", function)

    def test_photo_is_counted_only_after_encrypted_storage(self) -> None:
        source = (ROOT / "bot" / "main.py").read_text(
            encoding="utf-8"
        )
        function = source.split(
            "def handle_meter_photo", 1
        )[1].split("def request_bot_shutdown", 1)[0]
        self.assertLess(
            function.index("store_meter_photo("),
            function.index("photo_count += 1"),
        )

    def test_csv_formula_prefixes_are_neutralized(self) -> None:
        self.assertEqual(main.csv_safe_value("=1+1"), "'=1+1")
        self.assertEqual(main.csv_safe_value("@SUM(A1)"), "'@SUM(A1)")
        self.assertEqual(main.csv_safe_value("normal"), "normal")


if __name__ == "__main__":
    unittest.main()
