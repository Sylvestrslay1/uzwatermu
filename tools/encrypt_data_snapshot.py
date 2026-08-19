from __future__ import annotations

import argparse
import getpass
import hashlib
import json
from datetime import datetime
from pathlib import Path

from bot.encryption import encrypt_file, validate_password


DEFAULT_SOURCES = ("data", "storage", "backups", "outputs", "logs")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(
    sources: list[Path],
    destination: Path,
    password: str,
) -> Path:
    validate_password(password)
    destination.mkdir(parents=True, exist_ok=False)
    manifest_files: list[dict[str, object]] = []
    for source_root in sources:
        if not source_root.exists():
            continue
        for source in source_root.rglob("*"):
            if not source.is_file() or source.suffix == ".uwenc":
                continue
            relative = Path(source_root.name) / source.relative_to(source_root)
            target = destination / relative.parent / f"{relative.name}.uwenc"
            info = encrypt_file(
                source,
                target,
                password,
                label=f"snapshot:{source_root.name}",
            )
            manifest_files.append(
                {
                    "source": str(relative),
                    "encrypted": str(target.relative_to(destination)),
                    "plaintext_size": info.plaintext_size,
                    "encrypted_size": target.stat().st_size,
                    "sha256": sha256(target),
                }
            )

    manifest = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "cipher": "AES-256-GCM",
        "kdf": "scrypt-n32768-r8-p1",
        "files": manifest_files,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UZWATER ma'lumotlarining AES-256-GCM snapshotini yaratadi."
    )
    parser.add_argument(
        "--destination",
        default="encrypted_vault",
        help="Shifrlangan snapshotlar asosiy papkasi.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Manba papka. Bir necha marta berish mumkin.",
    )
    args = parser.parse_args()

    password = getpass.getpass("Yangi shifrlash paroli: ")
    confirmation = getpass.getpass("Parolni qayta kiriting: ")
    if password != confirmation:
        raise SystemExit("Parollar mos emas.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = Path(args.destination) / timestamp
    source_names = args.sources or list(DEFAULT_SOURCES)
    result = snapshot(
        [Path(name) for name in source_names],
        destination,
        password,
    )
    print(f"Shifrlangan snapshot yaratildi: {result}")
    print("Ochiq manba fayllari o'chirilmadi.")


if __name__ == "__main__":
    main()
