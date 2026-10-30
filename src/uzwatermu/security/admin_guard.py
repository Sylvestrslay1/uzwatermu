"""Admin handlerlari uchun bitta umumiy tekshiruv. Har bir admin handler shu orqali o'tadi."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

STAFF_ROLES = {"operator", "admin"}


def require_role(
    get_role: Callable[[int], str],
    allowed: set[str],
    on_denied: Callable[[Any], None],
) -> Callable:
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        def wrapper(message: Any, *args: Any, **kwargs: Any) -> Any:
            if message.chat.type != "private" or get_role(message.from_user.id) not in allowed:
                on_denied(message)
                return None
            return handler(message, *args, **kwargs)

        return wrapper

    return decorator
