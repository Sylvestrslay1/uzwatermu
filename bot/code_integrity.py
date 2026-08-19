from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

from bot.secret_store import load_secret


MANIFEST_PATH = Path("secrets/code_integrity_manifest.json")
KEY_NAME = "code_integrity_key"
MANIFEST_VERSION = 1


class CodeIntegrityError(RuntimeError):
    pass


def protected_files(root: str | Path = ".") -> list[Path]:
    base = Path(root).resolve()
    files = []
    for folder in ("bot", "tools"):
        for pattern in ("*.py", "*.ps1"):
            files.extend(
                path
                for path in (base / folder).rglob(pattern)
                if "__pycache__" not in path.parts
            )
    files.extend(
        path
        for path in (base / "requirements.txt", base / ".env.example")
        if path.exists()
    )
    return sorted(files, key=lambda path: path.relative_to(base).as_posix())


def file_hashes(root: str | Path = ".") -> dict[str, str]:
    base = Path(root).resolve()
    return {
        path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in protected_files(base)
    }


def _payload(files: dict[str, str]) -> bytes:
    return json.dumps(
        {"version": MANIFEST_VERSION, "files": files},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def build_manifest(key: str, root: str | Path = ".") -> dict[str, object]:
    files = file_hashes(root)
    signature = hmac.new(
        key.encode("utf-8"),
        _payload(files),
        hashlib.sha256,
    ).hexdigest()
    return {
        "version": MANIFEST_VERSION,
        "algorithm": "HMAC-SHA256",
        "files": files,
        "signature": signature,
    }


def verify_code_integrity(
    root: str | Path = ".",
    manifest_path: str | Path = MANIFEST_PATH,
) -> None:
    key = load_secret(KEY_NAME)
    if not key:
        raise CodeIntegrityError("Kod yaxlitligi uchun DPAPI kalit topilmadi.")
    path = Path(manifest_path)
    if not path.exists():
        raise CodeIntegrityError("Kod yaxlitligi manifesti topilmadi.")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CodeIntegrityError("Kod yaxlitligi manifesti o'qilmadi.") from error
    if (
        int(manifest.get("version") or 0) != MANIFEST_VERSION
        or manifest.get("algorithm") != "HMAC-SHA256"
        or not isinstance(manifest.get("files"), dict)
    ):
        raise CodeIntegrityError("Kod yaxlitligi manifesti formati noto'g'ri.")

    expected_files = {
        str(name): str(digest)
        for name, digest in manifest["files"].items()
    }
    expected_signature = hmac.new(
        key.encode("utf-8"),
        _payload(expected_files),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(
        str(manifest.get("signature") or ""),
        expected_signature,
    ):
        raise CodeIntegrityError("Kod yaxlitligi manifesti imzosi buzilgan.")

    current_files = file_hashes(root)
    if current_files != expected_files:
        changed = sorted(
            set(current_files) ^ set(expected_files)
            | {
                name
                for name in set(current_files) & set(expected_files)
                if current_files[name] != expected_files[name]
            }
        )
        sample = ", ".join(changed[:8])
        raise CodeIntegrityError(
            f"Ruxsatsiz yoki muhrlanmagan kod o'zgarishi aniqlandi: {sample}"
        )
