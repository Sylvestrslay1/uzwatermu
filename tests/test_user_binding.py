import gc
import sqlite3
import unittest
from pathlib import Path
from uuid import uuid4

from bot.storage import BotStorage


class UserBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        test_dir = Path("work") / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = test_dir / f"user_binding_{uuid4().hex}.sqlite3"
        self.storage = BotStorage(str(self.database_path))

    def tearDown(self) -> None:
        gc.collect()
        self.database_path.unlink(missing_ok=True)

    def test_profile_is_created_once_but_can_link_multiple_accounts(self) -> None:
        first = self.storage.create_user_if_absent(
            123456789,
            "1111111111",
            "uz",
            "901234567",
            status="approved",
        )
        second = self.storage.create_user_if_absent(
            123456789,
            "2222222222",
            "ru",
            "909999999",
        )

        self.assertTrue(first)
        self.assertFalse(second)
        user = self.storage.get_user(123456789)
        self.assertEqual(user["account"], "1111111111")
        self.assertEqual(user["language"], "uz")
        self.storage.link_account(
            123456789,
            "2222222222",
            "approved",
            "telegram_phone_match",
        )
        accounts = self.storage.linked_accounts(123456789)
        self.assertEqual(
            {item["account"] for item in accounts},
            {"1111111111", "2222222222"},
        )
        self.assertTrue(self.storage.set_active_account(123456789, "2222222222"))
        self.assertEqual(self.storage.get_user(123456789)["account"], "2222222222")

    def test_pending_request_can_only_be_approved_once(self) -> None:
        self.storage.create_user_if_absent(123456789, "1111111111", "uz")

        first = self.storage.transition_account_status(
            123456789,
            "1111111111",
            "pending",
            "approved",
            "operator:1",
        )
        second = self.storage.transition_account_status(
            123456789,
            "1111111111",
            "pending",
            "approved",
            "operator:2",
        )

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(
            self.storage.get_linked_account(123456789, "1111111111")["status"],
            "approved",
        )

    def test_processed_request_cannot_be_rejected_later(self) -> None:
        self.storage.create_user_if_absent(123456789, "1111111111", "uz")
        self.storage.transition_account_status(
            123456789,
            "1111111111",
            "pending",
            "approved",
            "operator:1",
        )

        changed = self.storage.transition_account_status(
            123456789,
            "1111111111",
            "pending",
            "rejected",
            "operator:2",
        )

        self.assertFalse(changed)
        self.assertEqual(
            self.storage.get_linked_account(123456789, "1111111111")["status"],
            "approved",
        )

    def test_pending_additional_account_appears_for_operator(self) -> None:
        self.storage.create_user_if_absent(
            123456789,
            "1111111111",
            "uz",
            status="approved",
        )
        self.storage.link_account(
            123456789,
            "2222222222",
            "pending",
            "operator_required",
        )

        pending = self.storage.pending_users()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["account"], "2222222222")
        self.assertEqual(pending[0]["telegram_id"], 123456789)
        self.assertEqual(self.storage.pending_account_count(), 1)
        self.assertEqual(self.storage.stats()["pending"], 1)

    def test_unapproved_account_cannot_be_made_active(self) -> None:
        self.storage.create_user_if_absent(
            123456789,
            "1111111111",
            "uz",
            status="approved",
        )
        self.storage.link_account(
            123456789,
            "2222222222",
            "pending",
            "operator_required",
        )

        self.assertFalse(self.storage.set_active_account(123456789, "2222222222"))
        self.assertEqual(self.storage.get_user(123456789)["account"], "1111111111")

    def test_all_approved_accounts_includes_every_linked_home(self) -> None:
        self.storage.create_user_if_absent(
            123456789,
            "1111111111",
            "uz",
            status="approved",
        )
        self.storage.link_account(
            123456789,
            "2222222222",
            "approved",
            "telegram_phone_match",
        )

        accounts = self.storage.all_approved_accounts()

        self.assertEqual(
            {item["account"] for item in accounts},
            {"1111111111", "2222222222"},
        )

    def test_debt_warnings_are_tracked_per_account(self) -> None:
        self.storage.save_debt_warning(
            123456789,
            "1111111111",
            "100000",
        )
        self.storage.save_debt_warning(
            123456789,
            "2222222222",
            "200000",
        )

        first = self.storage.last_debt_warning(
            123456789,
            "1111111111",
        )
        second = self.storage.last_debt_warning(
            123456789,
            "2222222222",
        )

        self.assertEqual(first["debit"], "100000")
        self.assertEqual(second["debit"], "200000")

    def test_debt_run_success_is_idempotent_per_account(self) -> None:
        self.storage.save_debt_warning_log(
            123456789,
            "1111111111",
            "100000",
            "uz",
            "13.06.2026",
            "sent",
            run_id="run-20260613",
        )

        self.assertTrue(
            self.storage.debt_warning_succeeded_in_run(
                123456789,
                "1111111111",
                "run-20260613",
            )
        )
        self.assertFalse(
            self.storage.debt_warning_succeeded_in_run(
                123456789,
                "2222222222",
                "run-20260613",
            )
        )
        self.assertFalse(
            self.storage.debt_warning_succeeded_in_run(
                123456789,
                "1111111111",
                "run-next",
            )
        )


class LegacyMigrationTests(unittest.TestCase):
    def test_existing_users_are_migrated_to_user_accounts(self) -> None:
        test_dir = Path("work") / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        database_path = test_dir / f"legacy_migration_{uuid4().hex}.sqlite3"
        db = sqlite3.connect(database_path)
        try:
            db.execute(
                """
                create table users (
                    telegram_id integer primary key,
                    account text not null,
                    language text not null,
                    phone text,
                    status text not null default 'approved',
                    created_at text default current_timestamp,
                    updated_at text default current_timestamp
                )
                """
            )
            db.execute(
                """
                insert into users (telegram_id, account, language, status)
                values (123456789, '1111111111', 'uz', 'approved')
                """
            )
            db.commit()
        finally:
            db.close()

        storage = BotStorage(str(database_path))
        linked = storage.get_linked_account(123456789, "1111111111")
        self.assertIsNotNone(linked)
        self.assertEqual(linked["status"], "approved")
        self.assertEqual(linked["verification_method"], "legacy")
        gc.collect()
        database_path.unlink(missing_ok=True)

    def test_legacy_debt_warning_key_is_migrated(self) -> None:
        test_dir = Path("work") / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        database_path = (
            test_dir / f"legacy_debt_{uuid4().hex}.sqlite3"
        )
        storage = BotStorage(str(database_path))
        with storage._connect() as db:
            db.execute("drop table debt_warnings")
            db.execute(
                """
                create table debt_warnings (
                    telegram_id integer primary key,
                    account text not null,
                    debit text not null,
                    sent_at text default current_timestamp
                )
                """
            )
            db.execute(
                """
                insert into debt_warnings
                    (telegram_id, account, debit)
                values (123456789, '1111111111', '100000')
                """
            )

        migrated = BotStorage(str(database_path))
        migrated.save_debt_warning(
            123456789,
            "2222222222",
            "200000",
        )

        self.assertIsNotNone(
            migrated.last_debt_warning(123456789, "1111111111")
        )
        self.assertIsNotNone(
            migrated.last_debt_warning(123456789, "2222222222")
        )
        gc.collect()
        database_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
