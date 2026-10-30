import pytest
from pydantic import ValidationError

from uzwatermu.config import Settings

TOKEN = "123456:" + "A" * 30


@pytest.fixture
def base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_TOKEN", TOKEN)
    monkeypatch.setenv("REPORT_CHANNEL_ID", "-100123")
    monkeypatch.setenv("MAIN_ADMIN_ID", "42")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return tmp_path


def test_defaults_and_paths(base_env, monkeypatch):
    monkeypatch.setenv("BACKUP_ADMIN_IDS", "")
    monkeypatch.setenv("MAIN_GROUP_ID", "")
    monkeypatch.setenv("IMPORT_DIR", "")
    settings = Settings(_env_file=None)
    assert settings.main_admin_id == 42
    assert settings.backup_admin_ids == set()
    assert settings.main_group_id is None
    root = base_env.resolve()
    assert settings.database_path == root / "db" / "bot.sqlite3"
    assert settings.resolved_import_dir == root / "import"


def test_backup_admins_csv_and_import_dir(base_env, monkeypatch, tmp_path_factory):
    import_dir = tmp_path_factory.mktemp("import")
    monkeypatch.setenv("BACKUP_ADMIN_IDS", "7, 8")
    monkeypatch.setenv("IMPORT_DIR", str(import_dir))
    settings = Settings(_env_file=None)
    assert settings.backup_admin_ids == {7, 8}
    assert settings.resolved_import_dir == import_dir.resolve()


def test_bad_token_rejected(base_env, monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "not-a-token")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_main_admin_required(base_env, monkeypatch):
    monkeypatch.delenv("MAIN_ADMIN_ID")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
