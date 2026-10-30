import pytest

from uzwatermu.db.migrate import migrate


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "bot.sqlite3"
    migrate(path)
    return path
