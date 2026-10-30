# uzwatermu v2 — kelishilgan talablar

> **Bu hujjat — asosiy manba.** `01_REJA_VA_SPETSIFIKATSIYA.md` va
> `02_V1_DAN_KOCHIRISH_XARITASI.md` bilan ziddiyat bo'lsa, shu hujjat to'g'ri hisoblanadi.
> Har bir bo'lim buyurtmachi bilan bandma-band muhokama qilinib tasdiqlangan.

## 1. Umumiy tamoyillar

- Telegram **bot, uning tokeni va hisobot kanali qoladi**. Qolgan hammasi noldan yoziladi.
- Barcha tugmalar **klaviatura qismida** (reply keyboard) bo'ladi va doim ko'rinib turadi. Foydalanuvchi
  tugma o'rniga matn yozsa, bot "Menyudan tanlang" deb javob beradi va klaviaturani qayta ko'rsatadi.
- 3 til: o'zbek (lotin), o'zbek (kirill), rus. **Har bir rol panelida `⚙️ Sozlamalar → 🌐 Til`** bor.
- Ishlab chiqish va sinov **test bot tokeni** bilan olib boriladi. Asl token ishga tushirish kuni qo'yiladi:
  bitta token bilan bir vaqtda faqat bitta dastur ishlay oladi.

## 2. Shaxsiy ma'lumotlar

| Diskda saqlanadi | Faqat operativ xotirada (RAM) |
|---|---|
| Telegram ID ↔ hisob raqam bog'lanishi | Abonent F.I.O, telefoni, manzili |
| Holatlar va vaqtlar (tasdiqlangan, rad etilgan…) | Balans, qarzdorlik |
| Hudud raqami | Inspektorlar ro'yxati ma'lumotlari |
| Rasmlarning Telegram `file_id`lari | KPI ma'lumotlari |
| Audit log (qisman yashirilgan) | |

- Abonent ma'lumotlari admin tayyorlagan Excel fayllardan **import papkasi** orqali RAM'ga yuklanadi (J7).
  Bot fayllardan nusxa olmaydi.
- Telefon raqami tekshirilgandan keyin bazaga faqat "tasdiqlangan" belgisi va vaqti yoziladi, raqamning o'zi yozilmaydi.
- Iste'molchiga ham ma'lumotlar qisman yashirilgan holda ko'rsatiladi.
- Telefon tasdiqlangach, bot iste'molchi yuborgan kontakt xabarini chatdan o'chiradi.
- Xodimlar to'liq ma'lumotni ochgan har bir holat audit logga yoziladi.
- Inspektor faqat o'z hududini ko'radi. Istisno — 5-jarayon (J5) bo'yicha boshqa hududdan olingan vazifa:
  bunda u faqat vazifadagi iste'molchini va faqat vazifa yopilguncha ko'radi.
- Loglarga ism, telefon va manzil yozilmaydi, tokenlar avtomatik yashiriladi.
- Bazada shaxsiy ma'lumot bo'lmagani uchun backup ham shaxsiy ma'lumotsiz bo'ladi.
- Ma'lumotlarni O'zbekiston hududida saqlash talabi tashkilot yuristi bilan aniqlashtiriladi.

## 3. Bosh sahifa (ro'yxatdan o'tmagan foydalanuvchi)

1. Start bosilishidan oldin bot haqida qisqa ma'lumot ko'rinadi. Bu Telegram bot tavsifi (description),
   3 tilda yoziladi; Telegram ilova tiliga qarab kerakli variantni o'zi tanlaydi.
2. Telegram "Start" tugmasi bosilgach: ikki tilda qisqa salom va til tanlash tugmalari bitta xabarda chiqadi.
3. Til tanlangach: shu tilda bot haqida batafsil ma'lumot va ro'yxatdan o'tish uchun nima kerakligi
   (hisob raqam — kvitansiyada bor, abonentda ro'yxatdan o'tgan telefon).
4. Menyu:
   ```
   [ 📝 Ro'yxatdan o'tish ]
   [ ❓ Yordam ] [ ⚙️ Sozlamalar ] [ ☎️ Aloqa ]
   ```
