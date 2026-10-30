from uzwatermu.locales import LANGUAGE_BUTTONS, LANGUAGES, button_key, t


def test_all_languages_have_same_keys():
    keys = {lang: set(texts) for lang, texts in LANGUAGES.items()}
    reference = keys["uz"]
    for lang, lang_keys in keys.items():
        assert lang_keys == reference, f"{lang}: {lang_keys ^ reference}"


def test_button_labels_are_unambiguous():
    seen: dict[str, str] = {}
    for texts in LANGUAGES.values():
        for key, label in texts.items():
            if key.startswith("btn."):
                assert seen.setdefault(label, key) == key, f"{label!r}: {seen[label]} va {key}"
    assert not set(LANGUAGE_BUTTONS) & set(seen)


def test_button_key_lookup_any_language():
    assert button_key(t("ru", "btn.settings")) == "btn.settings"
    assert button_key(t("uz_cyrl", "btn.back")) == "btn.back"
    assert button_key("salom") is None
