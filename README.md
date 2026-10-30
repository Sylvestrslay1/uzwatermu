# uzwatermu v2

Mirzo Ulug'bek tumani abonentlari uchun hisoblagich ko'rsatkichlarini qabul qiluvchi
Telegram bot — qayta loyihalangan versiya.

**Avval o'qing:** `docs/01_REJA_VA_SPETSIFIKATSIYA.md` (reja, arxitektura, xavfsizlik)
va `docs/02_V1_DAN_KOCHIRISH_XARITASI.md` (v1 kodining qaysi qismi qayerga boradi).

## Ishni boshlash (Windows)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env      # keyin .env ni to'ldiring (TEST bot tokeni bilan!)
python -m uzwatermu migrate      # var\db\bot.sqlite3 yaratiladi
pytest -q                        # testlar
ruff check .                     # kod sifati
python -m uzwatermu run          # bot
```

## Tuzilma

```text
src/uzwatermu/
  config.py            .env -> tekshirilgan sozlamalar, barcha yo'llar DATA_DIR ichida
  logging_setup.py     log + tokenlarni yashirish filtri
  db/                  ulanish, migratsiya, migrations/*.sql
  repositories/        barcha SQL shu yerda
  services/            biznes-qoidalar (Telegram'siz, testlanadi)
  security/            maskalash, rate limit, XLSX tekshiruvi, rol tekshiruvi
  telegram/            bot, klaviaturalar, handlers/ (faqat UI)
  locales/             uz / uz_cyrl / ru matnlari
  modules/             ixtiyoriy modullar (keyinroq)
scripts/               backup va boshqa CLI vositalar
deploy/                Windows (NSSM) va Linux (systemd) o'rnatish
tests/
```

## Qoidalar

- Handler ichida SQL yozilmaydi — faqat repository orqali.
- Sxema o'zgarishi = yangi `db/migrations/000N_nom.sql` fayli. Eski migratsiya o'zgartirilmaydi.
- Har bir yangi xulq-atvor — test bilan.
- Ishlab chiqish faqat **test bot tokeni** bilan; production tokeni faqat serverdagi `.env` da.
