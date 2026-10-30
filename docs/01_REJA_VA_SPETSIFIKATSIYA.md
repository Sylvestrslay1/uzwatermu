# uzwatermu v2 — qayta loyihalash rejasi va texnik spetsifikatsiya

## 0. Nima uchun qayta quramiz

Joriy bot (v1) ishlaydi, lekin uch toifadagi muammo to'plangan:

1. **Keraksiz murakkablik.** `bot/` jami ~12 100 qator, shundan `main.py` bir o'zi
   5 462 qator: tugmalar, handlerlar, biznes-mantiq, fon ishchilar, xavfsizlik
   tekshiruvlari — hammasi bitta faylda. Asosiy vazifa (abonentdan hisoblagich
   rasmini qabul qilish) atrofiga ko'plab alohida tizimlar yopishtirilgan.
2. **Axborot xavfsizligidagi kamchiliklar** — ko'p qatlam bor, lekin ularning bir
   qismi haqiqiy himoya bermaydi, bir qismi esa ishlashni mo'rt qiladi (3-bo'lim).
3. **Ekspluatatsiya mo'rtligi.** Yo'llar nisbiy, ishga tushirish Windows'ga xos
   qo'lda yozilgan skriptlarga bog'liq, sxema o'zgarishlari qo'lda "yamaladi".
   Loyihani C: dan D: ga ko'chirish bazaning bo'sh qolib, botning cheksiz
   `no such table` xatosi berishiga olib kelgani — shuning natijasi.

v2 maqsadi: **kichikroq, tushunarli, tekshiriladigan** bot; xavfsizlik — real
tahdidlarga mos va oddiy; har bir qo'shimcha imkoniyat — alohida, o'chirib
qo'yiladigan modul.

## 1. Imkoniyatlar triaji (nima qoladi, nima ketadi)

### 1.1. YADRO (v2.0 da albatta bo'ladi)

