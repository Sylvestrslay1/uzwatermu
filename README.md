# uzwatermu Telegram bot

Mirzo Ulug'bek tuman abonentlari uchun hisoblagich ko'rsatgichlarini qabul qilish Telegram boti.

## Imkoniyatlar

- Kirishda o'zbek va rus tillarida salomlashish.
- `Start` tugmasidan keyin o'zbek lotin, o'zbek kirill va rus tilini tanlash.
- Hisob raqamni Excel jadvalidan tekshirish.
- Shaxsiy kabinet: hisob raqam, F.I.O, telefon, manzil, inspektor F.I.O va telefoni.
- Telefon raqamni tahrirlash.
- Hisoblagich rasmlarini qabul qilish va kanalga caption bilan yuborish.
- Qabul qilingan rasmlar soni bo'yicha hisoblagichlar sonini ko'rsatish.
- Keyingi yuborish sanasini 30 kalendar kundan keyinga hisoblash.
- Balansni Excel ma'lumotlari bo'yicha ko'rsatish.
- Texnik xizmat menyusi: tilni o'zgartirish, yo'riqnoma, tuman manzili va geolokatsiya.
- Texnik xizmat ichida aloqa markazi telefonlari, manzil va geolokatsiya.
- Admin/operator amallari bo'yicha audit log.
- Excel yuklashdan oldin tekshiruv va admin tasdiqlovi.
- Ommaviy xabarlarni Telegram limitiga mos sekin yuborish.
- SQLite va Excel fayllar uchun backup tizimi.

## Excel ustunlari

Bot `data/abonents.xlsx` faylidan iste'molchilarni, `data/inspectors.xlsx` faylidan inspektorlarni o'qiydi.

`abonents.xlsx` birinchi qatorda ustun nomlari bo'lishi kerak:

```text
hisob raqam
fio
telefon
manzil
hudud
inspektor fio
inspektor telefon
oxirgi ko'rsatgich
ko'rsatgich sana
balans
yuklangan sana
```

`inspectors.xlsx` birinchi qatorda ustun nomlari bo'lishi kerak:

```text
hudud
inspektor fio
inspektor telefon
```

`hisob raqam` majburiy. `hudud` qiymati ikkala faylda bir xil yozilishi kerak, masalan `3-hudud`. Agar hudud bo'yicha inspektor topilmasa, bot `Vakant. 71-262-55-81 raqamiga murojaat qiling.` deb chiqaradi.

## O'rnatish

1. Python 3.11 yoki yangiroq versiyasini o'rnating.
2. Kutubxonalarni o'rnating:

```powershell
pip install -r requirements.txt
```

3. `.env.example` faylidan `.env` nusxa yarating va qiymatlarni to'ldiring:

```powershell
Copy-Item .env.example .env
```

4. BotFather orqali bot yarating. Bot username uchun `uzwatermu` band bo'lmasa shuni tanlang. BotFather bergan tokenni `.env` ichidagi `BOT_TOKEN` ga yozing.
5. Telegram kanal yarating, botni kanalga admin qiling va kanal ID sini `REPORT_CHANNEL_ID` ga yozing.
6. Aloqa markazi ma'lumotlarini `.env` ichida to'ldiring:

```env
CONTACT_PHONES=71-262-55-81
DISTRICT_ADDRESS=Mirzo Ulug'bek tuman Abonentlar bo'limi manzili
DISTRICT_LAT=41.3260
DISTRICT_LON=69.3340
```

7. Excel shablon yaratish:

```powershell
python create_excel_template.py
```

8. Botni ishga tushirish:

```powershell
python -m bot.main
```

## Admin panel

Bot ichida admin panel bor. Avval Telegram'da botga quyidagini yuboring:

```text
/myid
```

Bot sizga Telegram ID qaytaradi. Shu raqamni `.env` ichidagi `ADMIN_IDS` qatoriga yozing:

```env
ADMIN_IDS=123456789
```

Bir nechta admin bo'lsa vergul bilan yoziladi:

```env
ADMIN_IDS=123456789,987654321
```

Keyin botni qayta ishga tushiring va Telegram'da:

```text
/admin
```

Admin menyu ichki bo'limlarga ajratilgan:

```text
📁 Excel
🔎 Abonentlar
📋 Arizalar
👥 Operatorlar
📢 Xabarlar
📊 Hisobotlar
👷 Inspektorlar
🧹 Xizmat
```

