from __future__ import annotations

import re
import tkinter as tk
from tkinter import messagebox

from bot.secret_store import save_secret


TOKEN_PATTERN = re.compile(r"^\d{6,15}:[A-Za-z0-9_-]{20,}$")


def normalize_token(value: str) -> str:
    token = value.strip().strip("`'\"")
    prefixes = ("HTTP API:", "Token:", "BOT_TOKEN=")
    for prefix in prefixes:
        if token.lower().startswith(prefix.lower()):
            token = token[len(prefix) :].strip()
    return token


def main() -> None:
    root = tk.Tk()
    root.title("UZWATER Telegram tokenini yangilash")
    root.geometry("560x230")
    root.resizable(False, False)

    tk.Label(
        root,
        text="BotFather bergan yangi tokenni kiriting",
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=(20, 10))

    first = tk.Entry(root, show="*", width=65, font=("Consolas", 10))
    first.pack(pady=5)
    tk.Label(root, text="Tokenni qayta kiriting").pack(pady=(8, 0))
    second = tk.Entry(root, show="*", width=65, font=("Consolas", 10))
    second.pack(pady=5)

    def save() -> None:
        token = normalize_token(first.get())
        confirmation = normalize_token(second.get())
        if token != confirmation:
            messagebox.showerror("Xato", "Kiritilgan tokenlar mos emas.")
            return
        if not TOKEN_PATTERN.fullmatch(token):
            messagebox.showerror(
                "Xato",
                "Token formati noto'g'ri. BotFather xabaridan faqat "
                "raqamlar:harflar ko'rinishidagi tokenni nusxalang.",
            )
            return
        save_secret("bot_token", token)
        messagebox.showinfo(
            "Tayyor",
            "Telegram tokeni DPAPI omborida yangilandi.",
        )
        root.destroy()

    tk.Button(
        root,
        text="Xavfsiz saqlash",
        command=save,
        width=22,
        font=("Segoe UI", 10),
    ).pack(pady=18)
    first.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
