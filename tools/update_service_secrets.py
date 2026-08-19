from __future__ import annotations

import argparse
import getpass

from bot.secret_store import save_secret


SECRET_NAMES = {
    "bot-token": "bot_token",
    "openai-key": "openai_api_key",
}


def validate_value(kind: str, value: str) -> None:
    if not value or value.isspace():
        raise SystemExit("Maxfiy qiymat bo'sh bo'lmasin.")
    if kind == "bot-token" and (":" not in value or len(value) < 30):
        raise SystemExit("Telegram bot tokeni formati noto'g'ri ko'rinadi.")
    if kind == "openai-key" and not value.startswith("sk-"):
        raise SystemExit("OpenAI API kaliti formati noto'g'ri ko'rinadi.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Xizmat kalitini Windows DPAPI omborida xavfsiz yangilaydi."
    )
    parser.add_argument("kind", choices=sorted(SECRET_NAMES))
    args = parser.parse_args()

    value = getpass.getpass("Yangi maxfiy qiymatni kiriting: ").strip()
    confirmation = getpass.getpass("Qayta kiriting: ").strip()
    if value != confirmation:
        raise SystemExit("Kiritilgan qiymatlar mos emas.")
    validate_value(args.kind, value)
    path = save_secret(SECRET_NAMES[args.kind], value)
    print(f"DPAPI ombori yangilandi: {path}")
    print("Bot ishlayotgan bo'lsa, uni qayta ishga tushiring.")


if __name__ == "__main__":
    main()
