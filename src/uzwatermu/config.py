from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    bot_token: str = Field(pattern=r"^\d{5,}:[A-Za-z0-9_-]{20,}$")
    report_channel_id: int
    bootstrap_admin_ids: Annotated[set[int], NoDecode] = Field(min_length=1)
    data_dir: Path | None = None
    enabled_modules: Annotated[set[str], NoDecode] = set()

    user_request_limit: int = 15
    staff_request_limit: int = 60
    request_window_seconds: float = 10
    flood_block_seconds: float = 60
    max_meter_photos: int = Field(default=10, ge=1)
    max_meter_photo_mb: float = Field(default=10, gt=0)
    max_excel_upload_mb: float = Field(default=25, gt=0)
    backup_keep_days: int = Field(default=30, ge=1)

    @field_validator("bootstrap_admin_ids", "enabled_modules", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return {part.strip() for part in value.split(",") if part.strip()}
        if isinstance(value, int):
            return {value}
        return value

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
    def import_dir(self) -> Path:
        return self.var_dir / "imports"

    def ensure_dirs(self) -> None:
        for path in (self.database_path.parent, self.backup_dir, self.log_dir, self.import_dir):
            path.mkdir(parents=True, exist_ok=True)
