from uzwatermu.db.connection import connect
from uzwatermu.repositories.audit import AuditRepository
from uzwatermu.repositories.users import UserRepository
from uzwatermu.services.roles import Panel, ensure_main_admin, panel_for


def test_panel_for():
    assert panel_for(None, False) == Panel.GUEST
    assert panel_for({"role": "user", "revoked_at": None}, False) == Panel.GUEST
    assert panel_for({"role": "user", "revoked_at": None}, True) == Panel.CONSUMER
    assert panel_for({"role": "operator", "revoked_at": None}, False) == Panel.OPERATOR
    assert panel_for({"role": "inspector", "revoked_at": None}, True) == Panel.INSPECTOR
    assert panel_for({"role": "admin", "revoked_at": None}, False) == Panel.ADMIN


def test_revoked_staff_gets_no_staff_panel():
    assert panel_for({"role": "admin", "revoked_at": "2026-11-01"}, False) == Panel.GUEST


def _audit_count(db_path):
    with connect(db_path) as db:
        return db.execute(
            "select count(*) from audit_log where action = 'main_admin_granted'"
        ).fetchone()[0]


def test_main_admin_granted_once(db_path):
    users, audit = UserRepository(db_path), AuditRepository(db_path)
    assert ensure_main_admin(users, audit, 42)
    assert users.get(42)["role"] == "admin"
    assert not ensure_main_admin(users, audit, 42)
    assert _audit_count(db_path) == 1


def test_revoked_main_admin_not_restored(db_path):
    users, audit = UserRepository(db_path), AuditRepository(db_path)
    with connect(db_path) as db:
        db.execute(
            "insert into users (telegram_id, role, revoked_at) values (42, 'user', '2026-11-01')"
        )
    assert not ensure_main_admin(users, audit, 42)
    assert users.get(42)["role"] == "user"
