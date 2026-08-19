from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


ADMIN_FAILURE_LIMIT = 5
ADMIN_FAILURE_WINDOW_MINUTES = 10
ADMIN_BLOCK_MINUTES = 30
ADMIN_SESSION_MINUTES = 30


def _parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def admin_access_blocked(state: dict[str, Any], now: datetime | None = None) -> bool:
    current = now or datetime.now()
    blocked_until = _parse_datetime(state.get("blocked_until"))
    return bool(blocked_until and blocked_until > current)


def register_denied_attempt(
    state: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now()
    window_started = _parse_datetime(state.get("window_started"))
    if (
        window_started is None
        or current - window_started > timedelta(minutes=ADMIN_FAILURE_WINDOW_MINUTES)
    ):
        window_started = current
        failed_count = 0
    else:
        failed_count = int(state.get("failed_count") or 0)

    failed_count += 1
    blocked_until = ""
    just_blocked = failed_count >= ADMIN_FAILURE_LIMIT
    if just_blocked:
        blocked_until = (
            current + timedelta(minutes=ADMIN_BLOCK_MINUTES)
        ).isoformat(timespec="seconds")

    return {
        "failed_count": failed_count,
        "window_started": window_started.isoformat(timespec="seconds"),
        "blocked_until": blocked_until,
        "last_attempt": current.isoformat(timespec="seconds"),
        "just_blocked": just_blocked,
    }


def session_deadline(now: datetime | None = None) -> float:
    current = now or datetime.now()
    return (current + timedelta(minutes=ADMIN_SESSION_MINUTES)).timestamp()
