from __future__ import annotations

import base64
import json
import os
import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


MAGIC = b"UZWATER1"
VERSION = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
MIN_PASSWORD_LENGTH = 16
MAX_HEADER_SIZE = 16 * 1024


class EncryptionError(RuntimeError):
    pass


class InvalidPasswordOrData(EncryptionError):
    pass


@dataclass(frozen=True)
class EncryptedFileInfo:
    version: int
    label: str
    original_name: str
    plaintext_size: int


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise EncryptionError(
            f"Shifrlash paroli kamida {MIN_PASSWORD_LENGTH} belgidan iborat bo'lishi kerak."
        )
    if password.isspace():
        raise EncryptionError("Shifrlash paroli faqat bo'sh joylardan iborat bo'lmasin.")


def _derive_key(password: str, salt: bytes) -> bytes:
    validate_password(password)
    return Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=2**17,
        r=8,
        p=1,
    ).derive(password.encode("utf-8"))


def _header_bytes(
    *,
    salt: bytes,
    nonce: bytes,
    label: str,
    original_name: str,
    plaintext_size: int,
) -> bytes:
    header = {
        "version": VERSION,
        "cipher": "AES-256-GCM",
        "kdf": "scrypt-n131072-r8-p1",
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "label": label,
        "original_name": original_name,
        "plaintext_size": plaintext_size,
    }
    return json.dumps(
        header,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def encrypt_bytes(
    plaintext: bytes,
    password: str,
    *,
    label: str,
    original_name: str = "",
) -> bytes:
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    header = _header_bytes(
        salt=salt,
        nonce=nonce,
        label=label,
        original_name=original_name,
        plaintext_size=len(plaintext),
    )
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, MAGIC + header)
    return MAGIC + struct.pack(">I", len(header)) + header + ciphertext


def _parse_payload(payload: bytes) -> tuple[dict[str, object], bytes, bytes]:
    minimum_size = len(MAGIC) + 4 + 16
    if len(payload) < minimum_size or not payload.startswith(MAGIC):
        raise EncryptionError("Fayl UZWATER shifrlangan formatida emas.")

    header_size = struct.unpack(
        ">I",
        payload[len(MAGIC) : len(MAGIC) + 4],
    )[0]
    if header_size < 2 or header_size > MAX_HEADER_SIZE:
        raise EncryptionError("Shifrlangan fayl sarlavhasi noto'g'ri.")

    header_start = len(MAGIC) + 4
    header_end = header_start + header_size
    if header_end >= len(payload):
        raise EncryptionError("Shifrlangan fayl to'liq emas.")
    header_bytes = payload[header_start:header_end]
    try:
        header = json.loads(header_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EncryptionError("Shifrlangan fayl sarlavhasi o'qilmadi.") from error
    if int(header.get("version") or 0) != VERSION:
        raise EncryptionError("Shifrlangan fayl versiyasi qo'llab-quvvatlanmaydi.")
    return header, header_bytes, payload[header_end:]


def decrypt_bytes(payload: bytes, password: str) -> tuple[bytes, EncryptedFileInfo]:
    header, header_bytes, ciphertext = _parse_payload(payload)
    try:
        salt = base64.b64decode(str(header["salt"]), validate=True)
        nonce = base64.b64decode(str(header["nonce"]), validate=True)
    except (KeyError, ValueError) as error:
        raise EncryptionError("Salt yoki nonce ma'lumoti noto'g'ri.") from error
    if len(salt) != SALT_SIZE or len(nonce) != NONCE_SIZE:
        raise EncryptionError("Salt yoki nonce uzunligi noto'g'ri.")

    key = _derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(
            nonce,
            ciphertext,
            MAGIC + header_bytes,
        )
    except InvalidTag as error:
        raise InvalidPasswordOrData(
            "Parol noto'g'ri yoki shifrlangan ma'lumot o'zgartirilgan."
        ) from error

    expected_size = int(header.get("plaintext_size") or -1)
    if len(plaintext) != expected_size:
        raise EncryptionError("Ochilgan ma'lumot hajmi sarlavhaga mos emas.")
    info = EncryptedFileInfo(
        version=VERSION,
        label=str(header.get("label") or ""),
        original_name=str(header.get("original_name") or ""),
        plaintext_size=expected_size,
    )
    return plaintext, info


def encrypt_file(
    source: str | Path,
    target: str | Path,
    password: str,
    *,
    label: str,
) -> EncryptedFileInfo:
    source_path = Path(source)
    target_path = Path(target)
    plaintext = source_path.read_bytes()
    encrypted = encrypt_bytes(
        plaintext,
        password,
        label=label,
        original_name=source_path.name,
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = target_path.with_name(f".{target_path.name}.tmp")
    try:
        temporary.write_bytes(encrypted)
        temporary.replace(target_path)
    finally:
        temporary.unlink(missing_ok=True)
    return EncryptedFileInfo(VERSION, label, source_path.name, len(plaintext))


def decrypt_file(
    source: str | Path,
    target: str | Path,
    password: str,
    *,
    expected_label: str | None = None,
) -> EncryptedFileInfo:
    source_path = Path(source)
    target_path = Path(target)
    plaintext, info = decrypt_bytes(source_path.read_bytes(), password)
    if expected_label is not None and info.label != expected_label:
        raise EncryptionError(
            f"Fayl turi mos emas: {info.label!r}, kutilgan: {expected_label!r}."
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = target_path.with_name(f".{target_path.name}.tmp")
    try:
        temporary.write_bytes(plaintext)
        temporary.replace(target_path)
    finally:
        temporary.unlink(missing_ok=True)
    return info


def encrypted_file_info(path: str | Path) -> EncryptedFileInfo:
    header, _, _ = _parse_payload(Path(path).read_bytes())
    return EncryptedFileInfo(
        version=int(header["version"]),
        label=str(header.get("label") or ""),
        original_name=str(header.get("original_name") or ""),
        plaintext_size=int(header.get("plaintext_size") or 0),
    )
