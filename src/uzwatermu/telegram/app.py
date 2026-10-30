"""Telegram bilan bog'lovchi yupqa qatlam: xabarni BotLogic'ga beradi va javobni yuboradi."""

from __future__ import annotations

import logging

from telebot import ExceptionHandler, TeleBot, types

from uzwatermu.config import Settings
from uzwatermu.repositories.account_links import AccountLinkRepository
from uzwatermu.repositories.users import UserRepository
from uzwatermu.telegram.logic import BotLogic, Reply

log = logging.getLogger(__name__)

# Matn bo'lmagan xabarlar (rasm, ovoz, stiker...) hozircha "menyudan tanlang" javobini oladi.
NON_TEXT_TYPES = [
    "audio", "document", "photo", "sticker", "video", "video_note",
    "voice", "contact", "location", "venue", "animation", "poll", "dice",
]


class _LogExceptions(ExceptionHandler):
    def handle(self, exception: Exception) -> bool:
        log.exception("Handler xatosi: %s", type(exception).__name__, exc_info=exception)
        return True


def _markup(reply: Reply) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    for row in reply.keyboard:
        markup.row(*row)
    return markup


def build_bot(settings: Settings) -> TeleBot:
    bot = TeleBot(settings.bot_token, threaded=True, exception_handler=_LogExceptions())
    logic = BotLogic(
        UserRepository(settings.database_path),
        AccountLinkRepository(settings.database_path),
    )

    def send(message: types.Message, reply: Reply) -> None:
        bot.send_message(message.chat.id, reply.text, reply_markup=_markup(reply))

    @bot.message_handler(commands=["start"], chat_types=["private"])
    def on_start(message: types.Message) -> None:
        send(message, logic.start(message.from_user.id))

    @bot.message_handler(content_types=["text"], chat_types=["private"])
    def on_text(message: types.Message) -> None:
        send(message, logic.handle_text(message.from_user.id, message.text or ""))

    @bot.message_handler(content_types=NON_TEXT_TYPES, chat_types=["private"])
    def on_other(message: types.Message) -> None:
        send(message, logic.handle_text(message.from_user.id, ""))

    return bot
