from openpyxl import Workbook


HEADERS = [
    "Махалля",
    "Улица",
    "№ дома",
    "Кв-ра",
    "Ф.И.О. владельца",
    "Лиц.счет",
    "Сотовый тел",
    "Новый тел",
    "С водомерами или без водомера",
    "Дата послед.показ",
    "Показания",
    "Общий дебит",
    "Общий кредит",
    "Участок",
    "Инспектор",
]

EXAMPLE_ROW = [
    "Geologlar",
    "Улица Илк кадам",
    "1/3",
    "",
    "ALIYEV VALI",
    "100001",
    "901234567",
    "",
    "+",
    "21.05.2025",
    "1250",
    "155309.29",
    "0",
    "39",
    "Mirtursunov Mirolim Mirjalalovich",
]


def main() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Abonentlar"
    sheet.append(HEADERS)
    sheet.append(EXAMPLE_ROW)
    for column in sheet.columns:
        letter = column[0].column_letter
        sheet.column_dimensions[letter].width = 22
    workbook.save("data/abonents.xlsx")
    print("data/abonents.xlsx yaratildi")

    inspectors = Workbook()
    inspector_sheet = inspectors.active
    inspector_sheet.title = "Inspektorlar"
    inspector_sheet.append(["hudud", "inspektor fio", "inspektor telefon"])
    inspector_sheet.append(["39", "Mirtursunov Mirolim Mirjalalovich", "+998901112233"])
    for column in inspector_sheet.columns:
        letter = column[0].column_letter
        inspector_sheet.column_dimensions[letter].width = 28
    inspectors.save("data/inspectors.xlsx")
    print("data/inspectors.xlsx yaratildi")


if __name__ == "__main__":
    main()
