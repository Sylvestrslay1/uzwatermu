# uzwatermu — kod arxitekturasi va ishlash prinsiplari

> Bu fayl `README.md`ni almashtirmaydi (u imkoniyatlar va o'rnatish bo'yicha qo'llanma).
> Bu fayl kod ichida **nima qanday ishlashini** tushuntiradi: modullar, oqimlar, ma'lumotlar
> bazasi, xavfsizlik qatlamlari va fon jarayonlari. Coworking/jamoaga yuklash uchun yozilgan.

## 1. Loyiha papkasi

```text
/home/user/uzwatermu
```

Bu — joriy sessiyadagi (bulutli konteyner) manzil. Ishlab chiqarishda bot sizning
Windows kompyuteringizda/serveringizda boshqa papkada turadi (`.env` va Task Scheduler
shu real papka manziliga bog'langan bo'ladi).

## 2. Yuqori darajadagi papka tuzilmasi

```text
uzwatermu/
├── bot/                     # Botning butun biznes-mantig'i (Python paket)
│   ├── main.py              # Entry point: handlerlar, admin panel, fon ishchilar (~205 KB, eng katta fayl)
│   ├── config.py            # .env -> Config dataclass, validatsiya
│   ├── storage.py           # SQLite qatlami (BotStorage)
│   ├── excel_loader.py      # Excel (.xlsx) o'qish/yozish (AbonentBook)
│   ├── states.py            # Suhbat holatlari (FSM state konstantalari)
│   ├── buttons.py           # Barcha tugma matnlari (reply-keyboard label'lari)
│   ├── texts.py             # 3 tilli matnlar (TEXTS, WELCOME, GUIDE)
│   ├── formatters.py        # Foydalanuvchiga ko'rsatiladigan matn shablonlari
│   ├── masking.py           # Shaxsiy ma'lumotlarni (FIO/telefon/manzil) berkitish
│   ├── security.py          # Admin login flood-himoyasi (blok/urinish hisoblagichi)
│   ├── security_hardening.py# XLSX zip-bomb/makro tekshiruvi, log redaksiyasi
│   ├── rate_limit.py        # Foydalanuvchi so'rovlari uchun umumiy rate limiter
│   ├── runtime.py           # Process lock, health.json, shutdown signal'lari
│   ├── backup_manager.py    # Backup to'plam yaratish/tiklash/manifest
│   ├── health_checks.py     # Preflight: DB/Excel/disk/backup tekshiruvi
│   ├── encryption.py        # AES-256-GCM fayl shifrlash (umumiy)
│   ├── meter_vault.py       # Hisoblagich rasmlarini shifrlangan saqlash
│   ├── secret_store.py      # Windows DPAPI orqali parol/token saqlash
│   ├── code_integrity.py    # bot/ va tools/ fayllarining HMAC muhri (tamper-detection)
│   ├── image_matching.py    # Hisoblagich rasm fingerprint va moslik ballari
│   ├── debt_texts.py        # Qarzdorlik ogohlantirish matn shablonlari
│   ├── table_reports.py     # 3-oylik/qarzdor/kreditor Excel hisobotlari generatori
│   ├── passport_report.py   # "Tuman pasporti" hisoboti (F3 jadvaldan)
│   └── f3_extract.py        # "Umumiy shablon" F3 dan chiqarish
├── tools/                   # Windows'da ishga tushirish/xavfsizlik vositalari
│   ├── bot_supervisor.py    # Botni subprocess sifatida ishga tushiradi, qulasa qayta ko'taradi
│   ├── windows_job.py       # Windows Job Object: ota process o'lsa bola ham o'ladi
│   ├── install_startup_task.ps1 / uninstall_startup_task.ps1
│   ├── start_bot_hidden.ps1 # Yashirin oynada supervisor'ni ishga tushiruvchi wrapper
│   ├── harden_windows_acl.ps1 # Loyiha papkasi ACL'ini faqat kerakli foydalanuvchilarga cheklaydi
│   ├── seal_code_integrity.py   # code_integrity.py uchun HMAC manifest yaratadi
│   ├── setup_encryption.py      # ENCRYPTION_ENABLED/parol sozlash
│   ├── migrate_env_secrets.py   # .env dagi maxfiy qiymatlarni DPAPI'ga ko'chiradi
│   ├── update_service_secrets.py / update_secret_gui.py / update_openai_secret_gui.py
│   └── encrypt_data_snapshot.py # Joriy ma'lumotlarning o'zgarmas shifrlangan nusxasi
├── tests/                   # unittest asosidagi 180+ test (bot ichki mantig'ini sinaydi)
├── data/                    # abonents.xlsx, inspectors.xlsx (runtime'da yaratiladi)
├── storage/                 # bot.sqlite3 (runtime'da yaratiladi)
├── backups/, logs/, outputs/, work/, encrypted_vault/, secrets/  # runtime papkalari (.gitignore'da)
├── .env.example             # Muhit o'zgaruvchilari shabloni
├── requirements.txt
└── create_excel_template.py # Bo'sh Excel shablon yaratuvchi skript
```

`.env`, `storage/`, `backups/`, `data/`, `secrets/`, `encrypted_vault/` — barchasi
`.gitignore`da. Ya'ni **haqiqiy ma'lumotlar va maxfiy kalitlar Git repozitoriyga
hech qachon tushmaydi** — faqat kod tushadi.

## 3. Ishga tushirish zanjiri (Windows'da production)

```text
Task Scheduler (install_startup_task.ps1 bilan o'rnatilgan)
  -> tools/bot_supervisor.py   (subprocess nazoratchi, infinite restart loop)
      -> python -m bot.main    (haqiqiy bot processi)
```

`bot_supervisor.py`:
- Avval `verify_code_integrity()` ni chaqiradi — agar kod fayllari HMAC muhridan
  farq qilsa (ruxsatsiz o'zgartirilgan bo'lsa), bot **umuman ishga tushmaydi** va
  adminlarga xabar yuboradi.
- `bot.main`ni subprocess sifatida ishga tushiradi, stderr'ni `logs/supervisor.log`ga yozadi.
- Agar process kutilmaganda to'xtasa (crash), eksponensial backoff bilan (5s, 10s, ... 300s
  gacha) qayta ishga tushiradi va adminlarga Telegram orqali xabar beradi.