- **Yordam** — mavzular bo'yicha qo'llanma: ro'yxatdan o'tish, hisob raqamni qayerdan topish,
  ko'rsatkich yuborish, balans, savol-javob. Har bir mavzu alohida xabar, kerakli joyda rasm bilan.
  Ro'yxatdan o'tmagan foydalanuvchiga faqat ro'yxatdan o'tishga oid mavzular ko'rsatiladi.
- **Sozlamalar** — til.
- **Aloqa** — idora telefoni, manzili, xaritadagi joylashuvi, ish vaqti.
- Tanlangan til eslab qolinadi: faqat Telegram ID va til saqlanadi.
- Ro'yxatdan o'tgan foydalanuvchi va xodimlar `/start` bossa, to'g'ridan-to'g'ri o'z paneliga o'tadi.

## 4. Rollar

### 4.1. Iste'molchi
- Panelga kirganda va hisob raqam almashtirilganda **ma'lumot kartochkasi** chiqadi: tanlangan hisob raqam,
  qisman yashirilgan ma'lumotlar, "Bu oy ko'rsatkich: yuborilgan ✅ / yuborilmagan ⏳".
- Klaviatura:
  ```
  [ 📸 Ko'rsatkich yuborish ]
  [ 💰 Balans ] [ 🔢 Hisob raqamlarim ]
  [ 👷 Hudud inspektori ] [ ☎️ Aloqa ]
  [ ⚙️ Sozlamalar ]
  ```
- **Hisob raqamlarim:** hisob raqam qo'shish, almashtirish, hisobni uzish.
- **Aloqa:** idora kontaktlari va murojaat yuborish (J3).
- **Sozlamalar:** til va yordam.

### 4.2. Operator (5 ta)
- Admin taklif havolasi (24 soat) yoki Telegram ID orqali qo'shadi. Operator tilni o'zi tanlaydi.
- Telefoni Excel bilan mos kelmagan ro'yxatdan o'tish so'rovlarini ko'rib chiqadi (J1).
- Ko'rsatkichlarni **navbat** orqali ko'rib chiqadi (J2).
- Inspektorlarga vazifa yuboradi (J5).
- **Har bir operatorga alohida ruxsatlar** beriladi, masalan murojaatlarga javob berish yoki ommaviy xabar
  yuborish (1–2 operator). Qo'shimcha vazifalar keyin qo'shiladi.

### 4.3. Inspektor (60 hudud, 59 shtat, hozir 58 inspektor)
- Ro'yxat va shaxsiy havola orqali ulanadi (J10). **Bitta inspektor — bitta hudud.** Hududni faqat admin
  o'zgartiradi, operatorda bu huquq yo'q.
- `📊 Mening KPI'm`, reyting (J8), vazifalar (J5), o'z hududi bo'yicha iste'molchilarni qidirish, live lokatsiya (J6),
  `⚙️ Sozlamalar → 🌐 Til`.

### 4.4. Admin (asosiy admin — bitta)
- Barcha huquqlarga ega. **Arizalar va ko'rsatkichlar unga yuborilmaydi**, u kerak bo'lganda o'zi kirib ko'radi:
  qabul qiladi, nazorat qiladi, o'zgartiradi, o'chiradi.
- Avtomatik keladigan xabarlar faqat quyidagilar:
  - tizim xatolari va bot ishga tushgani;
  - xavfsizlik hodisalari;
  - lokatsiya yubormaganlar ro'yxati;
  - unga yo'naltirilgan va muddati o'tgan vazifalar;
  - 24 soat javobsiz qolgan murojaatlar;
  - kunlik xulosa.
- Vazifani **istalgan hududdagi istalgan inspektorga** biriktira oladi. Bu huquq faqat adminda bor.
- Ma'lumot yangilaydi (J7), KPI'ni e'lon qiladi (J8), ommaviy xabar yuboradi (J9), xodimlarni boshqaradi (J10).
- "Yangilanish" deganda faqat ma'lumot yangilanishi tushuniladi. Bot kodi bot orqali yangilanmaydi.
- Adminlarning Telegram akkauntida ikki bosqichli tasdiqlash (cloud parol) majburiy.

### 4.5. Zaxira akkauntlar (1–2 ta)
J11 ga qarang.

