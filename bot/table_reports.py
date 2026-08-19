from __future__ import annotations

import calendar
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ROW_PATTERN = re.compile(br"<row\b[^>]*\br=\"(\d+)\"[^>]*>.*?</row>", re.DOTALL)
CELL_PATTERN = re.compile(br"<c\b[^>]*?(?:/>|>.*?</c>)", re.DOTALL)
CELL_REFERENCE_PATTERN = re.compile(br"\br=\"([A-Z]+)(\d+)\"")


@dataclass(frozen=True)
class ThreeMonthReportResult:
    output_path: Path
    cutoff_date: date
    source_rows: int
    kept_rows: int
    removed_meter_rows: int
    removed_recent_rows: int


def three_month_cutoff(reference_date: date | None = None) -> date:
    current = reference_date or date.today()
    year = current.year
    month = current.month - 2
    while month <= 0:
        month += 12
        year -= 1
    previous_month = month - 1
    previous_year = year
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1
    return date(
        previous_year,
        previous_month,
        calendar.monthrange(previous_year, previous_month)[1],
    )


def excel_serial(day: date) -> int:
    return (day - date(1899, 12, 30)).days


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    path = "xl/sharedStrings.xml"
    if path not in archive.namelist():
        return []
    values: list[str] = []
    with archive.open(path) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag.rsplit("}", 1)[-1] != "si":
                continue
            values.append(
                "".join(
                    node.text or ""
                    for node in element.iter()
                    if node.tag.rsplit("}", 1)[-1] == "t"
                )
            )
            element.clear()
    return values


def _cell_bytes(row: bytes, column: str, row_number: int) -> bytes | None:
    pattern = re.compile(
        rb"<c\b[^>]*\br=\""
        + column.encode("ascii")
        + str(row_number).encode("ascii")
        + rb"\"[^>]*?(?:/>|>.*?</c>)",
        re.DOTALL,
    )
    match = pattern.search(row)
    return match.group(0) if match else None