- `exit code == 3` — "boshqa nusxa allaqachon ishlayapti" degani (`ProcessLock`dan keladi) —
  bu holda supervisor o'zi ham to'xtaydi (ikkita bot bir xil DB/Excel'ga yozmasin deb).
- `WindowsKillOnCloseJob` — Windows Job Object orqali, agar supervisor process o'lib qolsa,
  bola (bot) process ham avtomatik o'ldiriladi (osilib qolgan process qolmasligi uchun).

`bot/main.py:main()` ichida ishga tushish tartibi:

1. `verify_code_integrity()` — yana bir marta, bot process darajasida ham.
2. `load_config()` — `.env`ni o'qiydi, validatsiya qiladi (token formati, majburiy
   maydonlar, shifrlash sozlamasi). Noto'g'ri bo'lsa `RuntimeError` bilan darhol to'xtaydi.
3. `ensure_runtime_dirs()` — `data/`, `storage/`, `outputs/`, `work/`, `logs/`,
   `encrypted_vault/meter_photos/`, `backups/` papkalarini yaratadi.
4. `run_system_preflight()` — SQLite, ikkala Excel fayli, disk bo'sh joyi va oxirgi
   sog'lom backup tekshiriladi (`bot/health_checks.py`). **Kritik** xato bo'lsa
   (masalan, Excel fayli yo'q/buzilgan) — bot ishga tushmaydi, yangi bo'sh baza
   yaratib "jim" ishlamaydi.
5. `AbonentBook(...)` va `BotStorage(...)` ob'ektlari yaratiladi (global `book`, `storage`).
6. `telebot.TeleBot(...)` yaratiladi, handlerlar ro'yxatdan o'tkaziladi.
7. Bir nechta **fon thread** ishga tushadi (6-bo'limga qarang).
8. `bot.infinity_polling(...)` chaqiriladi (long-polling — webhook emas).

`ProcessLock` (`storage/uzwatermu.lock`) — OS darajasidagi fayl lock (`fcntl`/`msvcrt`)
orqali bitta vaqtda faqat bitta bot nusxasi ishlashini kafolatlaydi.

## 4. Xabarlarga ishlov berish arxitekturasi

Bot **pyTelegramBotAPI (`telebot`)** kutubxonasida, **long-polling** rejimida ishlaydi
(webhook yo'q — tashqi ochiq portga ehtiyoj yo'q).

- Har bir foydalanuvchi uchun **sessiya** (`sessions: dict[int, dict]`) xotirada
  saqlanadi — bu suhbat holati (qaysi "state"da turibdi, vaqtincha kiritilgan
  ma'lumotlar, hisoblagich rasmlari ro'yxati va h.k.). 1 soat harakatsiz qolgan
  sessiyalar avtomatik tozalanadi.
- `states.py` — oddiy string konstantalar bilan ifodalangan **holat mashinasi**
  (FSM): masalan `ENTERING_ACCOUNT`, `WAITING_METER_PHOTO`, `ADMIN_BROADCAST_UZ`
  va h.k. Har bir handler `current["state"]`ga qarab qanday xabar kutilayotganini
  aniqlaydi.
- `serialized_message_handler` dekoratori — bitta foydalanuvchining xabarlari
  **parallel ishlov berilmasligini** kafolatlaydi (har bir `telegram_id` uchun
  alohida `threading.RLock`, `weakref.WeakValueDictionary`da saqlanadi — xotira
  sizmasin deb). Bu racing holatlarni oldini oladi (masalan, bitta foydalanuvchi
  tez-tez bir nechta rasm yuborsa).
- `RequestRateLimiter` (`rate_limit.py`) — har bir foydalanuvchi/xodim uchun
  vaqt oynasi (`REQUEST_WINDOW_SECONDS`) ichida so'rovlar sonini cheklaydi;
  limitdan oshsa vaqtincha bloklaydi (`FLOOD_BLOCK_SECONDS`) va auditga yozadi.

Oqim namunasi (yangi abonent ro'yxatdan o'tishi):

```text
/start -> til tanlash -> hisob raqam kiritish (Excel'dan tekshiriladi)
  -> telefon tasdiqlash -> admin/operatorlarga "✅/❌" tugmali so'rov yuboriladi
  -> admin tasdiqlasa -> foydalanuvchiga asosiy menyu ochiladi, kanalga audit xabari ketadi
  -> admin rad etsa -> foydalanuvchiga rad etilgan xabari ko'rsatiladi
```

## 5. Ma'lumotlar manbalari: Excel va SQLite — ikki alohida qatlam

Bot ataylab **ikkita** ma'lumot manbasidan foydalanadi, chunki ularning vazifasi farqli:

| Manba | Fayl | Vazifasi |
|---|---|---|
| **Excel** (`AbonentBook`, `excel_loader.py`) | `data/abonents.xlsx`, `data/inspectors.xlsx` | "Haqiqat manbasi" — abonent FIO, manzil, balans, inspektor. Boshqaruv bo'limi tomonidan tashqarida yuritiladi va admin panel orqali almashtiriladi. |
| **SQLite** (`BotStorage`, `storage.py`) | `storage/bot.sqlite3` | Botning o'z holati — foydalanuvchilar, arizalar, audit loglar, operatorlar, inspektor sessiyalari va h.k. |

**`AbonentBook`** butun Excel faylni xotiraga o'qiydi (`dict[account, Abonent]`), shuning
uchun qidiruv tez. Ustun nomlarini **alias lug'ati** orqali avtomatik taniydi (masalan
"hisob raqam", "ls", "лицевой счет" — barchasi `account` maydoniga tushadi), shuningdek
"Real Abonent" formatidagi (mahalla/ko'cha/uy ustunli) faylni ham alohida xaritalash
orqali qo'llab-quvvatlaydi. Admin Excel almashtirsa, bot qayta ishga tushirilmasdan
`reload()` qilinadi.

**`BotStorage`** — oddiy `sqlite3` ustidan yupqa qatlam:
- Ulanish har safar yangidan ochiladi (`sqlite3.connect`), **WAL** jurnal rejimi,
  `busy_timeout=30000`, `foreign_keys=ON`.
- `_init()` barcha jadvallarni `CREATE TABLE IF NOT EXISTS` bilan yaratadi (xavfsiz,
  mavjud jadvalga tegmaydi) — bot ishga tushganda avtomatik chaqiriladi.
- **O'z-o'zini tiklash**: agar biror so'rov `"no such table"` xatosi bersa (masalan,
  baza fayli eski nusxa bilan almashtirilgan bo'lsa), `_connect()` buni ushlab,
  sxemani zudlik bilan qayta tiklaydi va keyingi urinish muvaffaqiyatli bo'ladi.
- Asosiy jadvallar: `users`, `user_accounts`, `submissions`, `meter_photos`,
  `operators`, `debt_warnings`, `audit_logs`, `inspector_users`,
  `inspector_location_sessions/responses/relays`, `admin_access_attempts`,
  `meter_review_messages`.

## 6. Fon jarayonlari (background threads)

`main()` ichida bir nechta doimiy `daemon` thread ishga tushadi, har biri o'z
davriyligi bilan, barchasi `shutdown_event` orqali tozalik bilan to'xtaydi:

| Thread | Vazifasi | Davriylik |
|---|---|---|
| `health_worker` | `logs/health.json`ga heartbeat yozadi (supervisor shuni o'qiydi) | 15s |
| `integrity_monitor_worker` | Kod fayllari HMAC muhrini davriy qayta tekshiradi | — |
| `automatic_backup_worker` | `BACKUP_INTERVAL_HOURS` bo'yicha avtomatik backup | soatlik tekshiruv |
| `debt_analysis_worker` | Oyning 1,5,10,15,20,25,30-kunlarida qarzdorlik tahlili | kunlik tekshiruv |
| `inspector_location_monitor_worker` | Live-lokatsiya muddatlari/eslatmalarini kuzatadi | 15s |
| HTTP health server (`_http_health_server_worker`) | `HEALTH_PORT` sozlansa, oddiy HTTP orqali holat qaytaradi | — |

Har bir worker o'z ichida `try/except` bilan o'ralgan — bitta worker xato bersa,
`notify_error(...)` orqali adminlarga Telegram xabari ketadi va worker **davom etadi**
(butun bot yiqilmaydi).

### Inspektor live-lokatsiya nazorati — holat mashinasi

```text
Super admin "📡 Live lokatsiya buyrug'i" bosadi
  -> barcha faol inspektorlarga "kamida 1 soat live lokatsiya yoqing" buyrug'i
  -> 10 daqiqa: bajarmaganlarga eslatma
  -> yana 10 daqiqa: yakuniy muddat
  -> muddat tugasa: bajarmagan inspektorlar ro'yxati super adminlarga yuboriladi
```

Bu holat SQLite'da (`inspector_location_sessions`/`responses`) saqlanadi, shuning
uchun bot qayta ishga tushsa ham jarayon davom etadi (xotirada emas).

## 7. Xavfsizlik qatlamlari

Loyiha bir nechta mustaqil xavfsizlik qatlamidan iborat — har biri turli tahdiddan himoya qiladi:

1. **Kod yaxlitligi** (`code_integrity.py`) — `bot/` va `tools/` ichidagi har bir
   `.py`/`.ps1` faylining SHA-256 xeshi + HMAC imzosi `secrets/code_integrity_manifest.json`da
   saqlanadi. Kod o'zgarsa (masalan, zararli kod kiritilsa) — bot ishga tushmaydi.
   Yangi kod joylanganda `tools/seal_code_integrity.py` bilan qayta muhrlash kerak.
2. **Maxfiy kalitlar** (`secret_store.py`) — bot tokeni va boshqa kalitlar `.env`da emas,
   **Windows DPAPI** orqali shifrlab saqlanadi (`secrets/*.dpapi`). Faqat ularni
   yaratgan Windows foydalanuvchisi ochadi — disk o'g'irlansa ham kalit ochilmaydi.
3. **Fayl shifrlash** (`encryption.py`) — AES-256-GCM + Scrypt key-derivation.
   Backup, eksportlar, hisoblagich rasmlari (`meter_vault.py`) shu orqali shifrlanadi
   (`ENCRYPTION_ENABLED=true` bo'lsa).
4. **Excel yuklash xavfsizligi** (`security_hardening.py`) — yuklangan `.xlsx` fayl
   ZIP-bomba, makro (`vbaProject`), tashqi formulalar (`WEBSERVICE`, `HYPERLINK("http...`)
   bo'yicha tekshiriladi, shundan keyingina ishonchli deb hisoblanadi.
5. **PII (shaxsiy ma'lumot) berkitish** (`masking.py`) — audit log, xatolik xabarlari
   va eksportlarda FIO/telefon/manzil/hisob raqami **qisman berkitiladi** (masalan
   `+998 90 *** * 123`). Log va xatolik xabarlarida loyihaning to'liq fayl yo'li ham
   `<project>`ga almashtiriladi (`redact_sensitive_text`).
6. **Admin login himoyasi** (`security.py`) — 10 daqiqada 5 marta noto'g'ri/ruxsatsiz
   `/admin` urinishi — 30 daqiqaga blok. Admin sessiyasi 30 daqiqadan keyin eskiradi.
7. **Rate limiting** (`rate_limit.py`) — flood/DoS'dan himoya, fayl hajmi va rasm soni
   chegaralari.
8. **Backup/restore yaxlitligi** (`backup_manager.py`) — har bir backup to'plami
   SHA-256 nazorat summali `manifest.json` bilan keladi; tiklashdan oldin hash
   tekshiriladi, muvaffaqiyatsiz bo'lsa **avtomatik rollback** qilinadi (eski fayl
   qaytariladi).
9. **Preflight / integrity monitoring** (`health_checks.py`) — bot ishga tushishdan
   oldin va keyin davriy ravishda DB/Excel/disk/backup holatini tekshiradi, muammo
   bo'lsa ogohlantiradi (kritik bo'lsa ishga tushmaydi).

## 8. Hisobot generatorlari (Excel yozuvi past darajada)

`table_reports.py`, `passport_report.py`, `f3_extract.py` — bu uchtasi **XLSX faylni
`openpyxl` orqali emas, balki to'g'ridan-to'g'ri ZIP/XML darajasida** o'qib-yozadi
(`zipfile` + qo'lda XML transformatsiya). Sabab: manba shablon (F3 jadval) formatlash,
formula va diagrammalarini **aynan saqlab qolish**, faqat kerakli qatorlarni filtrlash/
ko'chirish kerak (`openpyxl` buni to'liq saqlab qololmaydi). Bu fayllar eng murakkab va
"qo'lda yozilgan XML operatsiyalari" ko'p joy — o'zgartirishda ehtiyot bo'lish kerak.

- `table_reports.py` — 3 oylik ko'rsatkich olinmaganlar, qarzdorlar ro'yxati, kreditor
  iste'molchilar, hisob-kitob yuritilmayotganlar hisobotlari.
- `passport_report.py` — "Tuman pasporti" (F3 jadvaldan yig'ma statistik hisobot).
- `f3_extract.py` — "Umumiy shablon"ni F3 dan ajratib olish.

## 9. Testlar

`tests/` papkasida `unittest` asosida **180+ test** bor — har bir modulning asosiy
mantig'i (masalan `test_inspector_location_control.py`, `test_backup_manager.py`,
`test_privacy_regression.py`, `test_security_hardening.py`) alohida sinaladi. Ishga
tushirish:

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

Ba'zi testlar (`test_three_month_report.py`, Excel haqiqiyligini tekshiruvchi testlar)
`data/abonents.xlsx` va `outputs/` ichidagi real hisobot fayllariga bog'liq — ular
faqat real ma'lumotlar mavjud muhitda (masalan, production papkada) o'tadi.

## 10. Muhim arxitektura qoidalari (kod bilan ishlaganda yodda tutish)

- **`bot/main.py` — monolit fayl** (~205 KB). Yangi admin bo'lim/tugma qo'shishda:
  1) `buttons.py`ga matn qo'shiladi, 2) kerak bo'lsa `states.py`ga holat qo'shiladi,
  3) `main.py`dagi tegishli klaviatura funksiyasi va `handle_admin_menu`/
  `handle_admin_state` ichiga tarmoq qo'shiladi.
- **Hech qachon** `.env`ga parol/maxfiy kalit yozilmaydi — faqat DPAPI (`secret_store.py`)
  orqali.
- **Hech qachon** Excel/SQLite fayllar to'g'ridan-to'g'ri ustiga yozilmaydi — avval
  `work/` ichida vaqtinchalik faylga yoziladi, tekshiriladi, keyin atomik `replace()`
  bilan almashtiriladi (crash bo'lsa ham fayl yarim yozilgan holda qolmasin deb).
- **Har bir fon worker** o'z xatosini ushlab, `notify_error()` orqali xabar beradi va
  ishlashda davom etadi — bitta worker butun botni yiqitmasligi kerak.
- **Shaxsiy ma'lumotlar** faqat kerak joyda, kerakli odamga (admin/operator) to'liq
  ko'rinadi; audit log, eksport va xatolik xabarlarida har doim `masking.py` orqali
  qisman berkitiladi.
