import logging

from uzwatermu.logging_setup import RedactSecretsFilter
from uzwatermu.security.masking import mask_phone
from uzwatermu.security.rate_limit import RequestRateLimiter


def test_token_is_redacted_in_logs():
    record = logging.LogRecord("x", logging.INFO, "", 0, "token %s", ("123456:" + "A" * 30,), None)
    RedactSecretsFilter().filter(record)
    assert "AAAA" not in record.getMessage()


def test_mask_phone():
    assert mask_phone("+998901234567") == "+998 90 *** * 567"


def test_rate_limit_blocks_after_limit():
    limiter = RequestRateLimiter(window_seconds=10, block_seconds=60)
    assert all(limiter.check(1, 3, now=float(i)).allowed for i in range(3))
    assert not limiter.check(1, 3, now=3.0).allowed
