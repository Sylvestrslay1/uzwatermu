from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from bot.secret_store import save_secret


def normalize_key(value: str) -> str:
    key = value.strip().strip("`'\"")
    if key.startswith("OPENAI_API_KEY="):
        key = key.split("=", 1)[1].strip()
    return key


def main() -> None:
    root = tk.Tk()
    root.title("UZWATER OpenAI API kalitini yangilash")
    root.geometry("560x230")
    root.resizable(False, False)

    tk.Label(
        root,
        text="Yangi OpenAI API kalitini kiriting",
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=(20, 10))

    first = tk.Entry(root, show="*", width=65, font=("Consolas", 10))
    first.pack(pady=5)
    tk.Label(root, text="API kalitini qayta kiriting").pack(pady=(8, 0))
    second = tk.Entry(root, show="*", width=65, font=("Consolas", 10))
    second.pack(pady=5)

    def save() -> None:
        key = normalize_key(first.get())
        confirmation = normalize_key(second.get())
        if key != confirmation:
            messagebox.showerror("Xato", "Kiritilgan API kalitlari mos emas.")
            return
        if not key.startswith("sk-") or len(key) < 30:
            messagebox.showerror(
                "Xato",
                "API kaliti formati noto'g'ri. Faqat sk- bilan "
                "boshlanuvchi yangi kalitni nusxalang.",
            )
            return
        save_secret("openai_api_key", key)
        messagebox.showinfo(
            "Tayyor",
            "OpenAI API kaliti DPAPI omborida yangilandi.",
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
