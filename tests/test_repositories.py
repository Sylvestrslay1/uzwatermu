from uzwatermu.repositories.abonents import AbonentRepository
from uzwatermu.repositories.users import UserRepository


def test_user_language_and_role(db_path):
    users = UserRepository(db_path)
    users.upsert_language(1, "ru")
    users.set_role(1, "admin")
    assert users.get(1)["language"] == "ru"
    assert users.role(1) == "admin"
    assert users.role(999) == "user"


def test_abonent_import(db_path):
    repo = AbonentRepository(db_path)
    assert repo.replace_all([{"account": "100001", "fio": "Test"}]) == 1
    assert repo.find("100001")["fio"] == "Test"
    assert repo.find("404") is None
