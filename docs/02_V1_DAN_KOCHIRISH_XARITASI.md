# v1 kodini qayta tashkil qilish xaritasi

v1 fayllarining har biri v2 da qayerga borishi (yoki ketishi). v1 kodidan nusxa
olayotganda shu jadvalga qarang — qayta ishlatsa bo'ladigan yaxshi qismlar ham bor.

## Belgilar

- **KO'CHIRISH** — mantiq yaxshi, ozgina moslab o'tkaziladi
- **QAYTA YOZISH** — g'oya kerak, lekin kod yangidan yoziladi
- **OLIB TASHLASH** — v2 da yo'q

## bot/

| v1 fayl | Qator | Qaror | v2 dagi joyi / izoh |
|---|---|---|---|
| `main.py` | 5462 | QAYTA YOZISH | Bo'linadi: `telegram/keyboards.py`, `telegram/handlers/{start,cabinet,meter,admin}.py`, `services/*`. Biznes-mantiqni handlerlardan ajrating |
| `config.py` | ~180 | QAYTA YOZISH | `config.py` — `pydantic-settings`. DPAPI va shifrlash parol mantig'i olib tashlanadi |
| `storage.py` | ~1500 | QAYTA YOZISH | `db/connection.py` + `db/migrate.py` + `repositories/*.py`. SQL so'rovlarining o'zini ko'chirsa bo'ladi; `_ensure_column` o'rniga migratsiyalar |
| `excel_loader.py` | 363 | QAYTA YOZISH | `services/importer.py` — qat'iy ustunlar, natija SQLite'ga. `clean_account` va `_format` funksiyalarini ko'chirsa bo'ladi |
| `states.py` | 51 | KO'CHIRISH | `telegram/states.py` (Enum ko'rinishida) |
| `buttons.py` | 70 | KO'CHIRISH | `locales/*` ichiga (tugma matnlari ham tarjima) |
| `texts.py` | ~600 | KO'CHIRISH | `locales/uz.py`, `uz_cyrl.py`, `ru.py` |
| `formatters.py` | 161 | KO'CHIRISH | `telegram/formatters.py` |
| `masking.py` | 119 | KO'CHIRISH | `security/masking.py` — deyarli o'zgarishsiz, testlari bilan |
| `rate_limit.py` | 99 | KO'CHIRISH | `security/rate_limit.py` — o'zgarishsiz |
| `security.py` | 64 | KO'CHIRISH | `security/admin_guard.py` ga birlashtiriladi |
| `security_hardening.py` | 103 | KO'CHIRISH (qisman) | `validate_safe_xlsx` → `security/xlsx_guard.py`; `redact_sensitive_text` → `logging_setup.py` filtri |
| `runtime.py` | 141 | QISMAN | `ProcessLock` saqlanadi; health.json va signal'lar servis menejerga qoladi |
| `health_checks.py` | 186 | QAYTA YOZISH | `db/migrate.py` dagi startup tekshiruvi (sxema versiyasi, baza bo'sh emasligi) |
| `backup_manager.py` | 365 | QAYTA YOZISH | `services/backup.py` — SQLite `.backup()`, retention. Shifrlash va botdan tiklash olib tashlanadi; tiklash `scripts/restore.py` |
| `debt_texts.py` | ~100 | KO'CHIRISH | `modules/debt/` (ixtiyoriy modul) |
| `encryption.py` | 225 | OLIB TASHLASH | Kerak bo'lsa keyin backup arxivi uchun qaytariladi |
| `meter_vault.py` | 61 | OLIB TASHLASH | Rasm faqat Telegram `file_id` sifatida |
| `secret_store.py` | 145 | OLIB TASHLASH | `.env` + fayl ruxsatlari |
| `code_integrity.py` | 120 | OLIB TASHLASH | |
| `image_matching.py` | 165 | OLIB TASHLASH | Takror rasmni SHA-256 bilan aniqlash yetarli |
| `table_reports.py` | ~930 | ALOHIDA | Botdan tashqari, `reports/` CLI (6-bosqichdan keyin) |
| `passport_report.py` | ~740 | ALOHIDA | shu |
| `f3_extract.py` | ~470 | ALOHIDA | shu |

## tools/

| v1 fayl | Qaror | Izoh |
|---|---|---|
| `bot_supervisor.py`, `windows_job.py` | OLIB TASHLASH | NSSM (Windows) / systemd (Linux) |
| `install_startup_task.ps1`, `uninstall_startup_task.ps1`, `start_bot_hidden.ps1` | OLIB TASHLASH | `deploy/windows/install_service.ps1` (NSSM, ~15 qator) |
| `harden_windows_acl.ps1` | QAYTA YOZISH | Deploy yo'riqnomasida bitta `icacls` buyrug'i |
| `uzwatermu.service` | KO'CHIRISH | `deploy/linux/uzwatermu.service` |
| `seal_code_integrity.py`, `migrate_env_secrets.py`, `setup_encryption.py`, `update_*_gui.py`, `update_service_secrets.py`, `encrypt_data_snapshot.py` | OLIB TASHLASH | |

## tests/

v1 da 27 ta test fayli bor. Quyidagilarni mos modullar bilan birga ko'chiring
(ichidagi test holatlari qimmatli):

- `test_masking.py`, `test_rate_limit.py`, `test_formatters_privacy.py`, `test_privacy_regression.py`
- `test_account_verification.py`, `test_user_binding.py`, `test_admin_security.py`
- `test_security_hardening.py` (faqat XLSX qismi)

Qolganlari olib tashlangan modullar bilan bog'liq yoki `main.py` matnini string sifatida
tekshiradi (masalan `source.index(...)`) — bunday testlar v2 da yozilmaydi; xulq-atvor
testlari yoziladi.

## v1 dagi tuzatilishi kerak bo'lgan aniq xatolar (v2 da takrorlanmasin)

1. **Bo'sh baza bilan ishlash.** Baza fayli bo'sh/eski bo'lsa v1 jim ishlayverdi va
   har 15 soniyada xato yubordi. v2: startda sxema versiyasi tekshiriladi, mos kelmasa
   bot ishga tushmaydi.
2. **Nisbiy yo'llar cwd'ga bog'liq.** v2: hammasi `DATA_DIR` ichida, absolyut yo'l.
3. **Ishlayotgan botdan backup tiklash.** v2: faqat to'xtatilgan holda.
4. **Xotiradagi sessiyalar** restartda yo'qoladi. v2: `conversation_state` jadvali.
5. **Testlar avtomatik ishlamaydi.** v2: CI.
