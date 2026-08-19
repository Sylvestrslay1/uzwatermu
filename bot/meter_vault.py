from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from bot.encryption import decrypt_bytes, encrypt_bytes


METER_PHOTO_LABEL = "meter-photo"


class MeterPhotoIntegrityError(RuntimeError):
    pass


def store_meter_photo(
    payload: bytes,
    password: str,
    *,
    root: str | Path = "encrypted_vault/meter_photos",
) -> tuple[str, str]:
    digest = hashlib.sha256(payload).hexdigest()
    root_path = Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    target = root_path / f"{uuid4().hex}.uwenc"
    encrypted = encrypt_bytes(
        payload,
        password,
        label=METER_PHOTO_LABEL,
        original_name=f"{digest[:16]}.jpg",
    )
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_bytes(encrypted)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return str(target), digest


def load_meter_photo(path: str | Path, password: str, expected_sha256: str) -> bytes:
    root = Path("encrypted_vault/meter_photos").resolve()
    source = Path(path).resolve()
    if root != source.parent:
        raise MeterPhotoIntegrityError("Rasm yo'li himoyalangan ombordan tashqarida.")
    plaintext, info = decrypt_bytes(source.read_bytes(), password)
    if info.label != METER_PHOTO_LABEL:
        raise MeterPhotoIntegrityError("Shifrlangan fayl turi hisoblagich rasmi emas.")
    digest = hashlib.sha256(plaintext).hexdigest()
    if digest != expected_sha256:
        raise MeterPhotoIntegrityError("Rasmning SHA-256 nazorat summasi mos emas.")
    return plaintext


def remove_meter_photo(path: str | Path) -> None:
    root = Path("encrypted_vault/meter_photos").resolve()
    target = Path(path).resolve()
    if target.parent == root:
        target.unlink(missing_ok=True)
