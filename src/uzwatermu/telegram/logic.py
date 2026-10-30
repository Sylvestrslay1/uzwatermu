"""Suhbat mantig'i: kim, qaysi panelda, qaysi tugma nima qiladi. Telegram'ni bilmaydi —
kirish (foydalanuvchi ID, matn) va chiqish (javob matni, klaviatura) oddiy qiymatlar."""

from __future__ import annotations

from dataclasses import dataclass

from uzwatermu.locales import BILINGUAL_GREETING, LANGUAGE_BUTTONS, button_key, t
from uzwatermu.repositories.account_links import AccountLinkRepository
from uzwatermu.repositories.users import UserRepository
from uzwatermu.services.roles import Panel, panel_for
from uzwatermu.telegram.menus import LANGUAGE_KEYBOARD, PANEL_MENUS, SETTINGS_MENU, menu_keys

Keyboard = tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Reply:
    text: str
    keyboard: Keyboard


def _render(rows: list[list[str]], language: str) -> Keyboard:
    return tuple(tuple(t(language, key) for key in row) for row in rows)


class BotLogic:
    def __init__(self, users: UserRepository, links: AccountLinkRepository) -> None:
        self.users = users
        self.links = links

    def panel(self, telegram_id: int) -> Panel:
        return panel_for(self.users.get(telegram_id), self.links.has_approved(telegram_id))

    def start(self, telegram_id: int) -> Reply:
        user = self.users.get(telegram_id)
        if not user or not user["language"]:
            return Reply(BILINGUAL_GREETING, LANGUAGE_KEYBOARD)
        return self._panel_reply(telegram_id, user["language"])

    def handle_text(self, telegram_id: int, text: str) -> Reply:
        user = self.users.get(telegram_id)

        chosen = LANGUAGE_BUTTONS.get(text)
        if chosen:
            first_time = not user or not user["language"]
            self.users.set_language(telegram_id, chosen)
            if first_time:
                return self._panel_reply(telegram_id, chosen)
            return self._panel_reply(telegram_id, chosen, t(chosen, "language_saved"))

        if not user or not user["language"]:
            return self.start(telegram_id)

        language = user["language"]
        panel = self.panel(telegram_id)
        key = button_key(text)

        if key == "btn.settings":
            return Reply(t(language, "settings_title"), _render(SETTINGS_MENU, language))
        if key == "btn.language":
            return Reply(t(language, "choose_language"), LANGUAGE_KEYBOARD)
        if key == "btn.back":
            return self._panel_reply(telegram_id, language)
        if key in menu_keys(panel):
            return Reply(t(language, "coming_soon"), _render(PANEL_MENUS[panel], language))
        return self._panel_reply(telegram_id, language, t(language, "use_menu"))

    def _panel_reply(self, telegram_id: int, language: str, text: str | None = None) -> Reply:
        panel = self.panel(telegram_id)
        if text is None:
            text = t(language, "about") if panel == Panel.GUEST else t(language, f"panel.{panel}")
        return Reply(text, _render(PANEL_MENUS[panel], language))