| # | Imkoniyat | Izoh |
|---|---|---|
| C1 | `/start`, 3 til (uz, uz_cyrl, ru) | Matnlar alohida fayllarda (`locales/`) |
| C2 | Hisob raqam bo'yicha abonentni topish | Ma'lumot manbai — SQLite (Excel faqat import uchun, 4-bo'lim) |
| C3 | Telefon orqali egalikni tasdiqlash | Telegram `contact.user_id == from_user.id` tekshiruvi saqlanadi |
| C4 | Operator/admin tasdiqlovi (✅/❌) | |
| C5 | Shaxsiy kabinet (maskalangan ma'lumot) | |
| C6 | Hisoblagich rasmini yuborish → hisobot kanaliga | Rasm soni/hajmi limiti saqlanadi |
| C7 | Admin: abonent qidirish, kutilayotgan so'rovlar, Excel import | |
| C8 | Rollar: super admin / operator | DB'da, `.env`da faqat boshlang'ich super admin |
| C9 | Audit log (kim, qachon, nima) | Maskalash bilan |
| C10 | Rate limit | Sodda, xotirada — yetarli |
| C11 | Avtomatik backup (SQLite `.backup` + saqlash muddati) | Tiklash — CLI buyruq orqali, botdan emas |

### 1.2. IXTIYORIY MODULLAR (yadro tayyor bo'lgach, bittadan qo'shiladi)

Har biri `modules/<nom>/` papkasida, `.env`dagi `ENABLED_MODULES=` orqali yoqiladi.

| Modul | v1 dagi joyi | Tavsiya |
|---|---|---|
| `broadcast` — 3 tilli ommaviy xabar | `main.py` | Saqlash, lekin yuborish navbati DB'da (restartda yo'qolmasin) |
| `debt` — qarzdorlik ogohlantirishi | `main.py`, `debt_texts.py` | Saqlash. Avtomatik yuborishni o'chirib, faqat admin tasdiqlab yuboradigan qilish |
| `inspectors` — live-lokatsiya nazorati | `main.py` (~400 qator) | Haqiqatan kerakligini qayta ko'rib chiqing. Kerak bo'lsa — alohida modul |
| `reports` — jadval hisobotlari | `table_reports.py`, `passport_report.py`, `f3_extract.py` (~2 100 qator) | **Botdan ajratish** — alohida CLI skript sifatida. XLSX ichidagi XML'ni qo'lda o'zgartirish juda mo'rt |

### 1.3. OLIB TASHLANADI yoki ALMASHTIRILADI

| v1 dagi narsa | Muammo | v2 da |
|---|---|---|
| `tools/update_openai_secret_gui.py`, OpenAI kalit boshqaruvi | Kodda OpenAI umuman ishlatilmaydi | Olib tashlanadi |
| `image_matching.py` — rasmni "barmoq izi" bilan avto-tasdiqlash | dHash+gistogramma — firibgarlikka qarshi ishonchsiz, noto'g'ri avto-rad etish xavfi | Olib tashlanadi; faqat qo'lda ko'rib chiqish + bir xil rasm qayta yuborilishini SHA-256 bilan aniqlash |
| `code_integrity.py` + `seal_code_integrity.py` (HMAC muhr) | Har kod o'zgarishida qo'lda muhrlash; kalit o'sha foydalanuvchi ostida — hujumchi qayta muhrlay oladi. Himoya bermaydi, ishlashni to'xtatadi | Olib tashlanadi. O'rniga: kod Git'dan, fayl ruxsatlari, faqat o'qiladigan deploy papkasi |
| `secret_store.py` (Windows DPAPI) + `migrate_env_secrets.py` + `update_secret_gui.py` | Bitta Windows foydalanuvchisiga bog'langan — OS qayta o'rnatilsa yoki foydalanuvchi o'zgarsa, kalit yo'qoladi | `.env` (fayl ruxsati faqat bot foydalanuvchisiga) yoki OS secret manager. Bitta oddiy mexanizm |
| `meter_vault.py` — har bir rasmni AES bilan shifrlab saqlash | Rasm baribir Telegram kanaliga yuboriladi; mahalliy shifrlangan nusxa qo'shimcha himoya bermaydi | Mahalliy nusxa saqlanmaydi; faqat Telegram `file_id` DB'da |
| `tools/windows_job.py`, `bot_supervisor.py`, `start_bot_hidden.ps1`, `install_startup_task.ps1`, `harden_windows_acl.ps1` | 5 ta qo'lda yozilgan Windows "yelim"i | Windows: **NSSM** (bitta servis); Linux: **systemd**. Qayta ishga tushirishni servis menejeri bajaradi |
| Botdan backup tiklash (`♻️ Oxirgi backupni tiklash`) | Ishlayotgan bot o'z bazasini almashtiradi — bo'sh baza holati shu yo'l bilan yuzaga kelishi mumkin | Tiklash faqat bot to'xtatilgan holda, CLI buyruq bilan |
| `_ensure_column` bilan sxemani yamash (15 joyda) | Versiyasiz; bazaning qaysi holatda ekanini bilib bo'lmaydi | Raqamlangan migratsiyalar (`migrations/0001_*.sql`), `schema_version` jadvali |
| Excel — asosiy ma'lumot manbai, ustunlarni alias bilan "taxmin qilish" | Ustun nomi o'zgarsa jimgina noto'g'ri o'qiydi | Excel faqat **import** formati: qat'iy ustunlar, import oldidan validatsiya, keyin SQLite'ga yoziladi |

## 2. Arxitektura

### 2.1. Qatlamlar

```text
telegram/handlers  ->  services  ->  repositories  ->  SQLite
      (UI)            (biznes-mantiq)   (SQL shu yerda)
```

- **handlers** — faqat Telegram xabarini o'qish va javob yuborish. SQL yo'q,
  biznes qoidalari yo'q.
- **services** — barcha qoidalar (masalan "bir abonent kuniga necha rasm yubora
  oladi"). Telegram'ni bilmaydi — shuning uchun oddiy unit-test bilan tekshiriladi.
- **repositories** — barcha SQL shu yerda, parametrli so'rovlar bilan.
- **config** — ishga tushganda bir marta yuklanadi va tekshiriladi.

Qoida: pastki qatlam yuqorisini import qilmaydi.

### 2.2. Holat (state) boshqaruvi

v1 da sessiya xotirada (`dict`) — restartda yo'qoladi. v2 da suhbat holati
SQLite'dagi `conversation_state` jadvalida (foydalanuvchi, holat, vaqt, JSON
ma'lumot) saqlanadi.

### 2.3. Texnologiyalar

| Soha | Tanlov | Sabab |
|---|---|---|
| Til | Python 3.12+ | v1 bilan bir xil, jamoa biladi |
| Telegram | `pyTelegramBotAPI` (v1 dagi) yoki `aiogram 3` | Tanlov sizda (6-bo'lim). Handlerlar ajratilgan bo'lgani uchun keyin almashtirish oson |
| Baza | SQLite (WAL) | Bitta server uchun yetarli |
| Excel import | `openpyxl` (faqat o'qish) | |
| Konfiguratsiya | `.env` + `pydantic-settings` | Turlar va majburiy maydonlar avtomatik tekshiriladi |
| Testlar | `pytest` | |
| Sifat | `ruff` (lint + format) | |
| CI | GitHub Actions: har push'da `ruff` + `pytest` | v1 da CI yo'q |

### 2.4. Yo'llar

Barcha yo'llar **loyiha ildiziga nisbatan** hisoblanadi (`Path(__file__)` asosida),
joriy ishchi papkaga (cwd) emas. Bitta `DATA_DIR` sozlamasi — barcha runtime
fayllar shu ichida (`db/`, `backups/`, `logs/`, `imports/`). Loyihani boshqa diskka
ko'chirish = papkani ko'chirish + servisni qayta ko'rsatish.

## 3. Xavfsizlik modeli

### 3.1. Real tahdidlar (bu bot uchun)

1. Boshqa birovning hisob raqamini kiritib, uning ma'lumotlarini ko'rish.
2. Ruxsatsiz shaxsning admin funksiyalariga kirishi.
3. Bot tokeni oshkor bo'lishi.
4. Yuklangan Excel orqali zararli kontent.
5. Shaxsiy ma'lumotning loglar/kanallar orqali sizib chiqishi.
6. Spam/flood.
7. Ma'lumot yo'qolishi (disk, noto'g'ri tiklash, ko'chirish).

### 3.2. Choralar

| Tahdid | Chora |
|---|---|
| 1 | Telefon tasdiqlash (C3) + operator tasdiqlovi (C4). Tasdiqlanmagan foydalanuvchi hech qanday shaxsiy ma'lumot ko'rmaydi |
| 2 | Rollar DB'da. Har bir admin handler bitta umumiy dekorator orqali tekshiriladi. Admin amallari faqat shaxsiy chatda. Muvaffaqiyatsiz urinishlar auditga |
| 3 | Token faqat `.env` da; `.env` ruxsati faqat servis foydalanuvchisiga; loglarga token yozilmaydi (redaksiya filtri `logging` darajasida). Oshkor bo'lsa — BotFather'da almashtiriladi |
| 4 | Excel: hajm limiti, `.xlsx` ZIP tuzilmasi tekshiruvi, makro/tashqi havola taqiqi (v1 dagi `validate_safe_xlsx` — **saqlanadi**, yaxshi yozilgan), qat'iy ustunlar |
| 5 | Maskalash bitta joyda (`security/masking.py`); kanalga faqat zarur maydonlar; loglarda shaxsiy ma'lumot yo'q |
| 6 | Rate limit (C10) |
| 7 | Kunlik backup + saqlash muddati; tiklash faqat to'xtatilgan botda; startda sxema versiyasi tekshiriladi — baza bo'sh yoki eski bo'lsa bot **ishga tushmaydi** va aniq xabar beradi |

### 3.3. Ataylab qilinmaydigan narsalar

Kod yaxlitligi HMAC muhri, DPAPI, har bir rasmni mahalliy shifrlash, EFS
sertifikatlari. Ular murakkablik qo'shadi, lekin 3.1 dagi tahdidlarga sezilarli
himoya bermaydi. Diskni to'liq shifrlash kerak bo'lsa — OS darajasida
(BitLocker/LUKS) yoqiladi, kodda emas.

## 4. Ma'lumotlar modeli (boshlang'ich)

`migrations/0001_init.sql` da:

- `abonents` — hisob raqam (PK), FIO, telefon, manzil, hudud, inspektor, balans, import vaqti
- `users` — telegram_id (PK), til, rol (`user`/`operator`/`admin`), yaratilgan vaqt
- `user_accounts` — telegram_id, hisob raqam, holat (`pending`/`approved`/`rejected`)
- `submissions` — id, telegram_id, hisob raqam, rasm `file_id`lari, rasm SHA-256, holat, vaqt
- `audit_log` — id, actor_id, amal, tafsilot, vaqt
- `conversation_state` — telegram_id (PK), holat, JSON, yangilangan vaqt
- `schema_version` — versiya

Excel importi: fayl → validatsiya hisoboti → admin tasdiqlaydi → bitta tranzaksiyada
`abonents` yangilanadi (eski holat backupga).

## 5. Bosqichlar

| Bosqich | Natija | Tayyor mezoni |
|---|---|---|
| 0 | Skelet, CI, migratsiya, config | `pytest` va `ruff` CI'da yashil |
| 1 | C1–C3: start, til, abonent topish, telefon tasdiqlash | Testlar + test bot bilan qo'lda sinov |
| 2 | C4–C6: tasdiqlash, kabinet, rasm yuborish | |
| 3 | C7–C9: admin panel, rollar, audit | |
| 4 | C10–C11: rate limit, backup; servis sifatida o'rnatish | Bot 1 hafta test rejimida |
| 5 | v1 ma'lumotlarini ko'chirish (7-bo'lim), ishga tushirish | v1 to'xtatiladi |
| 6+ | Ixtiyoriy modullar bittadan | Har biri o'z testlari bilan |

Har bosqich — alohida Git branch va PR.

## 6. Sizning qaroringiz kerak bo'lgan savollar

1. **Telegram kutubxonasi:** `pyTelegramBotAPI` (v1 dagi, tanish) yoki `aiogram 3`
   (zamonaviy, async, FSM tayyor)? Skeletda handlerlar ajratilgan, ikkalasi ham mos.
2. **Server:** Windows PC'da qoladimi yoki Linux VPS? (Servis o'rnatish shunga bog'liq.)
3. **Inspektor live-lokatsiya** — real ishlatilyaptimi? Ishlatilmasa, v2 ga olinmaydi.
4. **Jadval hisobotlari** — botdan alohida CLI bo'lishi maqbulmi?
5. **Abonent ma'lumotlari** — Excel'dan oyiga necha marta yangilanadi? (Import oqimini shunga moslaymiz.)

## 7. v1 dan v2 ga ko'chish

v1 bazasini v2 ga ko'chirish uchun bir martalik skript (`scripts/migrate_from_v1.py`) yoziladi:
`users`, `user_accounts`, `submissions` (rasm `file_id`lari bilan), `operators` → `users.role`,
`audit_logs` → `audit_log`. Ko'chirishdan oldin v1 bazasining to'liq nusxasi olinadi.
Ishga tushirish kuni: v1 to'xtatiladi → ko'chirish skripti → v2 ishga tushadi → tekshiruv.
Muammo bo'lsa v1 nusxasiga qaytiladi.