def _cell_text(cell: bytes | None, strings: list[str]) -> str:
    if not cell:
        return ""
    inline = re.search(br"<t[^>]*>(.*?)</t>", cell, re.DOTALL)
    if inline:
        return (
            inline.group(1)
            .decode("utf-8", errors="replace")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
    value = re.search(br"<v>(.*?)</v>", cell, re.DOTALL)
    if not value:
        return ""
    raw = value.group(1).decode("utf-8", errors="replace").strip()
    if re.search(br'\bt=\"s\"', cell):
        try:
            return strings[int(raw)]
        except (ValueError, IndexError):
            return raw
    return raw


def _date_is_allowed(cell: bytes | None, cutoff_serial: int) -> bool:
    value = _cell_text(cell, [])
    if not value:
        return True
    try:
        return float(value) <= cutoff_serial
    except ValueError:
        return True


def _column_number(column: str) -> int:
    number = 0
    for character in column:
        number = number * 26 + ord(character) - 64
    return number


def _column_label(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _shift_column(column: str) -> str | None:
    number = _column_number(column)
    if number == 18:
        return None
    if number > 18:
        return _column_label(number - 1)
    return column


def _transform_row(
    row: bytes,
    old_row: int,
    new_row: int,
    old_last_data_row: int,
    new_last_data_row: int,
) -> bytes:
    transformed_cells: list[bytes] = []
    matches = list(CELL_PATTERN.finditer(row))
    if not matches:
        return re.sub(
            br'(<row\b[^>]*\br=")\d+(")',
            lambda match: match.group(1)
            + str(new_row).encode("ascii")
            + match.group(2),
            row,
            count=1,
        )

    start = matches[0].start()
    end = matches[-1].end()
    row_start = row[:start]
    row_end = row[end:]
    for match in matches:
        cell = match.group(0)
        reference = CELL_REFERENCE_PATTERN.search(cell)
        if not reference:
            transformed_cells.append(cell)
            continue
        old_column = reference.group(1).decode("ascii")
        new_column = _shift_column(old_column)
        if new_column is None:
            continue
        new_reference = f'{new_column}{new_row}'.encode("ascii")
        cell = CELL_REFERENCE_PATTERN.sub(
            b'r="' + new_reference + b'"',
            cell,
            count=1,
        )
        if new_last_data_row > 0:
            cell = cell.replace(
                str(old_last_data_row).encode("ascii"),
                str(new_last_data_row).encode("ascii"),
            )
        transformed_cells.append(cell)

    row_start = re.sub(
        br'(<row\b[^>]*\br=")\d+(")',
        lambda match: match.group(1)
        + str(new_row).encode("ascii")
        + match.group(2),
        row_start,
        count=1,
    )
    row_start = re.sub(
        br'spans="1:20"',
        b'spans="1:19"',
        row_start,
    )
    return row_start + b"".join(transformed_cells) + row_end


def _transform_columns(prefix: bytes) -> bytes:
    columns_match = re.search(br"<cols>.*?</cols>", prefix, re.DOTALL)
    if not columns_match:
        return prefix

    def transform_column(match: re.Match[bytes]) -> bytes:
        column = match.group(0)
        minimum_match = re.search(br'min="(\d+)"', column)
        maximum_match = re.search(br'max="(\d+)"', column)
        if not minimum_match or not maximum_match:
            return column
        minimum = int(minimum_match.group(1))
        maximum = int(maximum_match.group(1))
        if minimum == maximum == 18:
            return b""
        if minimum > 18:
            minimum -= 1
            if maximum < 16384:
                maximum -= 1
        column = re.sub(
            br'min="\d+"',
            f'min="{minimum}"'.encode("ascii"),
            column,
            count=1,
        )
        column = re.sub(
            br'max="\d+"',
            f'max="{maximum}"'.encode("ascii"),
            column,
            count=1,
        )
        return column

    transformed = re.sub(
        br"<col\b[^>]*/>",
        transform_column,
        columns_match.group(0),
    )
    return (
        prefix[: columns_match.start()]
        + transformed
        + prefix[columns_match.end() :]
    )


def _transform_merge_reference(
    reference: str,
    old_footer_row: int,
    new_footer_row: int,
) -> str | None:
    cells = reference.split(":")
    transformed = []
    for cell in cells:
        match = re.fullmatch(r"([A-Z]+)(\d+)", cell)
        if not match:
            return reference
        column = _shift_column(match.group(1))
        if column is None:
            return None
        row = int(match.group(2))
        if row == old_footer_row:
            row = new_footer_row
        transformed.append(f"{column}{row}")
    return ":".join(transformed)


def _transform_suffix(
    suffix: bytes,
    old_footer_row: int,
    new_footer_row: int,
) -> bytes:
    merge_block = re.search(
        br"<mergeCells\b[^>]*>.*?</mergeCells>",
        suffix,
        re.DOTALL,
    )
    if merge_block:
        references = re.findall(
            br'<mergeCell ref="([^"]+)"\s*/>',
            merge_block.group(0),
        )
        transformed_references = []
        for reference in references:
            transformed = _transform_merge_reference(
                reference.decode("ascii"),
                old_footer_row,
                new_footer_row,
            )
            if transformed:
                transformed_references.append(transformed)
        replacement = (
            f'<mergeCells count="{len(transformed_references)}">'
            + "".join(
                f'<mergeCell ref="{reference}"/>'
                for reference in transformed_references
            )
            + "</mergeCells>"
        ).encode("ascii")
        suffix = (
            suffix[: merge_block.start()]
            + replacement
            + suffix[merge_block.end() :]
        )
    return suffix


def _force_recalculation(workbook_xml: bytes) -> bytes:
    calc_match = re.search(br"<calcPr\b[^>]*/>", workbook_xml)
    if not calc_match:
        return workbook_xml
    calc = calc_match.group(0)
    for attribute, value in (
        (b"calcMode", b"auto"),
        (b"fullCalcOnLoad", b"1"),
        (b"forceFullCalc", b"1"),
    ):
        pattern = re.compile(attribute + br'="[^"]*"')
        replacement = attribute + b'="' + value + b'"'
        if pattern.search(calc):
            calc = pattern.sub(replacement, calc, count=1)
        else:
            calc = calc[:-2] + b" " + replacement + b"/>"
    return (
        workbook_xml[: calc_match.start()]
        + calc
        + workbook_xml[calc_match.end() :]
    )


def _transform_calc_chain(
    calc_chain: bytes,
    old_footer_row: int,
    new_footer_row: int,
) -> bytes:
    return calc_chain.replace(
        str(old_footer_row).encode("ascii"),
        str(new_footer_row).encode("ascii"),
    )


def _template_parts(
    template_archive: zipfile.ZipFile,
) -> tuple[int, int, bytes, bytes, bytes, bytes]:
    """Template faylidan header, footer va struktura qismlarini ajratib oladi.

    Qaytaradi: (tmpl_footer_row, tmpl_last_data_row,
                header_bytes, footer_bytes, prefix_bytes, suffix_bytes)
    """
    sheet = template_archive.read("xl/worksheets/sheet1.xml")
    dim = re.search(br'<dimension ref="[^"]*?(\d+)"', sheet)
    if not dim:
        raise RuntimeError("Template dimension topilmadi")
    tmpl_footer_row = int(dim.group(1))
    tmpl_last_data_row = tmpl_footer_row - 1

    sd_open = sheet.find(b"<sheetData>")
    sd_close = sheet.find(b"</sheetData>")
    content_start = sd_open + len(b"<sheetData>")
    prefix = sheet[:content_start]
    content = sheet[content_start:sd_close]
    suffix = sheet[sd_close:]

    header_bytes = b""
    footer_bytes = b""
    for m in ROW_PATTERN.finditer(content):
        rn = int(m.group(1))
        if rn <= 5:
            header_bytes += m.group(0)
        elif rn == tmpl_footer_row:
            footer_bytes = m.group(0)

    return tmpl_footer_row, tmpl_last_data_row, header_bytes, footer_bytes, prefix, suffix


def _renumber_footer(
    footer: bytes,
    old_footer_row: int,
    new_footer_row: int,
    old_last_data_row: int,
    new_last_data_row: int,
) -> bytes:
    """Footer qatoridagi qator raqamlari va SUM formulalarini yangilaydi.
    Ustun siljishsiz — template footer allaqachon to'g'ri formatda."""
    result = footer.replace(
        str(old_footer_row).encode("ascii"),
        str(new_footer_row).encode("ascii"),
    )
    if new_last_data_row > 0:
        result = result.replace(
            str(old_last_data_row).encode("ascii"),
            str(new_last_data_row).encode("ascii"),
        )
    return result


def _update_suffix_rows(suffix: bytes, old_row: int, new_row: int) -> bytes:
    """Suffix (mergeCells va boshqalar) dagi footer qator raqamini yangilaydi."""
    merge_block = re.search(br"<mergeCells\b[^>]*>.*?</mergeCells>", suffix, re.DOTALL)
    if not merge_block:
        return suffix
    old_b = str(old_row).encode("ascii")
    new_b = str(new_row).encode("ascii")
    new_block = merge_block.group(0).replace(old_b, new_b)
    return suffix[: merge_block.start()] + new_block + suffix[merge_block.end() :]


def generate_three_month_report(
    source_path: str | Path,
    output_path: str | Path,
    template_path: str | Path | None = None,
    reference_date: date | None = None,
) -> ThreeMonthReportResult:
    source = Path(source_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cutoff = three_month_cutoff(reference_date)
    cutoff_serial = excel_serial(cutoff)

    base = Path(template_path) if template_path else source
    with zipfile.ZipFile(source) as src_arch, zipfile.ZipFile(base) as tmpl_arch:
        strings = _shared_strings(src_arch)
        src_sheet = src_arch.read("xl/worksheets/sheet1.xml")

        # Manba (umumiy_shablon) dimension
        src_dim = re.search(br'<dimension ref="A1:T(\d+)"', src_sheet)
        if not src_dim:
            raise RuntimeError("umumiy_shablon A1:T... dimension topilmadi")
        old_footer_row = int(src_dim.group(1))
        old_last_data_row = old_footer_row - 1

        # Template dan header/footer/prefix/suffix
        tmpl_footer_row, tmpl_last_data, tmpl_header, tmpl_footer, prefix, suffix = \
            _template_parts(tmpl_arch)

        # Template prefix dagi dimension ni almashtirish uchun qoldiramiz (pastda yangilaymiz)
        src_sd_open = src_sheet.find(b"<sheetData>")
        src_sd_close = src_sheet.find(b"</sheetData>")
        src_content = src_sheet[src_sd_open + len(b"<sheetData>"):src_sd_close]

        source_rows = 0
        kept_rows = 0
        removed_meter_rows = 0
        removed_recent_rows = 0
        next_data_row = 6

        with tempfile.TemporaryFile() as filtered_rows:
            filtered_rows.write(tmpl_header)  # rows 1-5 templatedan (formatlangan)

            for match in ROW_PATTERN.finditer(src_content):
                old_row = int(match.group(1))
                row = match.group(0)
                if old_row <= 5 or old_row == old_footer_row:
                    continue  # header/footer dan o'tamiz

                source_rows += 1
                meter_value = _cell_text(_cell_bytes(row, "H", old_row), strings).strip()
                if meter_value != "+":
                    removed_meter_rows += 1
                    continue
                if not _date_is_allowed(_cell_bytes(row, "L", old_row), cutoff_serial):
                    removed_recent_rows += 1
                    continue

                filtered_rows.write(
                    _transform_row(row, old_row, next_data_row, old_last_data_row, 0)
                )
                next_data_row += 1
                kept_rows += 1

            new_last_data_row = max(5, next_data_row - 1)
            new_footer_row = next_data_row
            filtered_rows.seek(0)
            rows_bytes = filtered_rows.read()

        if tmpl_footer:
            rows_bytes += _renumber_footer(
                tmpl_footer, tmpl_footer_row, new_footer_row,
                tmpl_last_data, new_last_data_row,
            )

        prefix = re.sub(
            br'<dimension ref="[^"]*"',
            f'<dimension ref="A1:S{new_footer_row}"'.encode("ascii"),
            prefix, count=1,
        )
        suffix = _update_suffix_rows(suffix, tmpl_footer_row, new_footer_row)
        new_sheet_xml = prefix + rows_bytes + suffix

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out_arch:
            for item in tmpl_arch.infolist():
                if item.filename == "xl/calcChain.xml":
                    continue
                data = tmpl_arch.read(item.filename)
                if item.filename == "xl/worksheets/sheet1.xml":
                    data = new_sheet_xml
                elif item.filename == "xl/workbook.xml":
                    data = _force_recalculation(data)
                out_arch.writestr(item, data)

    return ThreeMonthReportResult(
        output_path=output,
        cutoff_date=cutoff,
        source_rows=source_rows,
        kept_rows=kept_rows,
        removed_meter_rows=removed_meter_rows,
        removed_recent_rows=removed_recent_rows,
    )


def latest_three_month_report(directory: str | Path) -> Path | None:
    folder = Path(directory)
    files = sorted(
        folder.glob("3_oylik_korsatgich_olinmagan_*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


@dataclass(frozen=True)
class DebtReportResult:
    output_path: Path
    source_rows: int
    kept_rows: int


from typing import Callable as _Callable


def _shift_column_debt(column: str) -> str | None:
    """P(16) va R(18) olib tashlanadi; A-O o'zgarmaydi; Q→P, S→Q, T→R."""
    number = _column_number(column)
    if number <= 15:
        return column
    if number == 16:
        return None
    if number == 17:
        return _column_label(16)
    if number == 18:
        return None
    return _column_label(number - 2)


def _shift_column_creditor(column: str) -> str | None:
    """O(15) va R(18) olib tashlanadi; A-N o'zgarmaydi; P→O, Q→P, S→Q, T→R."""
    number = _column_number(column)
    if number <= 14:
        return column
    if number == 15:
        return None
    if number == 16:
        return _column_label(15)
    if number == 17:
        return _column_label(16)
    if number == 18:
        return None
    return _column_label(number - 2)


def _transform_row_filtered(
    row: bytes,
    old_row: int,
    new_row: int,
    old_last_data_row: int,
    new_last_data_row: int,
    shift_fn: _Callable[[str], str | None],
    removed_count: int = 2,
) -> bytes:
    transformed_cells: list[bytes] = []
    matches = list(CELL_PATTERN.finditer(row))
    if not matches:
        return re.sub(
            br'(<row\b[^>]*\br=")\d+(")',
            lambda m: m.group(1) + str(new_row).encode("ascii") + m.group(2),
            row,
            count=1,
        )

    start = matches[0].start()
    end = matches[-1].end()
    row_start = row[:start]
    row_end = row[end:]
    for match in matches:
        cell = match.group(0)
        reference = CELL_REFERENCE_PATTERN.search(cell)
        if not reference:
            transformed_cells.append(cell)
            continue
        old_column = reference.group(1).decode("ascii")
        new_column = shift_fn(old_column)
        if new_column is None:
            continue
        new_reference = f"{new_column}{new_row}".encode("ascii")
        cell = CELL_REFERENCE_PATTERN.sub(b'r="' + new_reference + b'"', cell, count=1)
        if new_last_data_row > 0:
            cell = cell.replace(
                str(old_last_data_row).encode("ascii"),
                str(new_last_data_row).encode("ascii"),
            )
        transformed_cells.append(cell)

    row_start = re.sub(
        br'(<row\b[^>]*\br=")\d+(")',
        lambda m: m.group(1) + str(new_row).encode("ascii") + m.group(2),
        row_start,
        count=1,
    )
    if removed_count > 0:
        new_span = f'spans="1:{20 - removed_count}"'.encode("ascii")
        row_start = re.sub(br'spans="1:20"', new_span, row_start)
    return row_start + b"".join(transformed_cells) + row_end


def _transform_columns_filtered(
    prefix: bytes,
    shift_fn: _Callable[[str], str | None],
    removed_count: int = 2,
) -> bytes:
    columns_match = re.search(br"<cols>.*?</cols>", prefix, re.DOTALL)
    if not columns_match:
        return prefix

    def _shift_num(n: int) -> int | None:
        label = _column_label(n)
        new_label = shift_fn(label)
        if new_label is None:
            return None
        return _column_number(new_label)

    def transform_column(match: re.Match[bytes]) -> bytes:
        column = match.group(0)
        minimum_match = re.search(br'min="(\d+)"', column)
        maximum_match = re.search(br'max="(\d+)"', column)
        if not minimum_match or not maximum_match:
            return column
        minimum = int(minimum_match.group(1))
        maximum = int(maximum_match.group(1))
        new_min = _shift_num(minimum)
        new_max = (
            _shift_num(maximum)
            if maximum < 16384
            else maximum - removed_count
        )
        if new_min is None or new_max is None:
            return b""
        column = re.sub(
            br'min="\d+"',
            f'min="{new_min}"'.encode("ascii"),
            column,
            count=1,
        )
        column = re.sub(
            br'max="\d+"',
            f'max="{new_max}"'.encode("ascii"),
            column,
            count=1,
        )
        return column

    transformed = re.sub(br"<col\b[^>]*/>", transform_column, columns_match.group(0))
    return (
        prefix[: columns_match.start()]
        + transformed
        + prefix[columns_match.end() :]
    )


def _transform_suffix_filtered(
    suffix: bytes,
    old_footer_row: int,
    new_footer_row: int,
    shift_fn: _Callable[[str], str | None],
) -> bytes:
    merge_block = re.search(
        br"<mergeCells\b[^>]*>.*?</mergeCells>",
        suffix,
        re.DOTALL,
    )
    if not merge_block:
        return suffix
    references = re.findall(
        br'<mergeCell ref="([^"]+)"\s*/>',
        merge_block.group(0),
    )
    transformed_references = []
    for reference in references:
        cells = reference.decode("ascii").split(":")
        parts = []
        skip = False
        for cell in cells:
            m = re.fullmatch(r"([A-Z]+)(\d+)", cell)
            if not m:
                parts.append(cell)
                continue
            new_col = shift_fn(m.group(1))
            if new_col is None:
                skip = True
                break
            row = int(m.group(2))
            if row == old_footer_row:
                row = new_footer_row
            parts.append(f"{new_col}{row}")
        if not skip:
            transformed_references.append(":".join(parts))
    replacement = (
        f'<mergeCells count="{len(transformed_references)}">'
        + "".join(
            f'<mergeCell ref="{r}"/>' for r in transformed_references
        )
        + "</mergeCells>"
    ).encode("ascii")
    return (
        suffix[: merge_block.start()]
        + replacement
        + suffix[merge_block.end() :]
    )


def _generate_filtered_report(
    source_path: str | Path,
    output_path: str | Path,
    filter_column: str,
    filter_fn: _Callable[[float], bool],
    shift_fn: _Callable[[str], str | None],
    output_last_col: str = "R",
    removed_count: int = 2,
    template_path: str | Path | None = None,
) -> tuple[int, int]:
    """
    Ichki yordamchi: umumiy_shablon dan filtrlangan hisobot yaratadi.
    template_path berilsa — uning ZIP strukturasi, rows 1-5 va footer ishlatiladi.
    Qaytaradi: (source_rows, kept_rows).
    """
    source = Path(source_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    base = Path(template_path) if template_path else source

    with zipfile.ZipFile(source) as src_arch, zipfile.ZipFile(base) as tmpl_arch:
        strings = _shared_strings(src_arch)
        src_sheet = src_arch.read("xl/worksheets/sheet1.xml")

        src_dim = re.search(br'<dimension ref="A1:T(\d+)"', src_sheet)
        if not src_dim:
            raise RuntimeError("umumiy_shablon A1:T... dimension topilmadi")
        old_footer_row = int(src_dim.group(1))
        old_last_data_row = old_footer_row - 1

        tmpl_footer_row, tmpl_last_data, tmpl_header, tmpl_footer, prefix, suffix = \
            _template_parts(tmpl_arch)

        src_sd_open = src_sheet.find(b"<sheetData>")
        src_sd_close = src_sheet.find(b"</sheetData>")
        src_content = src_sheet[src_sd_open + len(b"<sheetData>"):src_sd_close]

        source_rows = 0
        kept_rows = 0
        next_data_row = 6

        with tempfile.TemporaryFile() as filtered_rows:
            filtered_rows.write(tmpl_header)  # rows 1-5 templatedan

            for match in ROW_PATTERN.finditer(src_content):
                old_row = int(match.group(1))
                row = match.group(0)
                if old_row <= 5 or old_row == old_footer_row:
                    continue

                source_rows += 1
                cell = _cell_bytes(row, filter_column, old_row)
                text = _cell_text(cell, strings).strip()
                try:
                    value = float(text.replace(",", ".")) if text else 0.0
                except ValueError:
                    value = 0.0
                if not filter_fn(value):
                    continue

                filtered_rows.write(
                    _transform_row_filtered(
                        row, old_row, next_data_row, old_last_data_row, 0, shift_fn, removed_count,
                    )
                )
                next_data_row += 1
                kept_rows += 1

            new_last_data_row = max(5, next_data_row - 1)
            new_footer_row = next_data_row
            filtered_rows.seek(0)
            rows_bytes = filtered_rows.read()

        if tmpl_footer:
            rows_bytes += _renumber_footer(
                tmpl_footer, tmpl_footer_row, new_footer_row,
                tmpl_last_data, new_last_data_row,
            )

        prefix = re.sub(
            br'<dimension ref="[^"]*"',
            f'<dimension ref="A1:{output_last_col}{new_footer_row}"'.encode("ascii"),
            prefix, count=1,
        )
        suffix = _update_suffix_rows(suffix, tmpl_footer_row, new_footer_row)
        new_sheet_xml = prefix + rows_bytes + suffix

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out_arch:
            for item in tmpl_arch.infolist():
                if item.filename == "xl/calcChain.xml":
                    continue
                data = tmpl_arch.read(item.filename)
                if item.filename == "xl/worksheets/sheet1.xml":
                    data = new_sheet_xml
                elif item.filename == "xl/workbook.xml":
                    data = _force_recalculation(data)
                out_arch.writestr(item, data)

    return source_rows, kept_rows


def generate_debt_report(
    source_path: str | Path,
    output_path: str | Path,
    template_path: str | Path | None = None,
) -> DebtReportResult:
    """umumiy_shablon dan qarzdorlar (O > 0): P va R olib tashlanadi."""
    source_rows, kept_rows = _generate_filtered_report(
        source_path, output_path,
        filter_column="O",
        filter_fn=lambda v: v > 0,
        shift_fn=_shift_column_debt,
        template_path=template_path,
    )
    return DebtReportResult(
        output_path=Path(output_path),
        source_rows=source_rows,
        kept_rows=kept_rows,
    )


def latest_debt_report(directory: str | Path) -> Path | None:
    folder = Path(directory)
    files = sorted(
        folder.glob("qarzdorlar_royxati_*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


@dataclass(frozen=True)
class CreditorReportResult:
    output_path: Path
    source_rows: int
    kept_rows: int


def generate_creditor_report(
    source_path: str | Path,
    output_path: str | Path,
    template_path: str | Path | None = None,
) -> CreditorReportResult:
    """umumiy_shablon dan kreditorlar (P != 0, ya'ni P < 0): O va R olib tashlanadi."""
    source_rows, kept_rows = _generate_filtered_report(
        source_path, output_path,
        filter_column="P",
        filter_fn=lambda v: v != 0,
        shift_fn=_shift_column_creditor,
        template_path=template_path,
    )
    return CreditorReportResult(
        output_path=Path(output_path),
        source_rows=source_rows,
        kept_rows=kept_rows,
    )


def latest_creditor_report(directory: str | Path) -> Path | None:
    folder = Path(directory)
    files = sorted(
        folder.glob("kreditor_royxati_*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


@dataclass(frozen=True)
class NoAccountingReportResult:
    output_path: Path
    source_rows: int
    kept_rows: int


def _identity_shift(column: str) -> str | None:
    return column


def generate_no_accounting_report(
    source_path: str | Path,
    output_path: str | Path,
    template_path: str | Path | None = None,
) -> NoAccountingReportResult:
    """umumiy_shablon dan hisob kitobi yuritilmayotganlar (N == 0): 20 ustun."""
    source_rows, kept_rows = _generate_filtered_report(
        source_path, output_path,
        filter_column="N",
        filter_fn=lambda v: v == 0,
        shift_fn=_identity_shift,
        output_last_col="T",
        removed_count=0,
        template_path=template_path,
    )
    return NoAccountingReportResult(
        output_path=Path(output_path),
        source_rows=source_rows,
        kept_rows=kept_rows,
    )


def latest_no_accounting_report(directory: str | Path) -> Path | None:
    folder = Path(directory)
    files = sorted(
        folder.glob("hisob_yuritilmayotgan_*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None
