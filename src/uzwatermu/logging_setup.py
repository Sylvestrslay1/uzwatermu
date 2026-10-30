from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(r"\b\d{6,15}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(password|token|secret)\s*[=:]\s*\S+"),
)


class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in _SECRET_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        record.msg = message
        record.args = None
        return True


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    console = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for item in (handler, console):
        item.setFormatter(formatter)
        item.addFilter(RedactSecretsFilter())
    root = logging.getLogger()
    root.handlers[:] = [handler, console]
    root.setLevel(logging.INFO)