### Super admin va operatorlar

`.env` ichidagi `ADMIN_IDS` super adminlar ro'yxati hisoblanadi. Super admin barcha operator funksiyalaridan foydalanadi va operatorlarni boshqaradi.

Super admin panelida barcha bo'limlar ko'rinadi. Operatorlarni boshqarish `👥 Operatorlar` bo'limida:

```text
👨‍💼 Operator qo'shish
👥 Operatorlar ro'yxati
🗑 Operator o'chirish
🧹 Test ma'lumotlarni tozalash
```

Operator qo'shish uchun super admin `👨‍💼 Operator qo'shish` tugmasini bosadi va operatorning Telegram ID raqamini kiritadi. Operator botga `/start` bosib kiradi, til tanlaydi va operator panelga o'tadi.

Operator panelida quyidagi bo'limlar ko'rinadi:

```text
📁 Excel
🔎 Abonentlar
📋 Arizalar
```

`🧹 Test ma'lumotlarni tozalash` faqat super admin uchun. U iste'molchilar va arizalar bazasini tozalaydi, operatorlar ro'yxati esa saqlanib qoladi.

### Qarzdorlik ogohlantirishi

Bot tasdiqlangan foydalanuvchilarni Excel fayldagi debitor qarzdorlik bo'yicha tekshiradi. Avtomatik tekshiruv oy kalendari bo'yicha 1, 5, 10, 15, 20, 25, 30-sanalarida ishlaydi.

`🔴 Qarzdorlik tahlili` tugmasi faqat tekshiradi va ogohlantirish yubormaydi. Xabar yuborish uchun super admin alohida `📨 Qarzdorlarga ogohlantirish yuborish` tugmasini bosadi va tasdiqlaydi.

Ogohlantirish matnlari alohida faylda saqlanadi:

```text
bot/debt_texts.py
```

Imloviy tuzatish kerak bo'lsa, shu fayldagi `DEBT_WARNING_TEXTS` ichidagi matnlarni o'zgartiring. `{statement_date}` va `{debit}` joylarini o'chirmang.

### Excel yuklash xavfsizligi

Admin/operator Excel fayl yuklaganda bot uni darhol eski fayl ustiga yozmaydi. Avval vaqtinchalik `work/uploads` papkasiga saqlaydi, tekshiradi va hisobot chiqaradi. Admin `✅ Excelni almashtirish` tugmasini bosgandan keyingina eski fayl backup qilinadi va yangi Excel asosiy faylga almashtiriladi.

Excel sifat nazoratida quyidagilar ham tekshiriladi:

```text
dublikat hisob raqamlar
bo'sh F.I.O qatorlar
noto'g'ri telefon formatlari
noto'g'ri debitor/kreditor summa formatlari
hududsiz qatorlar
inspektor mos kelmagan qatorlar
```

### Audit log va backup

Super admin `🧹 Xizmat` bo'limida `📜 Audit loglar` va `💾 Backup yaratish` tugmalarini ko'radi.

Audit logda kim qachon foydalanuvchini tasdiqlagani, operator qo'shgani/o'chirgani, Excel almashtirgani, qarzdorlik ogohlantirishi yoki broadcast yuborgani saqlanadi.

Backup `BACKUP_DIR` papkasiga yoziladi. Standart qiymat:

```env
BACKUP_DIR=backups
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=30
BACKUP_KEEP_SETS=30
```

Bot ishga tushganda avtomatik backup xizmati ham ishga tushadi. Har bir backup
alohida papkada SQLite baza, abonentlar Excel fayli, inspektorlar Excel fayli
va SHA-256 nazorat summalari yozilgan `manifest.json` bilan saqlanadi.

Super admin `Xizmat` bo'limida backup yaratishi, ro'yxatni ko'rishi va oxirgi
sog'lom backupni ikki bosqichli tasdiqlash orqali tiklashi mumkin. Tiklashdan
oldin joriy holatning xavfsizlik nusxasi avtomatik yaratiladi.

### AES-256 ma'lumot shifrlash

Backup, eksport va xatolik loglarini AES-256-GCM bilan shifrlash uchun:

```env
ENCRYPTION_ENABLED=true
```

`UZWATER_ENCRYPTION_PASSWORD` qiymatini `.env` ichiga yozish taqiqlangan.
Uni PyCharm Run Configuration yoki server secret manager orqali environment
variable sifatida bering. Parol kamida 16 belgidan iborat bo'lishi kerak.

