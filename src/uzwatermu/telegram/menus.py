"""Har bir panel klaviaturasi — tugma kalitlari bilan. Matn foydalanuvchi tiliga qarab qo'yiladi."""

from uzwatermu.locales import LANGUAGE_BUTTONS
from uzwatermu.services.roles import Panel

PANEL_MENUS: dict[Panel, list[list[str]]] = {
    Panel.GUEST: [
        ["btn.register"],
        ["btn.help", "btn.settings", "btn.contact"],
    ],
    Panel.CONSUMER: [
        ["btn.send_reading"],
        ["btn.balance", "btn.my_accounts"],
        ["btn.area_inspector", "btn.contact"],
        ["btn.settings"],
    ],
    Panel.OPERATOR: [["btn.settings"]],
    Panel.INSPECTOR: [["btn.settings"]],
    Panel.ADMIN: [["btn.settings"]],
}

SETTINGS_MENU: list[list[str]] = [["btn.language"], ["btn.back"]]

LANGUAGE_KEYBOARD: tuple[tuple[str, ...], ...] = tuple((label,) for label in LANGUAGE_BUTTONS)


def menu_keys(panel: Panel) -> set[str]:
    return {key for row in PANEL_MENUS[panel] for key in row}
