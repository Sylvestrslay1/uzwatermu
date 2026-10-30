from __future__ import annotations

import re
from typing import Any

EMPTY_VALUE = "-"


def _text(value: Any) -> str:
    return str(value or "").strip()


def mask_name(value: Any) -> str:
    """Keep a recognizable initial without exposing the full person's name."""
    parts = _text(value).split()
    if not parts:
        return EMPTY_VALUE

    masked: list[str] = []
    for index, part in enumerate(parts):
        visible_count = 2 if index == 1 and len(part) > 1 else 1
        masked.append(f"{part[:visible_count]}...")
    return " ".join(masked)


def mask_phone(value: Any) -> str:
    """Show the Uzbekistan operator code and only the final three digits."""
    digits = re.sub(r"\D", "", _text(value))
    if not digits:
        return EMPTY_VALUE

    if digits.startswith("998") and len(digits) >= 12:
        local = digits[3:12]
    elif len(digits) == 9:
        local = digits
    else:
        return f"***{digits[-3:]}" if len(digits) >= 3 else "***"

    return f"+998 {local[:2]} *** * {local[-3:]}"


def mask_account(value: Any) -> str:
    account = _text(value)
    if not account:
        return EMPTY_VALUE
    visible = account[-3:] if len(account) >= 3 else account[-1:]
    hidden_count = max(4, len(account) - len(visible))
    return f"{'*' * hidden_count}{visible}"


def mask_telegram_id(value: Any) -> str:
    telegram_id = _text(value)
    if not telegram_id:
        return EMPTY_VALUE
    visible = telegram_id[-3:] if len(telegram_id) >= 3 else telegram_id[-1:]
    return f"{'*' * max(5, len(telegram_id) - len(visible))}{visible}"


def mask_address(value: Any) -> str:
    """Preserve the area/street while hiding house and apartment identifiers."""
    address = _text(value)
    if not address:
        return EMPTY_VALUE

    patterns = [
        r"(?i)(\buy\s*[:.]?\s*)[\w/-]+",
        r"(?i)(\bxonadon\s*[:.]?\s*)[\w/-]+",
        r"(?i)(\bkvartira\s*[:.]?\s*)[\w/-]+",
        r"(?i)(\bдом\s*[:.]?\s*)[\w/-]+",
        r"(?i)(\bкв(?:артира)?\s*[:.]?\s*)[\w/-]+",
        r"\b\d+[\w/-]*(?=\s*-\s*(?:uy|xonadon)\b)",
    ]
    masked = address
    for pattern in patterns:
        replacement = r"\1**" if pattern.startswith("(?i)(") else "**"
        masked = re.sub(pattern, replacement, masked)
    return masked


def sanitize_audit_details(value: Any) -> str:
    """Mask common identifiers embedded in audit detail strings."""
    details = _text(value)
    if not details:
        return EMPTY_VALUE

    key_maskers = {
        "telegram_id": mask_telegram_id,
        "operator_id": mask_telegram_id,
        "inspector_id": mask_telegram_id,
        "actor_id": mask_telegram_id,
        "account": mask_account,
        "phone": mask_phone,
        "fio": mask_name,
    }
    for key, masker in key_maskers.items():
        pattern = re.compile(rf"(?i)(\b{re.escape(key)}\s*=\s*)([^;,\s]+(?:\s+[^;,]+)?)")
        details = pattern.sub(
            lambda match, m=masker: match.group(1) + m(match.group(2).strip()), details
        )
    return details


def masked_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return an export-safe copy; never mutate the database row."""
    result = dict(row)
    for key in ("telegram_id", "actor_id"):
        if key in result:
            result[key] = mask_telegram_id(result[key])
    if "account" in result:
        result["account"] = mask_account(result["account"])
    if "fio" in result:
        result["fio"] = mask_name(result["fio"])
    if "phone" in result:
        result["phone"] = mask_phone(result["phone"])
    if "address" in result:
        result["address"] = mask_address(result["address"])
    if "details" in result:
        result["details"] = sanitize_audit_details(result["details"])
    return result
