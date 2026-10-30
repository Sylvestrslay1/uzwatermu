from uzwatermu.locales import ru, uz, uz_cyrl

LANGUAGES = {"uz": uz.TEXTS, "uz_cyrl": uz_cyrl.TEXTS, "ru": ru.TEXTS}
DEFAULT_LANGUAGE = "uz"
LANGUAGE_BUTTONS = {"🇺🇿 O'zbek (lotin)": "uz", "🇺🇿 Ўзбек (кирилл)": "uz_cyrl", "🇷🇺 Русский": "ru"}

# Til hali tanlanmaganda ko'rsatiladi, shuning uchun ikki tilda.
BILINGUAL_GREETING = "Assalomu alaykum! Tilni tanlang 👇\nЗдравствуйте! Выберите язык 👇"


def t(language: str, key: str, **kwargs: object) -> str:
    texts = LANGUAGES.get(language, LANGUAGES[DEFAULT_LANGUAGE])
    return texts[key].format(**kwargs) if kwargs else texts[key]


def _build_button_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for texts in LANGUAGES.values():
        for key, label in texts.items():
            if key.startswith("btn."):
                index[label] = key
    return index


_BUTTON_INDEX = _build_button_index()


def button_key(text: str) -> str | None:
    """Tugma matnini (istalgan tilda) kalitga aylantiradi: '⚙️ Настройки' -> 'btn.settings'."""
    return _BUTTON_INDEX.get(text)
