import gc
import shutil
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import bot.main as main
from bot.storage import BotStorage


class InspectorLocationStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("work/tests/inspector_location")
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / f"{uuid4().hex}.sqlite3"
        self.storage = BotStorage(str(self.path))
        self.storage.add_inspector_user(
            111111111,
            "39",
            "Test Inspektor",
            "+998901234567",
        )

    def tearDown(self) -> None:
        gc.collect()
        self.path.unlink(missing_ok=True)
        Path(f"{self.path}-wal").unlink(missing_ok=True)
        Path(f"{self.path}-shm").unlink(missing_ok=True)

    def test_session_snapshots_active_inspectors(self) -> None:
        session_id, inspectors = (
            self.storage.create_inspector_location_session(
                999999999,
                "2026-06-13T10:00:00",
                "2026-06-13T10:10:00",
                "2026-06-13T10:20:00",
            )
        )

        self.assertEqual(len(inspectors), 1)
        responses = self.storage.inspector_location_responses(session_id)
        self.assertEqual(responses[0]["status"], "pending")
        self.assertEqual(responses[0]["fio"], "Test Inspektor")

    def test_live_location_marks_response_complete(self) -> None:
        session_id, _ = self.storage.create_inspector_location_session(
            999999999,
            "2026-06-13T10:00:00",
            "2026-06-13T10:10:00",
            "2026-06-13T10:20:00",
        )

        saved = self.storage.save_inspector_live_location(
            session_id,
            111111111,
            latitude=41.3,
            longitude=69.3,
            live_period=3600,
            source_message_id=77,
            received_at="2026-06-13T10:05:00",
        )

        self.assertTrue(saved)
        response = self.storage.inspector_location_responses(session_id)[0]
        self.assertEqual(response["status"], "live")
        self.assertEqual(response["source_message_id"], 77)
        self.storage.complete_inspector_location_session(
            session_id,
            "2026-06-13T10:20:00",
        )
        continued = self.storage.inspector_location_session_for_update(
            111111111,
            77,
        )
        self.assertEqual(int(continued["id"]), session_id)

    def test_second_active_session_is_not_created(self) -> None:
        first, _ = self.storage.create_inspector_location_session(
            999999999,
            "2026-06-13T10:00:00",
            "2026-06-13T10:10:00",
            "2026-06-13T10:20:00",
        )
        second, inspectors = (
            self.storage.create_inspector_location_session(
                999999999,
                "2026-06-13T11:00:00",
                "2026-06-13T11:10:00",
                "2026-06-13T11:20:00",
            )
        )

        self.assertEqual(first, second)
        self.assertEqual(inspectors, [])


class InspectorLocationFlowTests(unittest.TestCase):
    def test_static_location_is_rejected(self) -> None:
        fake_bot = Mock()
        fake_storage = Mock()
        fake_storage.active_inspector_location_session.return_value = {
            "id": 1
        }
        message = SimpleNamespace(
            chat=SimpleNamespace(id=111111111),
            from_user=SimpleNamespace(id=111111111),
            message_id=10,
            location=SimpleNamespace(
                latitude=41.3,
                longitude=69.3,
                live_period=None,
            ),
        )
        inspector = {
            "telegram_id": 111111111,
            "fio": "Test",
            "area": "39",
        }

        fake_config = SimpleNamespace(location_channel_id=None)
        with (
            patch.object(main, "bot", fake_bot, create=True),
            patch.object(main, "storage", fake_storage, create=True),
            patch.object(main, "config", fake_config, create=True),
        ):
            main.handle_inspector_location(message, inspector)

        fake_storage.save_inspector_live_location.assert_not_called()
        self.assertIn(
            "Oddiy yoki 1 soatdan qisqa",
            fake_bot.send_message.call_args.args[1],
        )

    def test_deadline_sends_reminder_then_final_report(self) -> None:
        fake_bot = Mock()
        fake_storage = Mock()
        session = {
            "id": 7,
            "requested_by": 999999999,
            "status": "active",
            "requested_at": "2026-06-13T10:00:00",
            "reminder_at": "2026-06-13T10:10:00",
            "final_at": "2026-06-13T10:20:00",
        }
        response = {
            "inspector_id": 111111111,
            "telegram_id": 111111111,
            "status": "pending",
            "fio": "Test Inspektor",
            "area": "39",
            "phone": "+998901234567",
        }
        fake_storage.active_inspector_location_session.return_value = session
        fake_storage.inspector_location_responses.return_value = [response]
        fake_storage.complete_inspector_location_session.return_value = True
        fake_config = SimpleNamespace(
            admin_ids={999999999},
            bulk_send_delay=0,
        )

        with (
            patch.object(main, "bot", fake_bot, create=True),
            patch.object(main, "storage", fake_storage, create=True),
            patch.object(main, "config", fake_config, create=True),
            patch.object(main, "audit"),
        ):
            main.process_inspector_location_deadlines(
                datetime(2026, 6, 13, 10, 10, 1)
            )
            session["status"] = "reminded"
            main.process_inspector_location_deadlines(
                datetime(2026, 6, 13, 10, 20, 1)
            )

        fake_storage.mark_inspector_location_reminded.assert_called_once()
        fake_storage.complete_inspector_location_session.assert_called_once()
        final_messages = [
            call.args[1]
            for call in fake_bot.send_message.call_args_list
        ]
        self.assertTrue(
            any("BUYRUG'I BAJARILMAGAN" in text for text in final_messages)
        )

    def test_source_registers_location_and_edited_updates(self) -> None:
        source = Path("bot/main.py").read_text(encoding="utf-8-sig")
        self.assertIn('"location",', source)
        self.assertIn("register_edited_message_handler(", source)
        self.assertIn("start_inspector_location_monitor_worker()", source)

    def test_large_noncompliance_report_is_chunked(self) -> None:
        responses = [
            {
                "telegram_id": 100000000 + index,
                "inspector_id": 100000000 + index,
                "status": "pending",
                "fio": f"Inspektor Testov {index}",
                "area": str(index),
                "phone": "+998901234567",
            }
            for index in range(100)
        ]
        chunks = main.inspector_noncompliance_report_chunks(
            {
                "requested_at": "2026-06-13T10:00:00",
                "final_at": "2026-06-13T10:20:00",
            },
            responses,
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 3800 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
