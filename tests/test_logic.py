import pytest

from uzwatermu.db.connection import connect
from uzwatermu.locales import BILINGUAL_GREETING, t
from uzwatermu.repositories.account_links import AccountLinkRepository
from uzwatermu.repositories.users import UserRepository
from uzwatermu.telegram.logic import BotLogic
from uzwatermu.telegram.menus import LANGUAGE_KEYBOARD

UZ = "🇺🇿 O'zbek (lotin)"
RU = "🇷🇺 Русский"


@pytest.fixture
def logic(db_path):
    return BotLogic(UserRepository(db_path), AccountLinkRepository(db_path))


def labels(reply):
    return [label for row in reply.keyboard for label in row]


def test_new_user_gets_bilingual_greeting_and_languages(logic):
    reply = logic.start(1)
    assert reply.text == BILINGUAL_GREETING
    assert reply.keyboard == LANGUAGE_KEYBOARD


def test_text_before_language_asks_language_again(logic):
    assert logic.handle_text(1, "salom").keyboard == LANGUAGE_KEYBOARD


def test_choosing_language_shows_about_and_home_menu(logic):
    reply = logic.handle_text(1, UZ)
    assert reply.text == t("uz", "about")
    assert labels(reply) == [
        t("uz", "btn.register"), t("uz", "btn.help"),
        t("uz", "btn.settings"), t("uz", "btn.contact"),
    ]


def test_language_is_remembered_on_next_start(logic):
    logic.handle_text(1, RU)
    reply = logic.start(1)
    assert reply.text == t("ru", "about")
    assert t("ru", "btn.register") in labels(reply)


def test_unknown_text_returns_menu(logic):
    logic.handle_text(1, UZ)
    reply = logic.handle_text(1, "nimadir")
    assert reply.text == t("uz", "use_menu")
    assert t("uz", "btn.register") in labels(reply)


def test_settings_language_change_flow(logic):
    logic.handle_text(1, UZ)
    settings = logic.handle_text(1, t("uz", "btn.settings"))
    assert labels(settings) == [t("uz", "btn.language"), t("uz", "btn.back")]
    assert logic.handle_text(1, t("uz", "btn.language")).keyboard == LANGUAGE_KEYBOARD
    changed = logic.handle_text(1, RU)
    assert changed.text == t("ru", "language_saved")
    assert t("ru", "btn.register") in labels(changed)


def test_back_returns_to_panel(logic):
    logic.handle_text(1, UZ)
    reply = logic.handle_text(1, t("uz", "btn.back"))
    assert reply.text == t("uz", "about")


def test_unfinished_sections_say_coming_soon(logic):
    logic.handle_text(1, UZ)
    reply = logic.handle_text(1, t("uz", "btn.register"))
    assert reply.text == t("uz", "coming_soon")


def test_guest_cannot_use_consumer_buttons(logic):
    logic.handle_text(1, UZ)
    reply = logic.handle_text(1, t("uz", "btn.send_reading"))
    assert reply.text == t("uz", "use_menu")


def test_admin_without_language_is_asked_then_gets_admin_panel(logic, db_path):
    UserRepository(db_path).set_role(42, "admin")
    assert logic.start(42).keyboard == LANGUAGE_KEYBOARD
    reply = logic.handle_text(42, UZ)
    assert reply.text == t("uz", "panel.admin")
    assert labels(reply) == [t("uz", "btn.settings")]


def test_consumer_with_approved_link_gets_consumer_panel(logic, db_path):
    logic.handle_text(9, UZ)
    with connect(db_path) as db:
        db.execute(
            "insert into account_links (telegram_id, account, status) "
            "values (9, '100001', 'approved')"
        )
    reply = logic.start(9)
    assert reply.text == t("uz", "panel.consumer")
    assert labels(reply)[0] == t("uz", "btn.send_reading")
