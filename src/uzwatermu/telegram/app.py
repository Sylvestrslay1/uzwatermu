from __future__ import annotations

import logging

from telebot import TeleBot

from uzwatermu.config import Settings
from uzwatermu.repositories.users import UserRepository
from uzwatermu.telegram.handlers import start

log = logging.getLogger(__name__)


def build_bot(settings: Settings) -> TeleBot:
    bot = TeleBot(settings.bot_token, threaded=True)
    users = UserRepository(settings.database_path)
    for admin_id in settings.bootstrap_admin_ids:
        users.set_role(admin_id, "admin")
    start.register(bot, users)
    # Keyingi bosqichlar: cabinet, meter, admin handlerlari shu yerda ro'yxatdan o'tadi.
    return bot
