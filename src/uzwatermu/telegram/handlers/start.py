"""1-bosqich namunasi: /start va til tanlash. Qolgan handlerlar shu uslubda qo'shiladi."""

from __future__ import annotations

from telebot import TeleBot, types

from uzwatermu.locales import LANGUAGE_BUTTONS, t
from uzwatermu.repositories.users import UserRepository
from uzwatermu.telegram.keyboards import language_keyboard


def register(bot: TeleBot, users: UserRepository) -> None:
    @bot.message_handler(commands=["start"], chat_types=["private"])
    def handle_start(message: types.Message) -> None:
        bot.send_message(message.chat.id, t("uz", "welcome"), reply_markup=language_keyboard())

    @bot.message_handler(func=lambda m: m.text in LANGUAGE_BUTTONS, chat_types=["private"])
    def handle_language(message: types.Message) -> None:
        language = LANGUAGE_BUTTONS[message.text]
        users.upsert_language(message.from_user.id, language)
        bot.send_message(
            message.chat.id,
            t(language, "ask_account"),
            reply_markup=types.ReplyKeyboardRemove(),
        )
