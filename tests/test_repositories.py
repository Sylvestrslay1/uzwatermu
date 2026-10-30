from uzwatermu.db.connection import connect
from uzwatermu.repositories.account_links import AccountLinkRepository
from uzwatermu.repositories.settings import SettingsRepository
from uzwatermu.repositories.users import UserRepository


def test_user_language_and_role(db_path):
    users = UserRepository(db_path)
    assert users.get(1) is None
    users.set_language(1, "ru")
    users.set_role(1, "operator")
    user = users.get(1)
    assert user["language"] == "ru"
    assert user["role"] == "operator"


def test_role_only_user_has_no_language(db_path):
    users = UserRepository(db_path)
    users.set_role(5, "admin")
    assert users.get(5)["language"] is None


def test_has_approved_link(db_path):
    UserRepository(db_path).set_language(7, "uz")
    links = AccountLinkRepository(db_path)
    assert not links.has_approved(7)
    with connect(db_path) as db:
        db.execute(
            "insert into account_links (telegram_id, account, status) "
            "values (7, '100001', 'pending')"
        )
    assert not links.has_approved(7)
    with connect(db_path) as db:
        db.execute("update account_links set status = 'approved' where telegram_id = 7")
    assert links.has_approved(7)


def test_settings_roundtrip(db_path):
    repo = SettingsRepository(db_path)
    assert repo.get("kpi.thresholds", [60, 80]) == [60, 80]
    repo.set("kpi.thresholds", [65, 85], updated_by=1)
    assert repo.get("kpi.thresholds") == [65, 85]
    repo.set("contact.address", "Olimlar ko'chasi 51", updated_by=1)
    assert repo.get("contact.address") == "Olimlar ko'chasi 51"
