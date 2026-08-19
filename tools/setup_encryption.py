from __future__ import annotations

import getpass
from pathlib import Path

from bot.encryption import validate_password
from bot.secret_store import save_encryption_password
from tools.encrypt_data_snapshot import DEFAULT_SOURCES, snapshot


def enable_dotenv_flag(path: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    updated: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("UZWATER_ENCRYPTION_PASSWORD="):
            continue
        if line.startswith("ENCRYPTION_ENABLED="):
            updated.append("ENCRYPTION_ENABLED=true")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append("ENCRYPTION_ENABLED=true")
    path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    print("UZWATER AES-256-GCM shifrlashni sozlash")
    print("Parol ekranda ko'rinmaydi va .env ichiga yozilmaydi.")
    password = getpass.getpass("Yangi kuchli parol: ")
    confirmation = getpass.getpass("Parolni qayta kiriting: ")
    if password != confirmation:
        raise SystemExit("Parollar mos emas.")
    validate_password(password)

    secret_path = save_encryption_password(password)
    enable_dotenv_flag(Path(".env"))

    destination = (
        Path("encrypted_vault")
        / __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    snapshot(
        [Path(name) for name in DEFAULT_SOURCES],
        destination,
        password,
    )
    print(f"DPAPI kalit ombori yaratildi: {secret_path}")
    print(f"AES-256 snapshot yaratildi: {destination}")
    print("ENCRYPTION_ENABLED=true qilindi.")
    print("Endi botni qayta ishga tushiring.")


if __name__ == "__main__":
    main()
