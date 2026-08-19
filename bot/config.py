from dataclasses import dataclass
from os import getenv
import re

from dotenv import dotenv_values, load_dotenv

from bot.secret_store import load_encryption_password, load_secret


@dataclass(frozen=True)
class Config:
    bot_token: str
    report_channel_id: int | None
    admin_ids: set[int]
    excel_file: str
    inspectors_file: str
    database_file: str
    contact_phones: str
    district_address: str
    district_lat: float | None
    district_lon: float | None
    backup_dir: str
    backup_interval_hours: float
    backup_retention_days: int
    backup_keep_sets: int
    encryption_enabled: bool
    encryption_password: str | None
    health_check_interval_hours: float
    backup_maximum_age_hours: float
    minimum_disk_free_gb: float
    minimum_disk_free_percent: float
    request_window_seconds: float
    user_request_limit: int
    staff_request_limit: int
    flood_block_seconds: float
    max_excel_upload_mb: float
    max_meter_photo_mb: float
    max_meter_photos: int
    bulk_send_delay: float
    error_channel_id: int | None
    location_channel_id: str | None
    health_port: int | None


def _optional_int(value: str | None) -> int | None:
    if not value:
        return None
    return int(value)


def _optional_float(value: str | None) -> float | None:
    if not value:
        return None
    return float(value)


def _admin_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    return {int(part.strip()) for part in value.split(",") if part.strip()}


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_config(config: Config) -> Config:
    if not re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{20,}", config.bot_token):
        raise RuntimeError(
            "BOT_TOKEN formati noto'g'ri. BotFather bergan tokenni "
            "to'liq kiriting."
        )
    if not config.admin_ids:
        raise RuntimeError(
            "ADMIN_IDS bo'sh. Kamida bitta super admin Telegram ID "
            "raqamini kiriting."
        )
    if config.report_channel_id is None:
        raise RuntimeError(
            "REPORT_CHANNEL_ID ko'rsatilmagan. Hisoblagich rasmlari "
            "yo'qolmasligi uchun hisobot kanalini sozlang."
        )
    if not config.encryption_enabled or not config.encryption_password:
        raise RuntimeError(
            "Production rejimida ENCRYPTION_ENABLED=true va DPAPI "
            "shifrlash kaliti majburiy."
        )
    if config.max_meter_photos < 1:
        raise RuntimeError("MAX_METER_PHOTOS kamida 1 bo'lishi kerak.")
    if config.max_excel_upload_mb <= 0 or config.max_meter_photo_mb <= 0:
        raise RuntimeError("Fayl hajmi limitlari 0 dan katta bo'lishi kerak.")
    return config


def load_config() -> Config:
    dotenv_data = dotenv_values()
    if dotenv_data.get("UZWATER_ENCRYPTION_PASSWORD"):
        raise RuntimeError(
            "UZWATER_ENCRYPTION_PASSWORD ni .env ichida saqlash taqiqlangan. "
            "Uni server yoki PyCharm environment variable orqali bering."
        )
    load_dotenv()
    token = load_secret("bot_token") or getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan")

    encryption_enabled = _bool(getenv("ENCRYPTION_ENABLED"))
    encryption_password = (
        getenv("UZWATER_ENCRYPTION_PASSWORD")
        or load_encryption_password()
    )
    if encryption_enabled and not encryption_password:
        raise RuntimeError(
            "ENCRYPTION_ENABLED=true, ammo DPAPI kalit ombori yaratilmagan. "
            "Avval tools/setup_encryption.py ni ishga tushiring."
        )

    return _validate_config(Config(
        bot_token=token,
        report_channel_id=_optional_int(getenv("REPORT_CHANNEL_ID")),
        admin_ids=_admin_ids(getenv("ADMIN_IDS")),
        excel_file=getenv("EXCEL_FILE", "data/abonents.xlsx"),
        inspectors_file=getenv("INSPECTORS_FILE", "data/inspectors.xlsx"),
        database_file=getenv("DATABASE_FILE", "storage/bot.sqlite3"),
        contact_phones=getenv("CONTACT_PHONES", "71-262-55-81"),
        district_address=getenv(
            "DISTRICT_ADDRESS",
            "Mirzo Ulug'bek tuman Abonentlar bo'limi manzili",
        ),
        district_lat=_optional_float(getenv("DISTRICT_LAT")),
        district_lon=_optional_float(getenv("DISTRICT_LON")),
        backup_dir=getenv("BACKUP_DIR", "backups"),
        backup_interval_hours=_optional_float(getenv("BACKUP_INTERVAL_HOURS")) or 24,
        backup_retention_days=int(getenv("BACKUP_RETENTION_DAYS", "30")),
        backup_keep_sets=int(getenv("BACKUP_KEEP_SETS", "30")),
        encryption_enabled=encryption_enabled,
        encryption_password=encryption_password,
        health_check_interval_hours=_optional_float(
            getenv("HEALTH_CHECK_INTERVAL_HOURS")
        )
        or 6,
        backup_maximum_age_hours=_optional_float(
            getenv("BACKUP_MAXIMUM_AGE_HOURS")
        )
        or 48,
        minimum_disk_free_gb=_optional_float(
            getenv("MINIMUM_DISK_FREE_GB")
        )
        or 2,
        minimum_disk_free_percent=_optional_float(
            getenv("MINIMUM_DISK_FREE_PERCENT")
        )
        or 5,
        request_window_seconds=_optional_float(
            getenv("REQUEST_WINDOW_SECONDS")
        )
        or 10,
        user_request_limit=int(getenv("USER_REQUEST_LIMIT", "15")),
        staff_request_limit=int(getenv("STAFF_REQUEST_LIMIT", "60")),
        flood_block_seconds=_optional_float(
            getenv("FLOOD_BLOCK_SECONDS")
        )
        or 60,
        max_excel_upload_mb=_optional_float(
            getenv("MAX_EXCEL_UPLOAD_MB")
        )
        or 25,
        max_meter_photo_mb=_optional_float(
            getenv("MAX_METER_PHOTO_MB")
        )
        or 10,
        max_meter_photos=int(getenv("MAX_METER_PHOTOS", "10")),
        bulk_send_delay=_optional_float(getenv("BULK_SEND_DELAY")) or 0.15,
        error_channel_id=_optional_int(getenv("ERROR_CHANNEL_ID")) or _optional_int(getenv("REPORT_CHANNEL_ID")),
        location_channel_id=getenv("LOCATION_CHANNEL_ID") or None,
        health_port=_optional_int(getenv("HEALTH_PORT")),
    ))
