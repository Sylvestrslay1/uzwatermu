from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int = 0
    newly_blocked: bool = False


class RequestRateLimiter:
    def __init__(self, window_seconds: float, block_seconds: float) -> None:
        self.window_seconds = max(window_seconds, 1)
        self.block_seconds = max(block_seconds, 1)
        self._requests: dict[int, deque[float]] = defaultdict(deque)
        self._blocked_until: dict[int, float] = {}
        self._lock = threading.Lock()
        self._last_cleanup = 0.0
        self.total_blocks = 0

    def _cleanup(self, current: float) -> None:
        if current - self._last_cleanup < max(self.window_seconds, 60):
            return
        cutoff = current - max(self.window_seconds, self.block_seconds) * 2
        stale_users = [
            user_id
            for user_id, requests in self._requests.items()
            if not requests or requests[-1] < cutoff
        ]
        for user_id in stale_users:
            self._requests.pop(user_id, None)
        for user_id, deadline in list(self._blocked_until.items()):
            if deadline <= current:
                self._blocked_until.pop(user_id, None)
        self._last_cleanup = current

    def check(
        self,
        user_id: int,
        limit: int,
        now: float | None = None,
    ) -> RateLimitDecision:
        current = time.monotonic() if now is None else now
        maximum = max(limit, 1)
        with self._lock:
            self._cleanup(current)
            blocked_until = self._blocked_until.get(user_id, 0)
            if blocked_until > current:
                return RateLimitDecision(
                    False,
                    max(1, int(blocked_until - current + 0.999)),
                    False,
                )
            self._blocked_until.pop(user_id, None)

            requests = self._requests[user_id]
            cutoff = current - self.window_seconds
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= maximum:
                blocked_until = current + self.block_seconds
                self._blocked_until[user_id] = blocked_until
                requests.clear()
                self.total_blocks += 1
                return RateLimitDecision(
                    False,
                    max(1, int(self.block_seconds)),
                    True,
                )
            requests.append(current)
            return RateLimitDecision(True)

    def active_blocks(self, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        with self._lock:
            expired = [
                user_id
                for user_id, deadline in self._blocked_until.items()
                if deadline <= current
            ]
            for user_id in expired:
                self._blocked_until.pop(user_id, None)
            return len(self._blocked_until)


def file_size_allowed(file_size: int | None, maximum_mb: float) -> bool:
    size = int(file_size or 0)
    maximum_bytes = int(max(maximum_mb, 0) * 1024 * 1024)
    return size > 0 and size <= maximum_bytes


def item_count_allowed(current_count: int, maximum_count: int) -> bool:
    return current_count < max(maximum_count, 1)
