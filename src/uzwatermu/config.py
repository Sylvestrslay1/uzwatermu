from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Faqat infratuzilma sozlamalari. Admin bot ichida o'zgartiradigan parametrlar
    (limitlar, chegaralar, vaqtlar) `settings` jadvalida saqlanadi."""

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    bot_token: str = Field(pattern=r"^\d{5,}:[A-Za-z0-9_-]{20,}$")
    report_channel_id: int
    main_group_id: int | None = None
    main_admin_id: int
    backup_admin_ids: Annotated[set[int], NoDecode] = set()
    emergency_phrase_hash: str | None = None
    data_dir: Path | None = None
    import_dir: Path | None = None

    @field_validator("backup_admin_ids", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return {part.strip() for part in value.split(",") if part.strip()}
        if isinstance(value, int):
            return {value}
        return value

    @field_validator(
        "main_group_id", "data_dir", "import_dir", "emergency_phrase_hash", mode="before"
    )
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @cached_property
    def var_dir(self) -> Path:
        base = self.data_dir if self.data_dir else PROJECT_ROOT / "var"
        return base.resolve()

    @property
    def database_path(self) -> Path:
        return self.var_dir / "db" / "bot.sqlite3"

    @property
    def backup_dir(self) -> Path:
        return self.var_dir / "backups"

    @property
    def log_dir(self) -> Path:
        return self.var_dir / "logs"

    @property
    def archive_dir(self) -> Path:
        return self.var_dir / "archive"

    @cached_property
    def resolved_import_dir(self) -> Path:
        return (self.import_dir if self.import_dir else self.var_dir / "import").resolve()

    def ensure_dirs(self) -> None:
        for path in (
            self.database_path.parent,
            self.backup_dir,
            self.log_dir,
            self.archive_dir,
            self.resolved_import_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