### 4.6. Rahbariyat (boshliq, o'rinbosar)
Keyinroq alohida rol sifatida qo'shiladi.

## 5. Jarayonlar

### J1. Ro'yxatdan o'tish
```
Iste'molchi: hisob raqam + kontakt ──▶ Bot: telefon Excel'ga mosmi?
   ├─ ha  ──▶ avtomatik ulanadi ──▶ panel
   └─ yo'q ──▶ "So'rovingiz operatorga yuborildi" ──▶ Operator navbati ──▶ ✅ / ❌ + sabab ──▶ Iste'molchi
```
- Hisob raqam kiritish urinishlari cheklanadi.
- Faqat foydalanuvchining o'z kontakti qabul qilinadi.
- Rad etish sababi tayyor ro'yxatdan tanlanadi va iste'molchiga uning tilida ko'rsatiladi.

### J2. Ko'rsatkich yuborish
```
Iste'molchi: rasm ──▶ Operator navbati (takroriy rasm bo'lsa ⚠️)
Operator ✅ ──▶ Hisobot kanali (hisob raqam + hudud + rasm) + Iste'molchi: "qabul qilindi"
Operator ❌ + sabab ──▶ Iste'molchi: sabab + "qayta yuborishingiz mumkin"
Operator ──(shubhali bo'lsa)──▶ J5
```
- Rasm soni va hajmi cheklanadi. Takroriy rasm SHA-256 orqali aniqlanadi.
- **Navbat:** operator `📸 Keyingi ariza (N)` tugmasini bosadi va bitta arizani oladi; ariza unga biriktiriladi.
- **Hisobot kanaliga faqat tasdiqlangan** rasmlar tushadi.
- Rad etilgan ko'rsatkichni qayta yuborish **oyiga 3 martagacha**. 3-rad etishdan keyin iste'molchiga
  "inspektor siz bilan bog'lanadi" degan xabar boradi, operatorga esa inspektorga vazifa yuborish taklif qilinadi.

### J3. Murojaat
```
Iste'molchi: Aloqa → Savol yuborish ──▶ ruxsati bor operator(lar) ──▶ javob ──▶ Iste'molchi
(admin ham javob bera oladi)
```
- Matn va ixtiyoriy rasm. Kuniga eng ko'pi 3 ta yangi murojaat.
- Holatlar: yangi → javob berildi → yopildi. Iste'molchi suhbatni davom ettira oladi.
- Murojaatni operator yopadi yoki iste'molchi 3 kun yozmasa, u avtomatik yopiladi. Keyin yozilgan xabar yangi murojaat ochadi.
- 24 soat ichida javob berilmasa, adminga eslatma boradi.

### J4. Hudud inspektori
- Inspektor bor bo'lsa — F.I.O va **xizmat telefoni**. U inspektorlar ro'yxatidagi alohida ustundan olinadi.
- Hudud vakant bo'lsa — idora telefoni.

### J5. Inspektorga vazifa
```
Operator: vazifa (hisob raqam, sabab, muddat)
   ├─ hududda inspektor bor ──▶ o'sha inspektor
   └─ vakant hudud ──▶ operator tanlagan inspektor YOKI admin
Admin: istalgan inspektorga, istalgan hududdan
Inspektor: ✅ Qabul qildim ──▶ joyga boradi ──▶ natija (izoh + rasm + 15 daqiqalik live lokatsiya) ──▶ Operator
Operator (yoki admin): vazifani yopadi
```
- Sabab tayyor ro'yxatdan tanlanadi va izoh qo'shiladi.
- Holatlar: yangi → qabul qilindi → bajarildi → yopildi.
- Muddati o'tsa, eslatma operatorga ham, adminga ham boradi.
- Natijadagi lokatsiya **live** bo'lishi shart: bir martalik lokatsiyani xaritadan qo'lda tanlash mumkin,
  shuning uchun u joyga borilganini isbotlamaydi.

### J6. Live lokatsiya nazorati
```
Admin: 📡 buyruq ──▶ barcha inspektorlar
Inspektor: live lokatsiya (kamida 1 soat) ──▶ tashkilotning asosiy guruhi
   +10 daq: yubormaganlarga ogohlantirish
   +5 daq:  yubormaganlar ro'yxati ──▶ faqat Admin
```
- Bir martalik lokatsiya qabul qilinmaydi.
- Bot asosiy guruhda a'zo bo'lishi va xabar yozish huquqiga ega bo'lishi kerak.
  Guruh a'zolari inspektorlar joylashuvini ko'radi; inspektorlar bundan xabardor qilinadi.

