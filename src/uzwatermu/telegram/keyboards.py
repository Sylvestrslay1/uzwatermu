from telebot import types

from uzwatermu.locales import LANGUAGE_BUTTONS


def language_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*LANGUAGE_BUTTONS)
    return markup
