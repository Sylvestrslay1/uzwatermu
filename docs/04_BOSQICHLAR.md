# uzwatermu v2 — ish bosqichlari

Har bir bosqich buyurtmachi bilan alohida tasdiqlangan. Talablar — `03_KELISHILGAN_TALABLAR.md` da.
Har bir bosqich alohida Git branch'da bajariladi va testlar (CI) muvaffaqiyatli o'tgandan keyin `v2` ga qo'shiladi.
Ishlab chiqish va sinov **test bot, test kanal va test guruh** bilan olib boriladi.

| № | Bosqich | Jarayonlar | Bog'liqligi |
|---|---|---|---|
| 0 | Poydevor | — | — |
| 1 | Ma'lumot yangilash | J7 | 0 |
| 2 | Bosh sahifa va iste'molchi paneli | J1 (avtomatik ulanish), J4 | 1 |
| 3 | Operatorlar va ko'rsatkichlar | J1 (operator orqali), J2, J10 (operator) | 2 |
| 4 | Inspektorlar | J5, J6, J10 (inspektor) | 3 |
| 5 | Murojaatlar | J3 | 3 |
| 6 | Ommaviy xabarlar | J9 | 3 |
| 7 | KPI va reyting | J8 | 4 |
| 8 | Nazorat va xavfsizlik | J11, J12 | 3 |
| 9 | Ishga tushirish | v1 → v2 ko'chirish | 0–8 |

## 0. Poydevor
- Ma'lumotlar bazasini yangi qarorlarga moslash:
  - abonentlarning shaxsiy ma'lumotlari uchun jadval olib tashlanadi;
  - 0-bosqichda faqat ishlatiladigan jadvallar yaratiladi: foydalanuvchilar va rollar, hisob raqam bog'lanishlari, sozlamalar, audit log;
  - ruxsatlar, taklif havolalari, navbat, murojaatlar, vazifalar va ommaviy xabarlar jadvallari o'z bosqichida alohida migratsiya (`0002_…`, `0003_…`) bilan qo'shiladi.
- `.env`: test token, hisobot kanali, asosiy guruh, import papkasi, zaxira akkauntlar, maxfiy so'z xeshi.
- `/start` bosilganda foydalanuvchi rolini aniqlash va kerakli panelga yo'naltirish.
- Klaviatura asosi: matn yozilsa "Menyudan tanlang" javobi; har bir panelda `Sozlamalar → Til`.
- 3 tilli matnlar tizimi, audit log yozuvchisi.
- **Tayyorlik mezoni:**
  - `/start` → salom → til tanlash → bosh sahifa menyusi ishlaydi;
  - admin admin paneliga o'tadi;
  - testlar (CI) muvaffaqiyatli o'tadi.

## 1. Ma'lumot yangilash (J7)
- Import papkasi. Dastlab ikki fayl: abonentlar ro'yxati va inspektorlar ro'yxati (F.I.O, hudud, xizmat telefoni).
- Fayl tekshiruvi:
  - xavfsizlik (makros, yashirin havolalar);
  - majburiy ustunlar;
  - takrorlangan hisob raqamlar;
  - telefon va summa formatlari.
- Tekshiruv hisoboti va o'zgarishlar — faqat adminga. Admin tasdiqlagach ma'lumot RAM'ga yuklanadi. Faylda xato bo'lsa, eski ma'lumot saqlanib qoladi.
- Bot qayta ishga tushganda ma'lumot avtomatik yuklanadi va adminga xabar boradi.
- **Tayyorlik mezoni:** yangilash → hisobot → tasdiqlash ishlaydi; bot qayta ishga tushgach ma'lumot o'z-o'zidan yuklanadi.
- **Kerak:** ikkala faylning ustunlari, to'qima ma'lumotli namuna bilan (ochiq savol №6).

## 2. Bosh sahifa va iste'molchi paneli
- Bot tavsifi: o'zbek (lotin), rus va standart variant. Telegram tillarni ikki harfli kod bilan ajratadi.
- `/start` oqimi va menyu: Ro'yxatdan o'tish · Yordam · Sozlamalar · Aloqa.
- J1, avtomatik yo'l:
  - hisob raqam kiritish urinishlari cheklanadi;
  - faqat foydalanuvchining o'z kontakti qabul qilinadi;
  - telefon mos kelsa, avtomatik ulanadi;
  - kontakt xabari chatdan o'chiriladi.

  Telefon mos kelmasa, so'rov navbatga yoziladi va 3-bosqichda ko'rib chiqiladi.
