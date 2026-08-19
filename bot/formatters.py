from typing import TYPE_CHECKING, Any

from bot.masking import mask_account, mask_address, mask_name, mask_phone
from bot.texts import TEXTS

if TYPE_CHECKING:
    from bot.excel_loader import Abonent
else:
    Abonent = Any


LABELS = {
    "uz": {
        "cabinet": "👤 Shaxsiy kabinet",
        "account": "🔢 Hisob raqami",
        "fio": "👨‍💼 F.I.O",
        "phone": "📞 Telefon",
        "program_phone": "📱 Dasturdagi telefon",
        "address": "🏠 Manzil",
        "area": "🧭 Hudud",
        "inspector": "👮 Inspektor",
        "inspector_phone": "📱 Inspektor tel",
        "balance": "💰 Balans",
        "debit": "🔴 Debitor qarzdorlik",
        "credit": "🟢 Oldindan to'lov",
        "excel_date": "📅 Excel ma'lumotlari sanasi",
        "meter_title": "📸 Hisoblagich ko'rsatkichini yuborish",
        "has_meter": "🚰 Hisoblagich mavjudligi",
        "last_meter": "🧾 Oxirgi ko'rsatkich",
        "last_meter_date": "📅 Kiritilgan sana",
        "caption_title": "📌 Abonent ma'lumotlari",
        "vacant": "Vakant",
    },
    "uz_cyrl": {
        "cabinet": "👤 Шахсий кабинет",
        "account": "🔢 Ҳисоб рақами",
        "fio": "👨‍💼 Ф.И.О",
        "phone": "📞 Телефон",
        "program_phone": "📱 Дастурдаги телефон",
        "address": "🏠 Манзил",
        "area": "🧭 Ҳудуд",
        "inspector": "👮 Инспектор",
        "inspector_phone": "📱 Инспектор тел",
        "balance": "💰 Баланс",
        "debit": "🔴 Дебитор қарздорлик",
        "credit": "🟢 Олдиндан тўлов",
        "excel_date": "📅 Excel маълумотлари санаси",
        "meter_title": "📸 Ҳисоблагич кўрсаткичини юбориш",
        "has_meter": "🚰 Ҳисоблагич мавжудлиги",
        "last_meter": "🧾 Охирги кўрсаткич",
        "last_meter_date": "📅 Киритилган сана",
        "caption_title": "📌 Абонент маълумотлари",
        "vacant": "Вакант",
    },
    "ru": {
        "cabinet": "👤 Личный кабинет",
        "account": "🔢 Лицевой счёт",
        "fio": "👨‍💼 Ф.И.О",
        "phone": "📞 Телефон",
        "program_phone": "📱 Телефон в программе",
        "address": "🏠 Адрес",
        "area": "🧭 Участок",
        "inspector": "👮 Инспектор",
        "inspector_phone": "📱 Тел. инспектора",
        "balance": "💰 Баланс",
        "debit": "🔴 Дебиторская задолженность",
        "credit": "🟢 Предоплата",
        "excel_date": "📅 Дата данных Excel",
        "meter_title": "📸 Отправить показание счетчика",
        "has_meter": "🚰 Наличие счетчика",
        "last_meter": "🧾 Последнее показание",
        "last_meter_date": "📅 Дата внесения",
        "caption_title": "📌 Данные абонента",
        "vacant": "Вакантно",
    },
}


def labels(language: str) -> dict[str, str]:
    return LABELS.get(language, LABELS["uz"])


def inspector_line(abonent: Abonent, language: str) -> str:
    text = TEXTS[language]
    label = labels(language)
    if abonent.inspector_fio:
        phone = f"\n{label['inspector_phone']}: {abonent.inspector_phone}" if abonent.inspector_phone else ""
        return f"{abonent.inspector_fio}{phone}"
    return text["vacant"]


def cabinet_text(abonent: Abonent, language: str, stored_phone: str = "") -> str:
    label = labels(language)
    phone = stored_phone or abonent.phone or "-"
    original_phone = (
        f"\n{label['program_phone']}: {mask_phone(abonent.original_phone)}"
        if abonent.edited_phone and abonent.original_phone
        else ""
    )
    return (
        f"{label['cabinet']}\n\n"
        f"{label['account']}: {mask_account(abonent.account)}\n"
        f"{label['fio']}: {mask_name(abonent.fio)}\n"
        f"{label['phone']}: {mask_phone(phone)}{original_phone}\n"
        f"{label['address']}: {mask_address(abonent.address)}\n"
        f"{label['area']}: {abonent.area or '-'}\n"
        f"{label['inspector']}: {inspector_line(abonent, language)}\n\n"
        f"ℹ️ {TEXTS[language]['no_phone']}"
    )


def balance_text(abonent: Abonent, language: str, loaded_at: str) -> str:
    label = labels(language)
    loaded = abonent.updated_at or loaded_at
    return (
        f"{label['balance']}\n\n"
        f"{label['account']}: {mask_account(abonent.account)}\n"
        f"{label['fio']}: {mask_name(abonent.fio)}\n"
        f"{label['debit']}: {abonent.debit or '0'}\n"
        f"{label['credit']}: {abonent.credit or '0'}\n"
        f"{label['excel_date']}: {loaded}\n\n"
        f"ℹ️ {TEXTS[language]['balance_note']}"
    )


def meter_intro_text(abonent: Abonent, language: str) -> str:
    label = labels(language)
    value = abonent.last_meter_value or "-"
    date = abonent.last_meter_date or "-"
    return (
        f"{label['meter_title']}\n\n"
        f"{label['account']}: {mask_account(abonent.account)}\n"
        f"{label['has_meter']}: {abonent.has_meter or '-'}\n"
        f"{label['last_meter']}: {value}\n"
        f"{label['last_meter_date']}: {date}\n\n"
        f"{TEXTS[language]['send_photo']}"
    )


def report_caption(
    abonent: Abonent,
    stored_phone: str = "",
    language: str = "uz",
    *,
    masked: bool = True,
) -> str:
    label = labels(language)
    phone = stored_phone or abonent.phone or "-"
    inspector = abonent.inspector_fio or label["vacant"]
    account = mask_account(abonent.account) if masked else (abonent.account or "-")
    fio = mask_name(abonent.fio) if masked else (abonent.fio or "-")
    shown_phone = mask_phone(phone) if masked else phone
    return (
        f"{label['caption_title']}\n\n"
        f"{label['account']}: {account}\n"
        f"{label['fio']}: {fio}\n"
        f"{label['phone']}: {shown_phone}\n"
        f"{label['area']}: {abonent.area or '-'}\n"
        f"{label['inspector']}: {inspector}"
    )