Mavjud ma'lumotlarning shifrlangan, o'zgartirilmaydigan snapshotini yaratish:

```powershell
py -3.14 -m tools.encrypt_data_snapshot
```

Vosita parolni terminalda yashirin so'raydi. Natija `encrypted_vault` ichida
yaratiladi. Asl fayllar avtomatik o'chirilmaydi.

Eslatma: ishlayotgan SQLite baza va Excel fayllarini to'liq disk darajasida
himoyalash uchun server diskida Windows BitLocker yoki Linux LUKS ham yoqilishi
kerak. Dasturiy shifrlash server administrator huquqi bilan ishlayotgan
hujumchidan operativ xotiradagi ochilgan ma'lumotni to'liq yashira olmaydi.

Windows ish stansiyasida faol ma'lumot papkalari EFS AES-256 bilan himoyalanishi
mumkin. EFS sertifikatini shifrlashdan oldin PFX formatida eksport qilish
majburiy. Ushbu loyiha uchun sertifikat nusxasi:

```text
secrets/uzwater_efs_certificate.PFX
```

PFX faylini va uning parolini bir joyda saqlamang. PFX nusxasini serverdan
tashqaridagi shifrlangan USB yoki tashkilotning maxfiy kalit omboriga ko'chiring.
Windows profili yo'qolsa, EFS fayllarini faqat shu PFX va uning paroli bilan
tiklash mumkin.

Bot tokeni va tashqi API kalitlarini `.env` dan Windows DPAPI omboriga ko'chirish:

```powershell
py -3.14 -m tools.migrate_env_secrets
```

DPAPI fayllari faqat ularni yaratgan Windows foydalanuvchisi ostida ochiladi.
Bot boshqa Windows hisobidan ishga tushirilsa, maxfiy kalitlar ochilmaydi.

Kalit `.env`, terminal tarixi, skrin yoki chatda ko'ringan bo'lsa, faqat
shifrlash yetarli emas: eski kalit provayderda bekor qilinib, yangisi olinadi.

Yangi Telegram bot tokenini DPAPI omboriga yozish:

```powershell
py -3.14 -m tools.update_service_secrets bot-token
```

Yangi OpenAI API kalitini DPAPI omboriga yozish:

```powershell
py -3.14 -m tools.update_service_secrets openai-key
```

### Windows avtomatik ishga tushirish

Bot Windows foydalanuvchisi tizimga kirganda yashirin supervisor orqali
avtomatik ishga tushadi. Supervisor bot yopilsa uni qayta ishga tushiradi,
process lock esa bir vaqtning o'zida ikki bot nusxasini to'sadi.

Task Scheduler vazifasini o'rnatish:

```powershell
powershell -File tools\install_startup_task.ps1
```

Vazifani olib tashlash:

```powershell
powershell -File tools\uninstall_startup_task.ps1
```

Supervisor logi `logs/supervisor.log`, bot heartbeat holati esa
`logs/health.json` ichida saqlanadi.

Kod yangilangandan keyin yangi kodni HMAC bilan muhrlang:

```powershell
py -3.14 -m tools.seal_code_integrity
```

Windows papka ruxsatlarini faqat joriy foydalanuvchi, `SYSTEM` va
administratorlarga cheklash:

```powershell
powershell -File tools\harden_windows_acl.ps1
```

### Preflight va integrity monitoring

Bot ishga tushishidan oldin SQLite baza, abonentlar Excel fayli, inspektorlar
Excel fayli, oxirgi sog'lom backup va disk bo'sh joyi tekshiriladi.

```env
HEALTH_CHECK_INTERVAL_HOURS=6
BACKUP_MAXIMUM_AGE_HOURS=48
MINIMUM_DISK_FREE_GB=2
MINIMUM_DISK_FREE_PERCENT=5
```

SQLite yoki majburiy Excel fayli yo'qolgan/buzilgan bo'lsa bot yangi bo'sh baza
yaratmaydi va xavfli holatda ishga tushmaydi. Backup eskirgan yoki disk joyi
kamaygan bo'lsa bot ishlashda davom etadi, lekin adminga ogohlantirish yuboradi.

Integrity hisoboti `logs/preflight.json` ichida saqlanadi va admin paneldagi
`Tizim holati` bo'limida ko'rsatiladi. Tekshiruv har 6 soatda takrorlanadi;
holat o'zgarmasa takroriy xabar yuborilmaydi.

