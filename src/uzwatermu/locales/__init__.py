from uzwatermu.locales import ru, uz, uz_cyrl

LANGUAGES = {"uz": uz.TEXTS, "uz_cyrl": uz_cyrl.TEXTS, "ru": ru.TEXTS}
LANGUAGE_BUTTONS = {"🇺🇿 O'zbek (lotin)": "uz", "🇺🇿 Ўзбек (кирилл)": "uz_cyrl", "🇷🇺 Русский": "ru"}


def t(language: str, key: str, **kwargs: object) -> str:
    texts = LANGUAGES.get(language, LANGUAGES["uz"])
    return texts[key].format(**kwargs)