### J7. Ma'lumot yangilash
```
Admin: Excel ──▶ import papka (belgilangan nomlar) ──▶ botda 🔄 Ma'lumotlarni yangilash
   ──▶ tekshiruv hisoboti (qatorlar, xatolar, o'zgarishlar) ──▶ ✅ Tasdiqlash ──▶ RAM
Bot qayta ishga tushsa ──▶ papkadan avtomatik yuklaydi ──▶ adminga xabar
```
- Import papkasi `.env` da qat'iy belgilanadi. **Botga fayl yo'lini yozib bo'lmaydi.**
- O'zgarishlar hisoboti (yangi, olib tashlangan, o'zgargan qatorlar) faqat adminga ko'rsatiladi.
- Faylda xato bo'lsa, yangilash rad etiladi va bot eski ma'lumot bilan ishlashda davom etadi.
- Bu usul bot shu kompyuterda ishlagandagina ishlaydi. Serverga ko'chilganda fayl yuklash imkoniyati qo'shiladi.

### J8. KPI va reyting
- Ko'rsatkichlar:
  - **tushum:** reja / bajarildi / qoldiq / %;
  - **xatlov:** reja / bajarildi / qoldiq / %, shuningdek 60% va 80% gacha qolgan son;
  - **kunlik me'yor:** qoldiq ÷ qolgan ish kunlari.
- 60% va 80% chegaralarini admin sozlaydi.
- **Reyting:** ko'rsatkichlar rejaga nisbatan foizda hisoblanadi va ulushlar bilan bitta umumiy ballga birlashtiriladi.
  Har bir ko'rsatkich uchun yuqori chegara bor (masalan 120%). Ulushlarni admin sozlaydi.
- Kunlik va oylik reyting bo'ladi. Admin tasdiqlagach har bir inspektorga yuboriladi: o'z KPI'si, top-5 va o'z o'rni (masalan 23/58).
- `📊 Mening KPI'm` tugmasi **admin tasdiqlagan oxirgi** ma'lumotni ko'rsatadi.

### J9. Ommaviy xabarlar
- **Turlari:**
  - qarzdorlarga ogohlantirish;
  - ko'rsatkich yubormaganlarga ogohlantirish;
  - yangilik yoki e'lon (hammaga yoki hudud bo'yicha).
- **Bosqichli chegaralar va har bir bosqich uchun alohida matn** (summa va sana bo'yicha) — admin sozlaydi.
- **Bot faqat tayyorlaydi:** qabul qiluvchilarni tanlaydi va matnni shakllantiradi. **Admin yoki ruxsati bor
  1–2 operator tasdiqlamaguncha hech narsa yuborilmaydi.**
- **Tasdiqlash oynasida:**
  - qabul qiluvchilar soni;
  - 3 tildagi oldindan ko'rinish;
  - ma'lumot qachon yangilangani (eskirgan bo'lsa ogohlantirish).
- Bitta odamga takroriy yuborish cheklanadi.
- Yuborishni to'xtatish tugmasi bor. Bot qayta ishga tushsa, yuborish to'xtagan joyidan davom etadi.
- Yuborish natijasi ko'rsatiladi: yuborildi / yetkazilmadi.
- Kim tasdiqlab yuborgani audit logga yoziladi.

### J10. Xodim qo'shish
- **Operator:** bir martalik havola (24 soat) → til → panel. So'ng admin operatorga ruxsatlar beradi.
- **Inspektor:** ro'yxat (F.I.O, hudud, xizmat telefoni) import papka orqali yuklanadi → har bir qator uchun
  shaxsiy havola (72 soat). Havolalar Excel faylga chiqariladi → inspektor havolani bosadi va
  "Siz N-hudud inspektori F.I.O." degan yozuvni tasdiqlaydi → til → panel.
