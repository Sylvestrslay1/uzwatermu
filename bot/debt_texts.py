from __future__ import annotations


DEBT_WARNING_TEXTS = {
    "uz": (
        "🔴 QARZDORLIK BO'YICHA OGOHLANTIRISH\n\n"
        "🔢 Hisob raqami: {account}\n"
        "📅 Ma'lumot sanasi: {statement_date}\n"
        "💰 Debitor qarzdorlik: {debit} so'm\n\n"
        "Suv ta'minoti va suv chiqarish xizmatlarini ko'rsatish sohasida "
        "to'lov intizomini tubdan takomillashtirish chora-tadbirlari "
        "to'g'risidagi 2017-yil 16-noyabrdagi PF-5241-son Farmonga ko'ra, "
        "barcha guruh iste'molchilariga suv ta'minoti va suv chiqarish "
        "xizmatlari 100 foizlik oldindan haq to'lash asosida ko'rsatiladi.\n\n"
        "Oldindan haq to'lanmagan taqdirda, iste'molchini suv ta'minoti va "
        "suv chiqarish tizimidan belgilangan tartibda to'liq uzishgacha "
        "bo'lgan choralar ko'rilishi mumkin. Qarzdorlik o'z vaqtida "
        "to'lanmasa, ma'lumotlaringiz Mirzo Ulug'bek tumani Majburiy ijro "
        "byurosiga taqdim etilishi va Mirzo Ulug'bek tumanlararo sudiga "
        "murojaat qilinishi mumkinligi haqida ogohlantiramiz.\n\n"
        "ESLATMA: Suv ta'minoti va suv chiqarish tizimidan ilgari uzilgan "
        "shaxslarni qayta ulashda II guruh iste'molchilaridan bazaviy "
        "hisoblash miqdorining ikki baravari miqdorida to'lov undiriladi. "
        "Mablag' qayta ulashni amalga oshirgan tashkilotning hisob raqamiga "
        "o'tkaziladi.\n\n"
        "Ichimlik suv va oqova suv xizmatlari uchun to'lovlarni o'z vaqtida "
        "amalga oshirishni unutmang!\n\n"
        "Qarzdorlik bo'yicha e'tirozingiz bo'lsa, Mirzo Ulug'bek tuman "
        "Abonentlar bo'limiga murojaat qiling."
    ),
    "uz_cyrl": (
        "🔴 ҚАРЗДОРЛИК БЎЙИЧА ОГОҲЛАНТИРИШ\n\n"
        "🔢 Ҳисоб рақами: {account}\n"
        "📅 Маълумот санаси: {statement_date}\n"
        "💰 Дебитор қарздорлик: {debit} сўм\n\n"
        "Сув таъминоти ва сув чиқариш хизматларини кўрсатиш соҳасида тўлов "
        "интизомини тубдан такомиллаштириш чора-тадбирлари тўғрисидаги "
        "2017 йил 16 ноябрдаги ПФ-5241-сон Фармонга кўра, барча гуруҳ "
        "истеъмолчиларига сув таъминоти ва сув чиқариш хизматлари 100 фоизлик "
        "олдиндан ҳақ тўлаш асосида кўрсатилади.\n\n"
        "Олдиндан ҳақ тўланмаган тақдирда, истеъмолчини сув таъминоти ва сув "
        "чиқариш тизимидан белгиланган тартибда тўлиқ узишгача бўлган чоралар "
        "кўрилиши мумкин. Қарздорлик ўз вақтида тўланмаса, маълумотларингиз "
        "Мирзо Улуғбек тумани Мажбурий ижро бюросига тақдим этилиши ва Мирзо "
        "Улуғбек туманлараро судига мурожаат қилиниши мумкинлиги ҳақида "
        "огоҳлантирамиз.\n\n"
        "ЭСЛАТМА: Сув таъминоти ва сув чиқариш тизимидан илгари узилган "
        "шахсларни қайта улашда II гуруҳ истеъмолчиларидан базавий ҳисоблаш "
        "миқдорининг икки баравари миқдорида тўлов ундирилади. Маблағ қайта "
        "улашни амалга оширган ташкилотнинг ҳисоб рақамига ўтказилади.\n\n"
        "Ичимлик сув ва оқова сув хизматлари учун тўловларни ўз вақтида "
        "амалга оширишни унутманг!\n\n"
        "Қарздорлик бўйича эътирозингиз бўлса, Мирзо Улуғбек туман "
        "Абонентлар бўлимига мурожаат қилинг."
    ),
    "ru": (
        "🔴 ПРЕДУПРЕЖДЕНИЕ О ЗАДОЛЖЕННОСТИ\n\n"
        "🔢 Лицевой счёт: {account}\n"
        "📅 Дата сведений: {statement_date}\n"
        "💰 Дебиторская задолженность: {debit} сум\n\n"
        "Согласно Указу Президента Республики Узбекистан от 16 ноября "
        "2017 года № ПФ-5241 о мерах по коренному совершенствованию "
        "платёжной дисциплины в сфере оказания услуг водоснабжения и "
        "водоотведения, услуги всем группам потребителей оказываются на "
        "основе 100-процентной предварительной оплаты.\n\n"
        "При отсутствии предварительной оплаты к потребителю могут быть "
        "применены установленные меры вплоть до полного отключения от систем "
        "водоснабжения и водоотведения. В случае несвоевременной оплаты "
        "задолженности Ваши данные могут быть переданы в Бюро принудительного "
        "исполнения Мирзо-Улугбекского района, а также может быть направлено "
        "обращение в Мирзо-Улугбекский межрайонный суд.\n\n"
        "ПРИМЕЧАНИЕ: При повторном подключении лиц, ранее отключённых от "
        "систем водоснабжения и водоотведения, с потребителей II группы "
        "взимается плата в размере двух базовых расчётных величин. Средства "
        "перечисляются на расчётный счёт организации, выполнившей повторное "
        "подключение.\n\n"
        "Не забывайте своевременно оплачивать услуги питьевого водоснабжения "
        "и водоотведения!\n\n"
        "При наличии возражений по задолженности обратитесь в абонентский "
        "отдел Мирзо-Улугбекского района."
    ),
}


def debt_warning_text(
    language: str,
    debit: str,
    statement_date: str,
    account: str = "-",
) -> str:
    template = DEBT_WARNING_TEXTS.get(language) or DEBT_WARNING_TEXTS["uz"]
    return template.format(
        debit=debit,
        statement_date=statement_date,
        account=account,
    )
