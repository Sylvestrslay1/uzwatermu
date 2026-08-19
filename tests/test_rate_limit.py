from __future__ import annotations

import threading
import unittest
from pathlib import Path

from bot.rate_limit import (
    RequestRateLimiter,
    file_size_allowed,
    item_count_allowed,
)


class RateLimiterTests(unittest.TestCase):
    def test_limit_allows_exact_count_then_blocks(self) -> None:
        limiter = RequestRateLimiter(10, 60)
        for index in range(15):
            self.assertTrue(limiter.check(100, 15, now=float(index) / 10).allowed)

        decision = limiter.check(100, 15, now=2)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.newly_blocked)
        self.assertEqual(60, decision.retry_after)
        self.assertEqual(1, limiter.total_blocks)

    def test_repeated_blocked_request_does_not_increment_total(self) -> None:
        limiter = RequestRateLimiter(10, 60)
        limiter.check(100, 1, now=0)
        first = limiter.check(100, 1, now=1)
        second = limiter.check(100, 1, now=2)
        self.assertTrue(first.newly_blocked)
        self.assertFalse(second.newly_blocked)
        self.assertEqual(1, limiter.total_blocks)

    def test_access_returns_after_block_expires(self) -> None:
        limiter = RequestRateLimiter(10, 5)
        limiter.check(100, 1, now=0)
        limiter.check(100, 1, now=1)
        self.assertTrue(limiter.check(100, 1, now=6).allowed)
        self.assertEqual(0, limiter.active_blocks(now=6))

    def test_users_are_rate_limited_independently(self) -> None:
        limiter = RequestRateLimiter(10, 60)
        self.assertTrue(limiter.check(1, 1, now=0).allowed)
        self.assertFalse(limiter.check(1, 1, now=1).allowed)
        self.assertTrue(limiter.check(2, 1, now=1).allowed)

    def test_parallel_checks_are_thread_safe(self) -> None:
        limiter = RequestRateLimiter(10, 60)
        results: list[bool] = []
        lock = threading.Lock()

        def check() -> None:
            allowed = limiter.check(100, 20, now=1).allowed
            with lock:
                results.append(allowed)

        threads = [threading.Thread(target=check) for _ in range(30)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(20, sum(results))
        self.assertEqual(1, limiter.total_blocks)


class ResourceLimitTests(unittest.TestCase):
    def test_file_size_limit(self) -> None:
        self.assertTrue(file_size_allowed(25 * 1024 * 1024, 25))
        self.assertFalse(file_size_allowed(25 * 1024 * 1024 + 1, 25))
        self.assertFalse(file_size_allowed(0, 25))
        self.assertFalse(file_size_allowed(None, 25))

    def test_item_count_limit(self) -> None:
        self.assertTrue(item_count_allowed(9, 10))
        self.assertFalse(item_count_allowed(10, 10))


class AbuseProtectionRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = Path("bot/main.py").read_text(encoding="utf-8")

    def test_all_public_handlers_use_rate_limit(self) -> None:
        for function_name in (
            "handle_start",
            "handle_myid",
            "handle_admin",
            "handle_approval_callback",
            "handle_meter_review_callback",
            "handle_message",
        ):
            start = self.source.index(f"def {function_name}(")
            next_function = self.source.find("\ndef ", start + 5)
            body = self.source[start:next_function]
            self.assertIn("request_allowed(", body)

    def test_excel_is_checked_before_download(self) -> None:
        start = self.source.index("def admin_upload_excel(")
        end = self.source.index("\ndef admin_confirm_excel_upload(", start)
        body = self.source[start:end]
        self.assertLess(
            body.index("file_size_allowed("),
            body.index("bot.download_file("),
        )

    def test_meter_count_and_size_are_limited(self) -> None:
        start = self.source.index("def handle_meter_photo(")
        end = self.source.index("\ndef request_bot_shutdown(", start)
        body = self.source[start:end]
        self.assertIn("item_count_allowed(", body)
        self.assertIn("file_size_allowed(", body)


if __name__ == "__main__":
    unittest.main()
