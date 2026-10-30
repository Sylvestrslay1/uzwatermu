"""Foydalanish:
    python -m uzwatermu migrate   # bazani yaratish/yangilash
    python -m uzwatermu run       # botni ishga tushirish
"""

from __future__ import annotations

import logging
import sys

from uzwatermu.config import Settings
from uzwatermu.db.migrate import SchemaError, migrate, verify
from uzwatermu.logging_setup import setup_logging


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "run"
    settings = Settings()
    settings.ensure_dirs()
    setup_logging(settings.log_dir)
    log = logging.getLogger("uzwatermu")

    if command == "migrate":
        version = migrate(settings.database_path)
        log.info("Baza versiyasi: %s (%s)", version, settings.database_path)
        return 0

    if command == "run":
        try:
            verify(settings.database_path)
        except SchemaError as error:
            log.critical("%s", error)
            return 2
        from uzwatermu.telegram.app import build_bot

        bot = build_bot(settings)
        log.info("Bot ishga tushdi. DATA_DIR=%s", settings.var_dir)
        bot.infinity_polling(skip_pending=True)
        return 0

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
