from __future__ import annotations

import logging
from enum import StrEnum

from uzwatermu.repositories.audit import AuditRepository
from uzwatermu.repositories.users import STAFF_ROLES, UserRepository

log = logging.getLogger(__name__)


class Panel(StrEnum):
    GUEST = "guest"
    CONSUMER = "consumer"
    OPERATOR = "operator"
    INSPECTOR = "inspector"
    ADMIN = "admin"


def panel_for(user: dict | None, has_approved_link: bool) -> Panel:
    if user and user.get("revoked_at") is None and user.get("role") in STAFF_ROLES:
        return Panel(user["role"])
    if has_approved_link:
        return Panel.CONSUMER
    return Panel.GUEST


def ensure_main_admin(users: UserRepository, audit: AuditRepository, main_admin_id: int) -> bool:
    """`.env` dagi asosiy adminga admin rolini beradi. Favqulodda bekor qilingan akkauntga
    qayta bermaydi — aks holda bot qayta ishga tushganda bekor qilish o'z kuchini yo'qotardi."""
    user = users.get(main_admin_id)
    if user and user["revoked_at"]:
        log.warning("MAIN_ADMIN_ID bekor qilingan akkauntga tegishli; admin roli berilmadi.")
        return False
    if user and user["role"] == "admin":
        return False
    users.set_role(main_admin_id, "admin")
    audit.write(None, "main_admin_granted", f"telegram_id={main_admin_id}")
    return True