- Iste'molchi paneli:
  - ma'lumot kartochkasi;
  - Balans, Hisob raqamlarim, Hudud inspektori, Aloqa, Sozlamalar (til, yordam).
- Yordam bo'limining tuzilmasi tayyorlanadi; qo'llanma matnlari keyin qo'yiladi (ochiq savol №8).
- **Tayyorlik mezoni:** test abonent ro'yxatdan o'tadi, paneldagi barcha tugmalar ishlaydi.
- **Kerak:** idoraning aloqa ma'lumotlari (telefon, manzil, koordinatalar) va ish vaqti.

## 3. Operatorlar va ko'rsatkichlar
- Operator qo'shish: havola (24 soat) yoki Telegram ID → til tanlash → panel.
- Har bir operatorga alohida ruxsatlar.
- Telefoni mos kelmagan ro'yxatdan o'tish so'rovlari: navbat → ✅ yoki ❌ + sabab.
- J2:
  - rasm soni va hajmi cheklangan; takroriy rasm ⚠️ bilan belgilanadi;
  - `📸 Keyingi ariza (N)` navbati;
  - ✅ → hisobot kanali va iste'molchiga xabar;
  - ❌ + sabab → iste'molchi oyiga 3 martagacha qayta yubora oladi.
- Admin uchun: operatorlar ro'yxati, operatorni uzish, navbatlar holati.
- **Tayyorlik mezoni:** rasm → operator ✅ → test kanalda paydo bo'ladi.
- **Kerak:** test kanal.

## 4. Inspektorlar
- Inspektorlar ro'yxatidan shaxsiy havolalar (72 soat), havolalar Excel faylga chiqariladi.
  - Inspektor ism va hududini tasdiqlaydi, so'ng tilni tanlaydi.
  - Adminda havolalar holati, havolani qayta yaratish, inspektorni uzish, hududni o'zgartirish.
- J5 — vazifalar:
  - yaratish;
  - yo'naltirish: hudud inspektori; vakant hududda operator tanlagan inspektor yoki admin; admin istalgan inspektorga;
  - natija: izoh, rasm va 15 daqiqalik live lokatsiya;
  - vazifani operator yoki admin yopadi;
  - muddati o'tsa eslatma;
  - J2 bilan bog'lanish: 3-rad etishdan keyin vazifa yaratish taklifi.
- O'z hududi bo'yicha qidiruv, har bir ko'rish audit logga yoziladi.
- J6 — live lokatsiya:
  - buyruq → kamida 1 soatlik live lokatsiya → asosiy guruh;
  - +10 daqiqada ogohlantirish;
  - +5 daqiqada yubormaganlar ro'yxati adminga.
- **Tayyorlik mezoni:** havola orqali ulanish → vazifa → natija; lokatsiya buyrug'i test guruhida ishlaydi.
- **Kerak:** test guruh.

## 5. Murojaatlar (J3)
- Murojaat: matn va ixtiyoriy rasm, kuniga 3 ta. Suhbatni davom ettirish mumkin.
- Ruxsati bor operatorlar murojaatlarni navbat orqali oladi va **erkin matnda** javob beradi. Tayyor javob shablonlari keyinroq qo'shiladi.
- Yopish: operator yoki 3 kun jimlikdan keyin avtomatik. 24 soat javobsiz qolsa, adminga eslatma.
- **Tayyorlik mezoni:** savol → javob → suhbat davom etadi → avtomatik yopiladi.

## 6. Ommaviy xabarlar (J9)
- Turlari: qarzdorlarga; ko'rsatkich yubormaganlarga; yangilik (hammaga yoki hududlar bo'yicha).
- Bosqichli chegaralar va 3 tilli matnlarni admin bot ichida sozlaydi.
- Tasdiqlash oynasi: qabul qiluvchilar soni, oldindan ko'rinish, ma'lumot sanasi.
  - Yuborish faqat admin yoki ruxsati bor operator tasdiqlagandan keyin.
- Yuborish:
  - Telegram cheklovlariga mos tezlikda;
  - restartdan keyin davom etadi;
  - `⏹ To'xtatish` tugmasi;
  - takroriy yuborish cheklangan.
- Natija hisoboti va audit log.
- **Tayyorlik mezoni:** uchala turdagi xabar yuboriladi; to'xtatish va davom ettirish ishlaydi.
- **Kerak:** ogohlantirish matnlari (v1 dagi `debt_texts.py` qoralama sifatida olinadi).

