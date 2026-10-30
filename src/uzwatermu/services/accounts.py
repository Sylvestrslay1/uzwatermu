"""Hisob raqam va telefon bo'yicha qoidalar. Telegram'ni bilmaydi — unit-test qilinadi."""

from __future__ import annotations

import re


def clean_account(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip() if ch.isdigit())


def normalize_uz_phone(value: str) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return digits
    return None


def phone_matches(abonent_phone: str, provided_phone: str) -> bool:
    expected = normalize_uz_phone(abonent_phone)
    actual = normalize_uz_phone(provided_phone)
    return bool(expected and actual and expected == actual)
