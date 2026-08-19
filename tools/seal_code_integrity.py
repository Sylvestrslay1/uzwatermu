from __future__ import annotations

import json
import secrets
from pathlib import Path

from bot.code_integrity import KEY_NAME, MANIFEST_PATH, build_manifest
from bot.secret_store import load_secret, save_secret


def main() -> int:
    key = load_secret(KEY_NAME)
    if not key:
        key = secrets.token_urlsafe(48)
        save_secret(KEY_NAME, key)
    manifest = build_manifest(key)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_name(f".{MANIFEST_PATH.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(MANIFEST_PATH)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Kod yaxlitligi muhrlandi: {len(manifest['files'])} fayl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
