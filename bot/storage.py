from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

_USER_STATUSES = {"pending", "approved", "rejected"}
_ACCOUNT_STATUSES = {"pending", "approved", "rejected"}
_SUBMISSION_STATUSES = {"received", "pending_review", "approved", "rejected", "auto_approved", "auto_rejected"}

_ALLOWED_SCHEMA_TABLES = frozenset({
    "users", "user_accounts", "submissions", "meter_photos", "meter_references",
    "operators", "debt_warnings", "audit_logs", "app_settings", "debt_warning_logs",
    "inspector_users", "inspector_location_sessions", "inspector_location_responses",
    "inspector_location_relays", "admin_access_attempts", "meter_review_messages",
})
_ALLOWED_COLUMN_RE = re.compile(r"^[a-z][a-z0-9_]{0,59}$")


class BotStorage:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30)
        db.execute("pragma busy_timeout=30000")
        db.execute("pragma journal_mode=WAL")
        db.execute("pragma synchronous=FULL")
        db.execute("pragma foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _init(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                create table if not exists users (
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
            self._ensure_user_status_column(db)
            db.execute(
                """
                create table if not exists user_accounts (
                    telegram_id integer not null,
                    account text not null,
                    status text not null default 'pending',
                    verification_method text,
                    created_at text default current_timestamp,
                    updated_at text default current_timestamp,
                    primary key (telegram_id, account)
                )
                """
            )
            db.execute(
                """
                insert or ignore into user_accounts
                    (telegram_id, account, status, verification_method, created_at, updated_at)
                select telegram_id, account, status, 'legacy', created_at, updated_at
                from users
                """
            )
            db.execute(
                """
                create table if not exists submissions (
                    id integer primary key autoincrement,
                    telegram_id integer not null,
                    account text not null,
                    photo_count integer not null,
                    language text,
                    inspector_fio text,
                    status text not null default 'received',
                    created_at text default current_timestamp
                )
                """
            )
            self._ensure_column(db, "submissions", "language", "text")
            self._ensure_column(db, "submissions", "inspector_fio", "text")
            self._ensure_column(db, "submissions", "status", "text not null default 'received'")
            self._ensure_column(db, "submissions", "similarity_score", "real")
            self._ensure_column(db, "submissions", "decision_reason", "text")
            self._ensure_column(db, "submissions", "decided_by", "integer")
            self._ensure_column(db, "submissions", "decided_at", "text")
            db.execute(
                """
                create table if not exists meter_photos (
                    id integer primary key autoincrement,
                    submission_id integer not null,
                    slot_index integer not null,
                    telegram_file_id text not null,
                    encrypted_path text not null,
                    sha256 text not null,
                    fingerprint text not null,
                    comparison_score real,
                    created_at text default current_timestamp,
                    unique (submission_id, slot_index),
                    foreign key (submission_id) references submissions(id)
                        on delete cascade
                )
                """
            )
            db.execute(
                """
                create table if not exists meter_references (
                    id integer primary key autoincrement,
                    account text not null,
                    slot_index integer not null,
                    photo_id integer not null,
                    fingerprint text not null,
                    approved_by integer,
                    created_at text default current_timestamp,
                    unique (account, slot_index, photo_id),
                    foreign key (photo_id) references meter_photos(id)
                        on delete cascade
                )
                """
            )
            db.execute(
                "create index if not exists idx_meter_refs_account "
                "on meter_references(account, slot_index, id desc)"
            )
            db.execute(
                """
                create table if not exists operators (
                    telegram_id integer primary key,
                    language text,
                    created_at text default current_timestamp,
                    updated_at text default current_timestamp
                )
                """
            )
            db.execute(
                """
                create table if not exists debt_warnings (
                    telegram_id integer not null,
                    account text not null,
                    debit text not null,
                    sent_at text default current_timestamp,
                    primary key (telegram_id, account)
                )
                """
            )
            self._ensure_debt_warning_account_key(db)
            db.execute(
                """
                create table if not exists audit_logs (
                    id integer primary key autoincrement,
                    actor_id integer,
                    action text not null,
                    details text,
                    created_at text default current_timestamp
                )
                """
            )
            db.execute(
                """
                create table if not exists app_settings (
                    key text primary key,
                    value text,
                    updated_at text default current_timestamp
                )
                """
            )
            db.execute(
                """
                create table if not exists debt_warning_logs (
                    id integer primary key autoincrement,
                    telegram_id integer not null,
                    account text not null,
                    debit text not null,
                    language text,
                    statement_date text,
                    status text not null,
                    error text,
                    run_id text,
                    created_at text default current_timestamp
                )
                """
            )
            self._ensure_column(db, "debt_warning_logs", "run_id", "text")
            db.execute(
                """
                create index if not exists idx_user_accounts_status
                on user_accounts(status, telegram_id, account)
                """
            )
            db.execute(
                """
                create index if not exists idx_debt_warning_logs_run
                on debt_warning_logs(run_id, telegram_id, account, status)
                """
            )
            db.execute(
                """
                create index if not exists idx_debt_warning_logs_created
                on debt_warning_logs(created_at)
                """
            )
            db.execute(
                """
                create table if not exists inspector_users (
                    telegram_id integer primary key,
                    area text,
                    fio text,
                    phone text,
                    language text not null default 'uz',
                    status text not null default 'active',
                    created_at text default current_timestamp,
                    updated_at text default current_timestamp
                )
                """
            )
            self._ensure_column(
                db,
                "inspector_users",
                "language",
                "text not null default 'uz'",
            )
            db.execute(
                """
                create table if not exists inspector_location_sessions (
                    id integer primary key autoincrement,
                    requested_by integer not null,
                    status text not null default 'active',
                    requested_at text not null,
                    reminder_at text not null,
                    final_at text not null,
                    completed_at text
                )
                """
            )
            db.execute(
                """
                create table if not exists inspector_location_responses (
                    session_id integer not null,
                    inspector_id integer not null,
                    status text not null default 'pending',
                    command_sent_at text,
                    reminder_sent_at text,
                    first_live_at text,
                    last_live_at text,
                    latitude real,
                    longitude real,
                    live_period integer,
                    source_message_id integer,
                    error text,
                    primary key (session_id, inspector_id),
                    foreign key(session_id)
                        references inspector_location_sessions(id)
                        on delete cascade
                )
                """
            )
            db.execute(
                """
                create table if not exists inspector_location_relays (
                    session_id integer not null,
                    inspector_id integer not null,
                    admin_id integer not null,
                    message_id integer not null,
                    primary key (session_id, inspector_id, admin_id),
                    foreign key(session_id)
                        references inspector_location_sessions(id)
                        on delete cascade
                )
                """
            )
            db.execute(
                """
                create index if not exists idx_inspector_location_status
                on inspector_location_responses(session_id, status)
                """
            )
            db.execute(
                """
                create table if not exists admin_access_attempts (
                    telegram_id integer primary key,
                    failed_count integer not null default 0,
                    window_started text,
                    blocked_until text,
                    last_attempt text
                )
                """
            )
            db.execute(
                """
                create table if not exists meter_review_messages (
                    id integer primary key autoincrement,
                    submission_id integer not null,
                    chat_id integer not null,
                    message_id integer not null,
                    source text not null default 'staff',
                    created_at text default current_timestamp,
                    unique (submission_id, chat_id, message_id),
                    foreign key (submission_id) references submissions(id)
                        on delete cascade
                )
                """
            )
            db.execute(
                """
                create index if not exists idx_meter_review_messages_submission
                on meter_review_messages(submission_id)
                """
            )

    def _ensure_user_status_column(self, db: sqlite3.Connection) -> None:
        self._ensure_column(db, "users", "status", "text not null default 'approved'")

    def _ensure_debt_warning_account_key(
        self,
        db: sqlite3.Connection,
    ) -> None:
        columns = db.execute("pragma table_info(debt_warnings)").fetchall()
        primary_key = [
            row[1]
            for row in sorted(columns, key=lambda row: row[5])
            if row[5]
        ]
        if primary_key == ["telegram_id", "account"]:
            return
        db.execute("alter table debt_warnings rename to debt_warnings_legacy")
        db.execute(
            """
            create table debt_warnings (
                telegram_id integer not null,
                account text not null,
                debit text not null,
                sent_at text default current_timestamp,
                primary key (telegram_id, account)
            )
            """
        )
        db.execute(
            """
            insert or replace into debt_warnings
                (telegram_id, account, debit, sent_at)
            select telegram_id, account, debit, sent_at
            from debt_warnings_legacy
            """
        )
        db.execute("drop table debt_warnings_legacy")

    def _ensure_column(self, db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        if table not in _ALLOWED_SCHEMA_TABLES:
            raise ValueError(f"_ensure_column: ruxsat etilmagan jadval: {table!r}")
        if not _ALLOWED_COLUMN_RE.match(column):
            raise ValueError(f"_ensure_column: ruxsat etilmagan ustun nomi: {column!r}")
        columns = {row[1] for row in db.execute(f"pragma table_info({table})").fetchall()}
        if column not in columns:
            db.execute(f"alter table {table} add column {column} {definition}")

    def save_user(
        self,
        telegram_id: int,
        account: str,
        language: str,
        phone: str = "",
        status: str = "approved",
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into users (telegram_id, account, language, phone, status)
                values (?, ?, ?, ?, ?)
                on conflict(telegram_id) do update set
                    account=excluded.account,
                    language=excluded.language,
                    phone=coalesce(nullif(excluded.phone, ''), users.phone),
                    status=excluded.status,
                    updated_at=current_timestamp
                """,
                (telegram_id, account, language, phone, status),
            )

    def create_user_if_absent(
        self,
        telegram_id: int,
        account: str,
        language: str,
        phone: str = "",
        status: str = "pending",
    ) -> bool:
        """Bind a Telegram profile once without overwriting an existing account."""
        with self._connect() as db:
            cursor = db.execute(
                """
                insert or ignore into users
                    (telegram_id, account, language, phone, status)
                values (?, ?, ?, ?, ?)
                """,
                (telegram_id, account, language, phone, status),
            )
            if cursor.rowcount == 1:
                db.execute(
                    """
                    insert or ignore into user_accounts
                        (telegram_id, account, status, verification_method)
                    values (?, ?, ?, ?)
                    """,
                    (telegram_id, account, status, "registration"),
                )
            return cursor.rowcount == 1

    def link_account(
        self,
        telegram_id: int,
        account: str,
        status: str,
        verification_method: str,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into user_accounts
                    (telegram_id, account, status, verification_method)
                values (?, ?, ?, ?)
                on conflict(telegram_id, account) do update set
                    status=excluded.status,
                    verification_method=excluded.verification_method,
                    updated_at=current_timestamp
                """,
                (telegram_id, account, status, verification_method),
            )

    def get_linked_account(self, telegram_id: int, account: str) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select telegram_id, account, status, verification_method, created_at, updated_at
                from user_accounts
                where telegram_id=? and account=?
                """,
                (telegram_id, account),
            ).fetchone()
            return dict(row) if row else None

    def linked_accounts(self, telegram_id: int, status: str = "approved") -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select telegram_id, account, status, verification_method, created_at, updated_at
                from user_accounts
                where telegram_id=? and status=?
                order by created_at, account
                """,
                (telegram_id, status),
            ).fetchall()
            return [dict(row) for row in rows]

    def set_active_account(self, telegram_id: int, account: str) -> bool:
        with self._connect() as db:
            linked = db.execute(
                """
                select 1 from user_accounts
                where telegram_id=? and account=? and status='approved'
                """,
                (telegram_id, account),
            ).fetchone()
            if not linked:
                return False
            cursor = db.execute(
                """
                update users
                set account=?, status='approved', updated_at=current_timestamp
                where telegram_id=?
                """,
                (account, telegram_id),
            )
            return cursor.rowcount == 1

    def update_status(self, telegram_id: int, status: str) -> None:
        if status not in _USER_STATUSES:
            raise ValueError(f"Noto'g'ri foydalanuvchi statusi: {status!r}")
        with self._connect() as db:
            db.execute(
                "update users set status=?, updated_at=current_timestamp where telegram_id=?",
                (status, telegram_id),
            )

    def transition_user_status(
        self,
        telegram_id: int,
        expected_status: str,
        new_status: str,
    ) -> bool:
        if new_status not in _USER_STATUSES:
            raise ValueError(f"Noto'g'ri foydalanuvchi statusi: {new_status!r}")
        with self._connect() as db:
            cursor = db.execute(
                """
                update users
                set status=?, updated_at=current_timestamp
                where telegram_id=? and status=?
                """,
                (new_status, telegram_id, expected_status),
            )
            return cursor.rowcount == 1

    def transition_account_status(
        self,
        telegram_id: int,
        account: str,
        expected_status: str,
        new_status: str,
        verification_method: str,
    ) -> bool:
        if new_status not in _ACCOUNT_STATUSES:
            raise ValueError(f"Noto'g'ri hisob statusi: {new_status!r}")
        with self._connect() as db:
            cursor = db.execute(
                """
                update user_accounts
                set status=?, verification_method=?, updated_at=current_timestamp
                where telegram_id=? and account=? and status=?
                """,
                (
                    new_status,
                    verification_method,
                    telegram_id,
                    account,
                    expected_status,
                ),
            )
            return cursor.rowcount == 1

    def update_phone(self, telegram_id: int, phone: str) -> None:
        with self._connect() as db:
            db.execute(
                "update users set phone=?, updated_at=current_timestamp where telegram_id=?",
                (phone, telegram_id),
            )

    def get_user(self, telegram_id: int) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                "select telegram_id, account, language, phone, status from users where telegram_id=?",
                (telegram_id,),
            ).fetchone()
            return dict(row) if row else None

    def save_submission(
        self,
        telegram_id: int,
        account: str,
        photo_count: int,
        language: str = "",
        inspector_fio: str = "",
        status: str = "received",
    ) -> int:
        if status not in _SUBMISSION_STATUSES:
            raise ValueError(f"Noto'g'ri status: {status!r}. Ruxsat etilganlar: {_SUBMISSION_STATUSES}")
        with self._connect() as db:
            cursor = db.execute(
                """
                insert into submissions (telegram_id, account, photo_count, language, inspector_fio, status)
                values (?, ?, ?, ?, ?, ?)
                """,
                (telegram_id, account, photo_count, language, inspector_fio, status),
            )
            return int(cursor.lastrowid)

    def save_meter_submission(
        self,
        telegram_id: int,
        account: str,
        language: str,
        inspector_fio: str,
        status: str,
        photos: list[dict[str, object]],
        similarity_score: float | None = None,
        decision_reason: str = "",
    ) -> int:
        if status not in _SUBMISSION_STATUSES:
            raise ValueError(f"Noto'g'ri submission statusi: {status!r}")
        with self._connect() as db:
            cursor = db.execute(
                """
                insert into submissions (
                    telegram_id, account, photo_count, language,
                    inspector_fio, status, similarity_score, decision_reason
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telegram_id,
                    account,
                    len(photos),
                    language,
                    inspector_fio,
                    status,
                    similarity_score,
                    decision_reason,
                ),
            )
            submission_id = int(cursor.lastrowid)
            for slot_index, photo in enumerate(photos, 1):
                db.execute(
                    """
                    insert into meter_photos (
                        submission_id, slot_index, telegram_file_id,
                        encrypted_path, sha256, fingerprint, comparison_score
                    )
                    values (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        submission_id,
                        slot_index,
                        str(photo["telegram_file_id"]),
                        str(photo["encrypted_path"]),
                        str(photo["sha256"]),
                        str(photo["fingerprint"]),
                        photo.get("comparison_score"),
                    ),
                )
            return submission_id

    def meter_submission(self, submission_id: int) -> dict[str, object] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select id, telegram_id, account, photo_count, language,
                       inspector_fio, status, similarity_score,
                       decision_reason, decided_by, decided_at, created_at
                from submissions where id=?
                """,
                (submission_id,),
            ).fetchone()
            return dict(row) if row else None

    def meter_submission_photos(self, submission_id: int) -> list[dict[str, object]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select id, submission_id, slot_index, telegram_file_id,
                       encrypted_path, sha256, fingerprint, comparison_score,
                       created_at
                from meter_photos
                where submission_id=?
                order by slot_index
                """,
                (submission_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def meter_reference_fingerprints(self, account: str) -> list[str]:
        with self._connect() as db:
            rows = db.execute(
                """
                select mr.fingerprint
                from meter_references mr
                join (
                    select slot_index, max(id) as latest_id
                    from meter_references
                    where account=?
                    group by slot_index
                ) latest on latest.latest_id=mr.id
                order by mr.slot_index
                """,
                (account,),
            ).fetchall()
            return [str(row[0]) for row in rows]

    def save_review_message(
        self,
        submission_id: int,
        chat_id: int,
        message_id: int,
        source: str = "staff",
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert or ignore into meter_review_messages
                    (submission_id, chat_id, message_id, source)
                values (?, ?, ?, ?)
                """,
                (submission_id, chat_id, message_id, source),
            )

    def get_review_messages(
        self, submission_id: int
    ) -> list[dict[str, int | str]]:
        with self._connect() as db:
            rows = db.execute(
                """
                select chat_id, message_id, source
                from meter_review_messages
                where submission_id=?
                order by id
                """,
                (submission_id,),
            ).fetchall()
            return [
                {"chat_id": r[0], "message_id": r[1], "source": r[2]}
                for r in rows
            ]

    def delete_review_messages(self, submission_id: int) -> None:
        with self._connect() as db:
            db.execute(
                "delete from meter_review_messages where submission_id=?",
                (submission_id,),
            )

    def meter_reference_paths(self) -> list[str]:
        with self._connect() as db:
            rows = db.execute(
                """
                select distinct mp.encrypted_path
                from meter_references mr
                join meter_photos mp on mp.id=mr.photo_id
                order by mp.encrypted_path
                """
            ).fetchall()
            return [str(row[0]) for row in rows]

    def purge_expired_rejected_meter_submissions(
        self,
        retention_days: int = 90,
    ) -> list[str]:
        days = max(int(retention_days), 1)
        with self._connect() as db:
            rows = db.execute(
                """
                select distinct mp.encrypted_path
                from meter_photos mp
                join submissions s on s.id=mp.submission_id
                left join meter_references mr on mr.photo_id=mp.id
                where s.status in ('rejected', 'auto_rejected')
                  and mr.id is null
                  and datetime(s.created_at) < datetime('now', ?)
                """,
                (f"-{days} days",),
            ).fetchall()
            db.execute(
                """
                delete from submissions
                where status in ('rejected', 'auto_rejected')
                  and datetime(created_at) < datetime('now', ?)
                  and not exists (
                      select 1
                      from meter_photos mp
                      join meter_references mr on mr.photo_id=mp.id
                      where mp.submission_id=submissions.id
                  )
                """,
                (f"-{days} days",),
            )
            return [str(row[0]) for row in rows]

    def transition_meter_submission(
        self,
        submission_id: int,
        expected_status: str,
        target_status: str,
        actor_id: int | None,
        reason: str,
        *,
        create_references: bool = False,
    ) -> bool:
        if target_status not in _SUBMISSION_STATUSES:
            raise ValueError(f"Noto'g'ri submission statusi: {target_status!r}")
        with self._connect() as db:
            cursor = db.execute(
                """
                update submissions
                set status=?, decision_reason=?, decided_by=?,
                    decided_at=current_timestamp
                where id=? and status=?
                """,
                (
                    target_status,
                    reason,
                    actor_id,
                    submission_id,
                    expected_status,
                ),
            )
            if cursor.rowcount != 1:
                return False
            if create_references:
                submission = db.execute(
                    "select account from submissions where id=?",
                    (submission_id,),
                ).fetchone()
                if not submission:
                    raise RuntimeError("Hisoblagich arizasi topilmadi.")
                db.execute(
                    """
                    insert or ignore into meter_references (
                        account, slot_index, photo_id, fingerprint, approved_by
                    )
                    select ?, slot_index, id, fingerprint, ?
                    from meter_photos
                    where submission_id=?
                    """,
                    (str(submission[0]), actor_id, submission_id),
                )
            return True

    def stats(self) -> dict[str, int]:
        with self._connect() as db:
            users = db.execute("select count(*) from users").fetchone()[0]
            submissions = db.execute("select count(*) from submissions").fetchone()[0]
            photos = db.execute("select coalesce(sum(photo_count), 0) from submissions").fetchone()[0]
            operators = db.execute("select count(*) from operators").fetchone()[0]
            pending = db.execute(
                "select count(*) from user_accounts where status='pending'"
            ).fetchone()[0]
            return {
                "users": int(users),
                "submissions": int(submissions),
                "photos": int(photos),
                "operators": int(operators),
                "pending": int(pending),
            }

    def user_status_counts(self) -> dict[str, int]:
        with self._connect() as db:
            rows = db.execute("select status, count(*) from users group by status").fetchall()
            return {str(row[0] or "-"): int(row[1]) for row in rows}

    def user_language_counts(self) -> dict[str, int]:
        with self._connect() as db:
            rows = db.execute("select language, count(*) from users group by language").fetchall()
            return {str(row[0] or "-"): int(row[1]) for row in rows}

    def all_user_ids(self) -> list[int]:
        with self._connect() as db:
            rows = db.execute(
                "select telegram_id from users where status='approved' order by created_at"
            ).fetchall()
            return [int(row[0]) for row in rows]

    def all_users(self) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select telegram_id, account, language, phone, status, created_at, updated_at
                from users
                where status='approved'
                order by created_at
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def all_approved_accounts(self) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select u.telegram_id, ua.account, u.language, u.phone,
                       ua.status, ua.created_at, ua.updated_at
                from user_accounts ua
                join users u on u.telegram_id=ua.telegram_id
                where u.status='approved' and ua.status='approved'
                order by ua.created_at, ua.account
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def all_user_records(self) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select telegram_id, account, language, phone, status, created_at, updated_at
                from users
                order by created_at
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def recent_submissions(self, limit: int = 10) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select id, telegram_id, account, photo_count, language,
                       inspector_fio, status, similarity_score,
                       decision_reason, decided_by, decided_at, created_at
                from submissions
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def pending_users(self, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select ua.telegram_id, ua.account, u.language, u.phone,
                       ua.status, ua.created_at, ua.updated_at
                from user_accounts ua
                join users u on u.telegram_id=ua.telegram_id
                where ua.status='pending'
                order by ua.created_at, ua.updated_at, ua.telegram_id
                limit ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def pending_account_count(self) -> int:
        with self._connect() as db:
            row = db.execute(
                "select count(*) from user_accounts where status='pending'"
            ).fetchone()
            return int(row[0] or 0)

    def add_operator(self, telegram_id: int) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into operators (telegram_id)
                values (?)
                on conflict(telegram_id) do update set updated_at=current_timestamp
                """,
                (telegram_id,),
            )

    def remove_operator(self, telegram_id: int) -> None:
        with self._connect() as db:
            db.execute("delete from operators where telegram_id=?", (telegram_id,))

    def get_operator(self, telegram_id: int) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                "select telegram_id, language, created_at, updated_at from operators where telegram_id=?",
                (telegram_id,),
            ).fetchone()
            return dict(row) if row else None

    def save_operator_language(self, telegram_id: int, language: str) -> None:
        with self._connect() as db:
            db.execute(
                "update operators set language=?, updated_at=current_timestamp where telegram_id=?",
                (language, telegram_id),
            )

    def operators(self) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "select telegram_id, language, created_at, updated_at from operators order by created_at"
            ).fetchall()
            return [dict(row) for row in rows]

    def clear_test_data(self) -> None:
        with self._connect() as db:
            db.execute("delete from submissions")
            db.execute("delete from user_accounts")
            db.execute("delete from users")
            db.execute("delete from debt_warnings")
            db.execute("delete from debt_warning_logs")

    def last_debt_warning(
        self,
        telegram_id: int,
        account: str,
    ) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select telegram_id, account, debit, sent_at
                from debt_warnings
                where telegram_id=? and account=?
                """,
                (telegram_id, account),
            ).fetchone()
            return dict(row) if row else None

    def save_debt_warning(self, telegram_id: int, account: str, debit: str) -> None:
        sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as db:
            db.execute(
                """
                insert into debt_warnings (telegram_id, account, debit, sent_at)
                values (?, ?, ?, ?)
                on conflict(telegram_id, account) do update set
                    debit=excluded.debit,
                    sent_at=excluded.sent_at
                """,
                (telegram_id, account, debit, sent_at),
            )

    def save_debt_warning_log(
        self,
        telegram_id: int,
        account: str,
        debit: str,
        language: str,
        statement_date: str,
        status: str,
        error: str = "",
        run_id: str = "",
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into debt_warning_logs
                    (telegram_id, account, debit, language, statement_date,
                     status, error, run_id)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telegram_id,
                    account,
                    debit,
                    language,
                    statement_date,
                    status,
                    error,
                    run_id,
                ),
            )

    def debt_warning_succeeded_in_run(
        self,
        telegram_id: int,
        account: str,
        run_id: str,
    ) -> bool:
        if not run_id:
            return False
        with self._connect() as db:
            row = db.execute(
                """
                select 1
                from debt_warning_logs
                where run_id=? and telegram_id=? and account=?
                  and status='sent'
                limit 1
                """,
                (run_id, telegram_id, account),
            ).fetchone()
            return row is not None

    def recent_debt_warning_logs(self, limit: int = 50) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select id, telegram_id, account, debit, language, statement_date, status, error, created_at
                from debt_warning_logs
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def all_debt_warning_logs(self, limit: int = 10000) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select id, telegram_id, account, debit, language, statement_date, status, error, created_at
                from debt_warning_logs
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def add_inspector_user(self, telegram_id: int, area: str, fio: str, phone: str = "") -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into inspector_users (telegram_id, area, fio, phone)
                values (?, ?, ?, ?)
                on conflict(telegram_id) do update set
                    area=excluded.area,
                    fio=excluded.fio,
                    phone=excluded.phone,
                    status='active',
                    updated_at=current_timestamp
                """,
                (telegram_id, area, fio, phone),
            )

    def inspector_users(self) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select telegram_id, area, fio, phone, language, status,
                       created_at, updated_at
                from inspector_users
                order by area, fio
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_inspector_user(
        self,
        telegram_id: int,
    ) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select telegram_id, area, fio, phone, language, status,
                       created_at, updated_at
                from inspector_users
                where telegram_id=?
                """,
                (telegram_id,),
            ).fetchone()
            return dict(row) if row else None

    def active_inspector_users(self) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select telegram_id, area, fio, phone, language, status,
                       created_at, updated_at
                from inspector_users
                where status='active'
                order by area, fio
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def create_inspector_location_session(
        self,
        requested_by: int,
        requested_at: str,
        reminder_at: str,
        final_at: str,
    ) -> tuple[int, list[dict[str, str]]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            active = db.execute(
                """
                select id, requested_by, status, requested_at, reminder_at,
                       final_at, completed_at
                from inspector_location_sessions
                where status in ('active', 'reminded')
                order by id desc
                limit 1
                """
            ).fetchone()
            if active:
                return int(active["id"]), []
            inspectors = db.execute(
                """
                select telegram_id, area, fio, phone, language, status
                from inspector_users
                where status='active'
                order by area, fio
                """
            ).fetchall()
            cursor = db.execute(
                """
                insert into inspector_location_sessions
                    (requested_by, requested_at, reminder_at, final_at)
                values (?, ?, ?, ?)
                """,
                (requested_by, requested_at, reminder_at, final_at),
            )
            session_id = int(cursor.lastrowid)
            db.executemany(
                """
                insert into inspector_location_responses
                    (session_id, inspector_id, status)
                values (?, ?, 'pending')
                """,
                [
                    (session_id, int(item["telegram_id"]))
                    for item in inspectors
                ],
            )
            return session_id, [dict(item) for item in inspectors]

    def active_inspector_location_session(
        self,
    ) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select id, requested_by, status, requested_at, reminder_at,
                       final_at, completed_at
                from inspector_location_sessions
                where status in ('active', 'reminded')
                order by id desc
                limit 1
                """
            ).fetchone()
            return dict(row) if row else None

    def inspector_location_session_for_update(
        self,
        inspector_id: int,
        source_message_id: int,
    ) -> dict[str, str] | None:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select s.id, s.requested_by, s.status, s.requested_at,
                       s.reminder_at, s.final_at, s.completed_at
                from inspector_location_sessions s
                join inspector_location_responses r
                  on r.session_id=s.id
                where r.inspector_id=? and r.source_message_id=?
                  and r.status='live'
                order by s.id desc
                limit 1
                """,
                (inspector_id, source_message_id),
            ).fetchone()
            return dict(row) if row else None

    def inspector_location_responses(
        self,
        session_id: int,
    ) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select r.session_id, r.inspector_id, r.status,
                       r.command_sent_at, r.reminder_sent_at,
                       r.first_live_at, r.last_live_at, r.latitude,
                       r.longitude, r.live_period, r.source_message_id,
                       r.error, i.area, i.fio, i.phone, i.language
                from inspector_location_responses r
                join inspector_users i on i.telegram_id=r.inspector_id
                where r.session_id=?
                order by i.area, i.fio
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_inspector_command_delivery(
        self,
        session_id: int,
        inspector_id: int,
        *,
        delivered: bool,
        sent_at: str,
        error: str = "",
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                update inspector_location_responses
                set command_sent_at=?,
                    status=case when ? then status else 'delivery_failed' end,
                    error=?
                where session_id=? and inspector_id=?
                """,
                (
                    sent_at,
                    1 if delivered else 0,
                    error,
                    session_id,
                    inspector_id,
                ),
            )

    def mark_inspector_location_reminded(
        self,
        session_id: int,
        inspector_id: int,
        sent_at: str,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                update inspector_location_responses
                set reminder_sent_at=?,
                    status=case
                        when status='pending' then 'reminded'
                        else status
                    end
                where session_id=? and inspector_id=?
                  and status in ('pending', 'delivery_failed')
                """,
                (sent_at, session_id, inspector_id),
            )

    def save_inspector_live_location(
        self,
        session_id: int,
        inspector_id: int,
        *,
        latitude: float,
        longitude: float,
        live_period: int,
        source_message_id: int,
        received_at: str,
    ) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                """
                update inspector_location_responses
                set status='live',
                    first_live_at=coalesce(first_live_at, ?),
                    last_live_at=?,
                    latitude=?,
                    longitude=?,
                    live_period=?,
                    source_message_id=?,
                    error=''
                where session_id=? and inspector_id=?
                """,
                (
                    received_at,
                    received_at,
                    latitude,
                    longitude,
                    live_period,
                    source_message_id,
                    session_id,
                    inspector_id,
                ),
            )
            return cursor.rowcount == 1

    def complete_inspector_location_session(
        self,
        session_id: int,
        completed_at: str,
    ) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                """
                update inspector_location_sessions
                set status='completed', completed_at=?
                where id=? and status in ('active', 'reminded')
                """,
                (completed_at, session_id),
            )
            return cursor.rowcount == 1

    def set_inspector_location_session_status(
        self,
        session_id: int,
        status: str,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                update inspector_location_sessions
                set status=?
                where id=?
                """,
                (status, session_id),
            )

    def save_inspector_location_relay(
        self,
        session_id: int,
        inspector_id: int,
        admin_id: int,
        message_id: int,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into inspector_location_relays
                    (session_id, inspector_id, admin_id, message_id)
                values (?, ?, ?, ?)
                on conflict(session_id, inspector_id, admin_id)
                do update set message_id=excluded.message_id
                """,
                (session_id, inspector_id, admin_id, message_id),
            )

    def inspector_location_relays(
        self,
        session_id: int,
        inspector_id: int,
    ) -> list[dict[str, int]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select admin_id, message_id
                from inspector_location_relays
                where session_id=? and inspector_id=?
                """,
                (session_id, inspector_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into app_settings (key, value, updated_at)
                values (?, ?, current_timestamp)
                on conflict(key) do update set
                    value=excluded.value,
                    updated_at=current_timestamp
                """,
                (key, value),
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as db:
            row = db.execute("select value from app_settings where key=?", (key,)).fetchone()
            return str(row[0]) if row and row[0] is not None else default

    def add_audit_log(self, actor_id: int | None, action: str, details: str = "") -> None:
        with self._connect() as db:
            db.execute(
                "insert into audit_logs (actor_id, action, details) values (?, ?, ?)",
                (actor_id, action, details),
            )

    def admin_access_attempt(self, telegram_id: int) -> dict[str, str | int]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                select telegram_id, failed_count, window_started,
                       blocked_until, last_attempt
                from admin_access_attempts
                where telegram_id=?
                """,
                (telegram_id,),
            ).fetchone()
            return dict(row) if row else {
                "telegram_id": telegram_id,
                "failed_count": 0,
                "window_started": "",
                "blocked_until": "",
                "last_attempt": "",
            }

    def save_admin_access_attempt(
        self,
        telegram_id: int,
        failed_count: int,
        window_started: str,
        blocked_until: str,
        last_attempt: str,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                insert into admin_access_attempts
                    (telegram_id, failed_count, window_started,
                     blocked_until, last_attempt)
                values (?, ?, ?, ?, ?)
                on conflict(telegram_id) do update set
                    failed_count=excluded.failed_count,
                    window_started=excluded.window_started,
                    blocked_until=excluded.blocked_until,
                    last_attempt=excluded.last_attempt
                """,
                (
                    telegram_id,
                    failed_count,
                    window_started,
                    blocked_until,
                    last_attempt,
                ),
            )

    def clear_admin_access_attempts(self, telegram_id: int) -> None:
        with self._connect() as db:
            db.execute(
                "delete from admin_access_attempts where telegram_id=?",
                (telegram_id,),
            )

    def recent_audit_logs(self, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                select id, actor_id, action, details, created_at
                from audit_logs
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
