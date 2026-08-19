from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values

from bot.encryption import encrypt_file
from bot.secret_store import load_encryption_password, save_secret


SECRET_KEYS = {
    "BOT_TOKEN": "bot_token",
    "OPENAI_API_KEY": "openai_api_key",
}


def migrate(path: Path = Path(".env")) -> list[str]:
    if not path.exists():
        raise RuntimeError(".env fayli topilmadi.")
    encryption_password = load_encryption_password()
    if not encryption_password:
        raise RuntimeError("Avval DPAPI shifrlash parolini yarating.")

    values = dotenv_values(path)
    migrated: list[str] = []
    for environment_name, secret_name in SECRET_KEYS.items():
        value = values.get(environment_name)
        if value:
            save_secret(secret_name, value)
            migrated.append(environment_name)

    if not migrated:
        return []

    encrypted_backup = Path("secrets/env_before_secret_migration.uwenc")
    encrypt_file(
        path,
        encrypted_backup,
        encryption_password,
        label="environment_backup",
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    filtered = [
        line
        for line in lines
        if not any(line.startswith(f"{name}=") for name in migrated)
    ]
    path.write_text("\n".join(filtered).rstrip() + "\n", encoding="utf-8")
    return migrated


def main() -> None:
    migrated = migrate()
    if migrated:
        print("DPAPI omboriga ko'chirildi: " + ", ".join(migrated))
        print(".env ichidagi ochiq qiymatlar olib tashlandi.")
    else:
        print("Ko'chiriladigan ochiq xizmat kaliti topilmadi.")


if __name__ == "__main__":
    main()