## 7. KPI va reyting (J8)
- KPI fayli import papkasi orqali yuklanadi.
- Har bir inspektor uchun:
  - tushum va xatlov: reja, bajarildi, qoldiq, %;
  - xatlov bo'yicha 60% va 80% gacha qolgan son;
  - kunlik me'yor.
- Reyting:
  - ko'rsatkichlar rejaga nisbatan foizda, yuqori chegarasi 120%;
  - ulushlar bilan bitta umumiy ball;
  - kunlik va oylik; vakant hududlar kirmaydi.
- Admin tasdiqlagach har bir inspektorga o'z KPI'si, top-5 va o'z o'rni yuboriladi. Panelda `📊 Mening KPI'm` tugmasi paydo bo'ladi.
- **Tayyorlik mezoni:** raqamlar qo'lda hisoblangan natija bilan mos keladi; reyting yetkaziladi.
- **Kerak** (ochiq savollar №3, №4):
  - KPI fayli ustunlari va namuna;
  - raqamlar oy boshidan jamlanganmi yoki kunlikmi;
  - ish haftasi va bayram kunlari;
  - ball ulushlari.

## 8. Nazorat va xavfsizlik (J11, J12)
- Audit log:
  - qidiruv;
  - operatorlar hisoboti;
  - kunlik xulosa (08:00);
  - 1 yildan keyin nazorat summasi bilan avtomatik arxivlash; qo'lda arxivlash;
  - botda o'chirish yo'q.
- Favqulodda huquqlarni bekor qilish:
  - maxfiy so'z xeshini kompyuterda yaratish uchun skript;
  - urinishlar cheklanadi, boshqa zaxira akkauntlarga xabar boradi;
  - bekor qilingan akkaunt kanal va guruhdan chiqariladi;
  - zaxira akkaunt vaqtincha admin bo'ladi.
- Sozlamalar ekrani, tizim xabarlari.
- Ma'lumotlar bazasining kunlik zaxira nusxasi; tiklash faqat kompyuterda, bot to'xtatilgan holda.
- **Tayyorlik mezoni:**
  - favqulodda vaziyat mashqi muvaffaqiyatli o'tadi;
  - arxiv fayli yaratiladi va nazorat summasi tekshiriladi;
  - zaxira nusxadan tiklash sinab ko'riladi.
- **Kerak:** test zaxira akkaunt.

## 9. Ishga tushirish
- Operatorlar va inspektorlar bilan test botda 1 haftalik sinov.
- Kompyuterni tayyorlash:
  - Windows servisi, import papkasi;
  - `.env` ga kirish huquqlari, BitLocker;
  - ikki bosqichli tasdiqlash;
  - kanal va guruh egaligi zaxira akkauntga o'tkaziladi;
  - botga kanal va guruhda admin huquqlari beriladi.
- v1 → v2 ko'chirish:
  - ko'chiriladi: iste'molchilarning tasdiqlangan bog'lanishlari, tillari, **ko'rsatkichlar tarixi**;
  - ko'chirilmaydi: v1 dagi telefon va boshqa shaxsiy ma'lumotlar;
  - operatorlar va inspektorlar yangi havolalar orqali qayta ulanadi;
  - v1 bazasining to'liq nusxasi arxivga olinadi.
- Ishga tushirish kuni:
  ```
  v1 to'xtatiladi → nusxa → ko'chirish skripti → haqiqiy token, kanal va guruh → v2 ishga tushadi → tekshiruv
  ```
- Orqaga qaytish: v2 to'xtatiladi, v1 qayta yoqiladi (v1 bazasiga tegilmaydi).
- **Tayyorlik mezoni:** iste'molchilar qayta ro'yxatdan o'tmasdan panelga kiradi; v1 o'chirilgan, lekin nusxasi saqlangan.

## Ochiq savollar qaysi bosqichda yopiladi

| № | Savol | Bosqich |
|---|---|---|
| 1 | Operator uchun abonent qidirish | 3 (yoki keyin) |
| 2 | Operatorlarning qo'shimcha vazifalari | 3 dan keyin |
| 3 | KPI ma'lumot manbai va fayl tuzilmasi | 7 |
| 4 | Reyting ball ulushlari | 7 |
| 5 | Murojaatga javob turi | ✅ yopildi: erkin matn, keyinroq shablonlar |
| 6 | Excel fayllar ro'yxati va ustunlari | 1 |
| 7 | Rahbariyat roli | 9 dan keyin |
| 8 | Qo'llanma matnlari | 2 |