### Flood va resurs himoyasi

Bot barcha xabar, buyruq va admin callbacklarini rate limit orqali o'tkazadi.
Oddiy foydalanuvchi va xodimlar uchun alohida chegaralar mavjud:

```env
REQUEST_WINDOW_SECONDS=10
USER_REQUEST_LIMIT=15
STAFF_REQUEST_LIMIT=60
FLOOD_BLOCK_SECONDS=60
MAX_EXCEL_UPLOAD_MB=25
MAX_METER_PHOTO_MB=10
MAX_METER_PHOTOS=10
```

Limitdan oshgan profil vaqtincha bloklanadi va hodisa auditga yoziladi. Takroriy
bloklangan so'rovlar admin kanaliga ortiqcha xabar yubormaydi. Excel hajmi
Telegram serveridan yuklab olinishidan oldin tekshiriladi. Bir ko'rsatgich
topshirishda rasm soni va har bir rasm hajmi ham cheklangan.

Faol va jami flood bloklari, Excel va foto chegaralari admin paneldagi
`Tizim holati` bo'limida ko'rsatiladi.

### Hisobotlar bo'limi

Super admin uchun `📊 Hisobotlar` bo'limida quyidagi eksportlar bor:

```text
📤 Audit eksport
📤 Foydalanuvchilar eksport
📤 Qarzdorlar eksport
📤 Arizalar eksport
📤 Ogohlantirishlar eksport
```

Eksportlar CSV formatda `outputs` papkasiga yaratiladi va Telegram orqali admin chatiga yuboriladi.

### Ogohlantirish va ariza tarixi

Qarzdorlik ogohlantirishlari alohida tarixga yoziladi:

```text
kimga yuborildi
hisob raqam
qarzdorlik summasi
foydalanuvchi tili
Excel sanasi
yuborildi / o'tkazildi / xato
```

Hisoblagich arizalarida endi rasm soni bilan birga foydalanuvchi tili, inspektor va status ham saqlanadi.

### Inspektor live lokatsiya nazorati

`👷 Inspektorlar` bo'limida inspektor Telegram ID bo'yicha botga ulanadi:

```text
Telegram ID
hudud
F.I.O
telefon
status
```

Ulangan inspektor `/start` bosganda alohida inspektor paneliga kiradi.

Super admin `📡 Live lokatsiya buyrug'i` tugmasini bosganda:

1. Barcha faol inspektorlarga kamida 1 soatlik live lokatsiyani yoqish buyrug'i yuboriladi.
2. Oddiy statik lokatsiya yoki 1 soatdan qisqa live lokatsiya qabul qilinmaydi.
3. 10 daqiqada bajarmagan inspektorlarga avtomatik ogohlantirish yuboriladi.
4. Ogohlantirishdan keyin yana 10 daqiqa beriladi.
5. Yakuniy muddatda bajarmagan inspektorlar F.I.O, hudud, telefon va Telegram profil havolasi bilan super adminlarga yuboriladi.
6. Qabul qilingan live lokatsiya adminlarga uzatiladi va inspektor harakatlanganda xaritadagi nuqta yangilanadi.

Telegram xavfsizlik qoidalariga ko'ra bot inspektor telefonida geolokatsiyani o'zi yoqa olmaydi. Inspektor Telegramdagi `Location → Share My Live Location` amalini shaxsan tasdiqlashi shart.

## Operator tasdiqlovi

Yangi foydalanuvchi hisob raqamini kiritgandan keyin bot darhol asosiy menyuni ochmaydi. Ulanish so'rovi `ADMIN_IDS` ichida ko'rsatilgan admin/operatorlarga yuboriladi.

Admin/operator xabar ichidagi tugmalardan birini bosadi:

```text
✅ Tasdiqlash
❌ Rad etish
```

Tasdiqlansa, foydalanuvchiga asosiy menyu ochiladi. Rad etilsa, foydalanuvchiga tuman abonentlar bo'limiga murojaat qilish kerakligi haqida xabar boradi.

### Uch tilda xabar yuborish

`📢 Xabar yuborish` tugmasi admin matnlarni 3 tilda ketma-ket kiritishini so'raydi:

```text
uz      -> o'zbek lotin
uz_cyrl -> o'zbek kirill
ru      -> rus tili
```