- Adminda har bir havolaning holati ko'rinadi (ishlatilgan / kutilmoqda), havolani qayta yaratish mumkin.
  Havolalar tarqatilgach, faylni o'chirish tavsiya etiladi.
- Xodimni uzish: kirish huquqi darhol yopiladi.

### J11. Favqulodda huquqlarni bekor qilish
```
Zaxira akkaunt: maxfiy so'z ──▶ bot xabarni o'chiradi ──▶ huquqli akkauntlar ro'yxati
   ──▶ tanlash ──▶ ✅ ──▶ huquqlar bekor + hisobot kanali va asosiy guruhdan chiqarish
   ──▶ boshqa zaxira akkauntlarga xabar
```
- **Zaxira akkauntlar ro'yxati va maxfiy so'zning xeshi faqat `.env` faylida** turadi, bot orqali o'zgartirilmaydi.
- Maxfiy so'z faqat zaxira akkauntlardan ishlaydi. Begona akkaunt uni yozsa, bot oddiy noma'lum matn sifatida qabul qiladi.
- Noto'g'ri urinishlar cheklanadi va har biri haqida boshqa zaxira akkauntlarga xabar boradi.
- Asosiy admin bekor qilingach, zaxira akkaunt vaqtincha admin huquqlarini oladi va yangi asosiy adminni tayinlaydi.
- Bot hisobot kanali va asosiy guruhda "foydalanuvchilarni bloklash" huquqiga ega admin bo'lishi kerak.
- **Kanal va guruh egaligi** kamdan-kam ishlatiladigan zaxira akkauntga o'tkaziladi, chunki egani hech kim chiqara olmaydi.
- Begona seanslarni Telegram'ning "Qurilmalar" bo'limida qo'lda yopish kerak bo'ladi.

### J12. Nazorat
- **Audit log:** kim, qachon, nima qildi, tafsilot. Ma'lumotlar qisman yashiriladi. Ko'rish huquqi faqat adminda.
- **1 yil saqlanadi.** Keyin yozuvlar kompyuterdagi arxiv papkasiga nazorat summasi bilan **avtomatik ko'chiriladi**.
  Admin istalgan paytda qo'lda ham arxivlay oladi.
- **Botda yozuvni o'chirish yo'q**, faqat arxivlash bor. Arxiv faylini o'chirish faqat kompyuterda, qo'lda bajariladi.
- **Admin panelida:**
  - operatorlar hisoboti (ko'rib chiqilgan so'rov, ko'rsatkich, murojaat, vazifalar soni; o'rtacha javob vaqti);
  - audit logdan qidirish;
  - arxivlash.
- **Kunlik xulosa** har kuni ertalab (vaqtni admin sozlaydi) avtomatik keladi.

## 6. Admin sozlaydigan parametrlar (boshlang'ich qiymatlar)

| Parametr | Qiymat |
|---|---|
| Hisob raqam kiritish urinishlari | soatiga 5 |
| Bitta ko'rsatkichdagi rasm soni / hajmi | 10 ta / 10 MB |
| Rad etilgandan keyin qayta yuborish | oyiga 3 marta |
| Kunlik murojaatlar | 3 ta |
| Murojaatni avtomatik yopish | 3 kun |
| Javobsiz murojaat bo'yicha eslatma | 24 soat |
| Vazifa natijasidagi live lokatsiya | 15 daqiqa |
| J6 live lokatsiya / ogohlantirish / ro'yxat | ≥1 soat / 10 daq / +5 daq |
| Operator / inspektor havolasining amal qilish muddati | 24 soat / 72 soat |
| KPI chegaralari | 60%, 80% |
| Reyting: ko'rsatkich yuqori chegarasi | 120% |
| Audit log saqlash | 1 yil |
| Kunlik xulosa vaqti | 08:00 |

## 7. Ochiq savollar

1. Operator uchun abonent qidirish.
2. Operatorlarning qo'shimcha vazifalari.
3. KPI ma'lumot manbai va fayl tuzilmasi.
4. Reyting ball ulushlari.
5. ~~Murojaatga javob turi~~ — yopildi: avval erkin matn, keyinroq tayyor javob shablonlari.
6. Excel fayllar ro'yxati va ularning ustunlari.
7. Rahbariyat roli.
8. Qo'llanma matnlarini kim yozadi.
