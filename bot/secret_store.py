from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SECRETS_DIR = _PROJECT_ROOT / "secrets"
SECRET_FILE = _SECRETS_DIR / "encryption_password.dpapi"
ENTROPY = b"uzwatermu-encryption-password-v1"
CRYPTPROTECT_UI_FORBIDDEN = 0x1


class SecretStoreError(RuntimeError):
    pass


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _blob(data: bytes) -> tuple[DATA_BLOB, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    blob = DATA_BLOB(
        len(data),
        ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)),
    )
    return blob, buffer


def _windows_only() -> None:
    if os.name != "nt":
        raise SecretStoreError(
            "DPAPI faqat Windows tizimida ishlaydi. Linux serverda secret "
            "manager yoki systemd credentials ishlating."
        )


def protect_secret(secret: str) -> bytes:
    _windows_only()
    if not secret:
        raise SecretStoreError("Bo'sh maxfiy qiymatni saqlab bo'lmaydi.")
    input_blob, input_buffer = _blob(secret.encode("utf-8"))
    entropy_blob, entropy_buffer = _blob(ENTROPY)
    output_blob = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    success = crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        "UZWATER encryption password",
        ctypes.byref(entropy_blob),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    _ = input_buffer, entropy_buffer
    if not success:
        raise SecretStoreError(
            f"Windows DPAPI shifrlash xatosi: {ctypes.get_last_error()}"
        )
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(output_blob.pbData)


def unprotect_secret(payload: bytes) -> str:
    _windows_only()
    input_blob, input_buffer = _blob(payload)
    entropy_blob, entropy_buffer = _blob(ENTROPY)
    output_blob = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    success = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    _ = input_buffer, entropy_buffer
    if not success:
        raise SecretStoreError(
            "DPAPI maxfiy qiymatini ochib bo'lmadi. Bot boshqa Windows "
            "foydalanuvchisi ostida ishga tushirilgan bo'lishi mumkin."
        )
    try:
        return ctypes.string_at(
            output_blob.pbData,
            output_blob.cbData,
        ).decode("utf-8")
    finally:
        kernel32.LocalFree(output_blob.pbData)


def save_encryption_password(
    password: str,
    path: str | Path = SECRET_FILE,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_bytes(protect_secret(password))
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def load_encryption_password(
    path: str | Path = SECRET_FILE,
) -> str | None:
    target = Path(path)
    if not target.exists():
        return None
    return unprotect_secret(target.read_bytes())


def secret_path(name: str) -> Path:
    safe_name = "".join(
        character
        for character in name.lower()
        if character.isalnum() or character in {"_", "-"}
    )
    if not safe_name:
        raise SecretStoreError("Maxfiy qiymat nomi noto'g'ri.")
    return _SECRETS_DIR / f"{safe_name}.dpapi"


def save_secret(name: str, value: str) -> Path:
    return save_encryption_password(value, secret_path(name))


def load_secret(name: str) -> str | None:
    return load_encryption_password(secret_path(name))