Keyin preview ko'rsatadi. Admin `✅ Yuborish` tugmasini bosgandan so'ng har bir foydalanuvchiga uning tanlagan tili bo'yicha xabar boradi. Bu rejim bepul ishlaydi va OpenAI API key talab qilmaydi.

Ommaviy yuborishda bot har xabardan keyin kichik pauza qiladi. Pauza `.env` ichidagi `BULK_SEND_DELAY` orqali boshqariladi:

```env
BULK_SEND_DELAY=0.15
```

Telegram `Too Many Requests` cheklovi qaytsa, bot kutib qayta urinadi.

## Kanalga yuboriladigan ma'lumot

Ro'yxatdan o'tganda yoki telefon raqam tahrirlanganda kanalga quyidagi ko'rinishda xabar boradi:

```text
Hisob raqam: 100001
F.I.O: Aliyev Vali
Telefon: +998901234567
Inspektor: Karimov Akmal
```

Hisoblagich rasmi yuborilganda rasm kanalga tushadi va caption ichida shu ma'lumotlar ko'rinadi.

## Eslatma

Admin panel orqali Excel almashtirilsa, botni qayta ishga tushirish shart emas: bot faylni qayta o'qiydi.

## Serverga tayyorlash

Ishlab chiqarish uchun botni PyCharm/uy kompyuterida emas, VPS/serverda ishlatish tavsiya qilinadi.

Muhim xavfsizlik qoidalari:

```text
.env faylini hech kimga yubormang.
BOT_TOKEN ni skrin qilmang.
data, storage, backups papkalarini begona odamga bermang.
Operatorlarga faqat zarur Telegram ID orqali ruxsat bering.
REPORT_CHANNEL_ID va ERROR_CHANNEL_ID kanallarida faqat mas'ul shaxslar bo'lsin.
```

## Test checklist

Botni katta tekshiruvdan o'tkazish uchun tavsiya qilinadigan tartib:

1. `/start` bosilganda salomlashuv va Start tugmasi chiqishini tekshirish.
2. O'zbek lotin, o'zbek kirill va rus tillarini alohida tanlab ko'rish.
3. Excelda yo'q hisob raqam kiritilganda qayta so'rashini tekshirish.
4. Excelda bor hisob raqam kiritilganda tasdiqlash so'rovi admin/operatorga borishini tekshirish.
5. Admin/operator `✅ Tasdiqlash` bosganda foydalanuvchiga asosiy menyu ochilishini tekshirish.
6. `❌ Rad etish` bosilganda foydalanuvchi rad etilgan xabarini olishini tekshirish.
7. Shaxsiy kabinetda F.I.O, telefon, manzil, hudud va inspektor ma'lumotlari to'g'ri chiqishini tekshirish.
8. Telefon raqam tahrirlash ishlashini va hisobot kanaliga xabar borishini tekshirish.
9. Hisoblagich rasmi yuborish: 1 ta va bir nechta rasm bilan test qilish.
10. Rasmlar hisobot kanaliga caption bilan tushishini tekshirish.
11. Balans tugmasida debitor/kreditor va Excel sanasi to'g'ri chiqishini tekshirish.
12. Texnik xizmat: aloqa markazi, ish vaqti, FAQ, tilni o'zgartirishni tekshirish.
13. Admin panel: `📊 Statistika`, `🩺 Tizim holati`, `👥 Foydalanuvchi statistikasi`ni tekshirish.
14. Excel yuklashda avval tekshiruv hisoboti, keyin `✅ Excelni almashtirish` ishlashini tekshirish.
15. Excel almashtirishdan oldin backup yaratilganini tekshirish.
16. `💾 Backup yaratish` va `📂 Backup ro'yxati` tugmalarini tekshirish.
17. `📜 Audit loglar` va `📤 Audit eksport` tugmalarini tekshirish.
18. `🔴 Qarzdorlik tahlili` faqat hisoblashini, xabar yubormasligini tekshirish.
19. `📨 Qarzdorlarga ogohlantirish yuborish` tasdiqdan keyin xabar yuborishini tekshirish.
20. `📢 Xabar yuborish` uch tilda kiritilgan matnni foydalanuvchi tiliga qarab yuborishini tekshirish.
21. Ruxsatsiz Telegram ID bilan `/admin` yozilganda rad etilishi va auditga tushishini tekshirish.
22. `logs/errors.log` fayli xatolik bo'lganda yozilishini tekshirish.
