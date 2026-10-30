import pytest
from pydantic import ValidationError

from uzwatermu.config import Settings

TOKEN = "123456:" + "A" * 30


def test_csv_lists_are_parsed(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_TOKEN", TOKEN)
    monkeypatch.setenv("REPORT_CHANNEL_ID", "-100123")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_IDS", "1, 2")
    monkeypatch.setenv("ENABLED_MODULES", "")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings = Settings(_env_file=None)
    assert settings.bootstrap_admin_ids == {1, 2}
    assert settings.enabled_modules == set()
    assert settings.database_path == tmp_path.resolve() / "db" / "bot.sqlite3"


def test_bad_token_rejected(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "not-a-token")
    monkeypatch.setenv("REPORT_CHANNEL_ID", "-100123")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_IDS", "1")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
