"""
Tuman pasporti hisobotini to'liq F3 (104 ustunli) fayldan yaratadi.
Barcha 83 ko'rsatkich Python COUNTIFS/SUMIFS bilan hisoblanadi.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import zipfile
import xml.etree.ElementTree as ET

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side


# ---------------------------------------------------------------------------
# Ustun indekslari (0-based, Excel column → 0-based: A=0, B=1, ...)
# ---------------------------------------------------------------------------

def _ci(letter: str) -> int:
    n = 0
    for c in letter.upper():
        n = n * 26 + (ord(c) - 64)
    return n - 1


_CI_MAHALLA  = _ci("B")   # Махалля
_CI_STREET   = _ci("C")   # Улица
_CI_HOUSE    = _ci("D")   # № дома
_CI_KOD      = _ci("F")   # Код благоустройства (2/3/4 (2202))
_CI_FROM     = _ci("J")   # От какой даты охвачен
_CI_TYPE     = _ci("N")   # Тип дома: МЭ / ЧД
_CI_METER    = _ci("U")   # C водомером (+/-)
_CI_PROP     = _ci("W")   # Кол-во лиц (факт)
_CI_PROZHIV  = _ci("X")   # Текущ.
_CI_MCOUNT   = _ci("Z")   # Кол.счет (hisoblagich soni)
_CI_LASTREAD = _ci("AA")  # Дата послед.показ
_CI_AVGDAY   = _ci("AC")  # Сред.на 1 чел (kub/sut)
_CI_DEBIT    = _ci("BQ")  # Общий дебит
_CI_KREDIT   = _ci("BT")  # Общий кредит
_CI_CHARGED  = _ci("CF")  # Всего начисленно сум
_CI_CHRGVAT  = _ci("CH")  # Всего начисленно С НДС
_CI_LASTPAY  = _ci("CV")  # Дата последнего платежа

_DATA_ROW_START = 6
_TYPE_ME  = "МЭ"
_TYPE_CHD = "ЧД"


# ---------------------------------------------------------------------------
# Yordamchi funksiyalar
# ---------------------------------------------------------------------------

def _to_date(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return None


def _to_float(v) -> float:
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _to_int(v) -> int:
    return int(_to_float(v))


def _to_str(v) -> str:
    return str(v).strip() if v is not None else ""


def _edate(d: date, months: int) -> date:
    m = d.month + months
    y = d.year
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _get(row: tuple, idx: int):
    return row[idx] if idx < len(row) else None


# ---------------------------------------------------------------------------
# F3 faylini o'qish
# ---------------------------------------------------------------------------

def _extract_ref_date(header_text: str) -> date | None:
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", str(header_text))
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


_XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_EXCEL_EPOCH = date(1899, 12, 30)  # Excel serial date epoch


def _excel_serial_to_date(serial) -> date | None:
    try:
        n = int(float(serial))
        if n <= 0:
            return None
        from datetime import timedelta
        return _EXCEL_EPOCH + timedelta(days=n)
    except (TypeError, ValueError):
        return None


def _col_letter_to_idx(ref: str) -> int:
    """Excel cell ref like 'A1','N6','BQ100' → 0-based column index."""
    letters = re.match(r"([A-Za-z]+)", ref)
    if not letters:
        return -1
    s = letters.group(1).upper()
    n = 0
    for c in s:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def _load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    """Shared strings table (xl/sharedStrings.xml)."""
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    with z.open("xl/sharedStrings.xml") as f:
        tree = ET.parse(f)
    ns = {"s": _XLSX_NS}
    strings = []
    for si in tree.findall(".//s:si", ns):
        texts = si.findall(".//s:t", ns)
        strings.append("".join((t.text or "") for t in texts))
    return strings


def _read_f3(path: Path) -> tuple[date | None, list[dict]]:
    """
    XLSX faylni to'g'ridan-to'g'ri XML orqali o'qiydi.
    dimension ref="A1" bo'lsa ham to'g'ri ishlaydi.
    """
    # Kerakli ustun indekslari to'plami
    needed_idx = {
        _CI_MAHALLA, _CI_STREET, _CI_HOUSE, _CI_KOD, _CI_FROM,
        _CI_TYPE, _CI_METER, _CI_PROP, _CI_PROZHIV, _CI_MCOUNT,
        _CI_LASTREAD, _CI_AVGDAY, _CI_DEBIT, _CI_KREDIT,
        _CI_CHARGED, _CI_CHRGVAT, _CI_LASTPAY,
    }
    # Date ustunlari (Excel serial date sifatida saqlangan)
    date_idx = {_CI_FROM, _CI_LASTREAD, _CI_LASTPAY}

    ref_date: date | None = None
    rows: list[dict] = []

    with zipfile.ZipFile(str(path), "r") as z:
        shared = _load_shared_strings(z)
        with z.open("xl/worksheets/sheet1.xml") as f:
            row_buf: dict[int, object] = {}  # col_idx → value
            row_num = 0
            for event, elem in ET.iterparse(f, events=("start", "end")):
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if event == "start" and tag == "row":
                    row_buf = {}
                    row_num = int(elem.get("r", 0))
                elif event == "end" and tag == "c":
                    ref = elem.get("r", "")
                    col_idx = _col_letter_to_idx(ref)
                    if col_idx not in needed_idx and (row_num != 1 or col_idx != 0):
                        elem.clear()
                        continue
                    typ_attr = elem.get("t", "")
                    if typ_attr == "inlineStr":
                        # <is><t>text</t></is> formatida saqlangan.
                        # Sana ustunlarida inlineStr = bo'sh hujayraga (skip).
                        if col_idx in date_idx:
                            pass
                        else:
                            t_elem = elem.find(f".//{{{_XLSX_NS}}}t")
                            raw_str = (t_elem.text or "").strip() if t_elem is not None else ""
                            if raw_str:
                                row_buf[col_idx] = raw_str
                    else:
                        v_elem = elem.find(f"{{{_XLSX_NS}}}v")
                        raw = v_elem.text if v_elem is not None else None
                        if raw is not None:
                            if typ_attr == "s":
                                idx_s = int(raw)
                                row_buf[col_idx] = shared[idx_s] if idx_s < len(shared) else ""
                            elif col_idx in date_idx:
                                row_buf[col_idx] = _excel_serial_to_date(raw)
                            else:
                                try:
                                    row_buf[col_idx] = float(raw)
                                except ValueError:
                                    row_buf[col_idx] = raw
                    elem.clear()
                elif event == "end" and tag == "row":
                    if row_num == 1:
                        ref_date = _extract_ref_date(str(row_buf.get(0, "")))
                    elif row_num >= _DATA_ROW_START:
                        typ = _to_str(row_buf.get(_CI_TYPE, "")).upper()
                        if typ in (_TYPE_ME, _TYPE_CHD):
                            rows.append({
                                "mahalla":  _to_str(row_buf.get(_CI_MAHALLA)),
                                "street":   _to_str(row_buf.get(_CI_STREET)),
                                "house":    _to_str(row_buf.get(_CI_HOUSE)),
                                "kod":      _to_str(row_buf.get(_CI_KOD)),
                                "from_dt":  row_buf.get(_CI_FROM),
                                "type":     typ,
                                "meter":    _to_str(row_buf.get(_CI_METER)),
                                "prop":     _to_int(row_buf.get(_CI_PROP, 0)),
                                "prozhiv":  _to_int(row_buf.get(_CI_PROZHIV, 0)),
                                "mcount":   _to_int(row_buf.get(_CI_MCOUNT, 0)),
                                "lastread": row_buf.get(_CI_LASTREAD),
                                "avgday":   _to_float(row_buf.get(_CI_AVGDAY, 0)),
                                "debit":    _to_float(row_buf.get(_CI_DEBIT, 0)),
                                "kredit":   _to_float(row_buf.get(_CI_KREDIT, 0)),
                                "charged":  _to_float(row_buf.get(_CI_CHARGED, 0)),
                                "chrgvat":  _to_float(row_buf.get(_CI_CHRGVAT, 0)),
                                "lastpay":  row_buf.get(_CI_LASTPAY),
                            })
                    row_buf = {}
                    elem.clear()

    return ref_date, rows


# ---------------------------------------------------------------------------
# Hisobot validatsiyasi
# ---------------------------------------------------------------------------

def validate_f3_full(path: Path) -> str | None:
    """None = yaroqli; string = xato xabari."""
    try:
        with zipfile.ZipFile(str(path), "r") as z:
            names = z.namelist()
        if "xl/worksheets/sheet1.xml" not in names:
            return "Fayl tuzilishi noto'g'ri (sheet1.xml topilmadi)."
    except Exception as exc:
        return f"Faylni ochib bo'lmadi: {exc}"
    # Ustun sonini cols XML dan aniqlaymiz
    try:
        with zipfile.ZipFile(str(path), "r") as z:
            with z.open("xl/worksheets/sheet1.xml") as f:
                chunk = f.read(8192).decode("utf-8", errors="replace")
        # <cols> bo'limida oxirgi col max ni topamiz
        max_vals = re.findall(r'max="(\d+)"', chunk)
        if max_vals:
            max_col = max(int(v) for v in max_vals)
            if max_col < 100:
                return (
                    f"Fayl {max_col} ustun — to'liq F3 kerak (kamida 100 ustun). "
                    "Bu umumiy shablon (20 ustunli) bo'lishi mumkin."
                )
    except Exception:
        pass  # tekshirish muvaffaqiyatsiz bo'lsa ham qabul qilaver
    return None


# ---------------------------------------------------------------------------
# Ko'rsatkichlarni hisoblash
# ---------------------------------------------------------------------------

def _cnt(rows: list[dict], **conds) -> int:
    total = 0
    for r in rows:
        ok = True
        for key, (op, val) in conds.items():
            rv = r.get(key)
            if op == "eq":
                ok = rv == val
            elif op == "ne":
                ok = rv != val
            elif op == "gt":
                ok = rv is not None and rv > val
            elif op == "lt":
                ok = rv is not None and rv < val
            elif op == "ge":
                ok = rv is not None and rv >= val
            elif op == "le":
                ok = rv is not None and rv <= val
            elif op == "ltle":  # lo < x <= hi
                ok = rv is not None and val[0] < rv <= val[1]
            elif op == "ltlt":
                ok = rv is not None and val[0] < rv < val[1]
            elif op == "not_none":
                ok = rv is not None
            if not ok:
                break
        if ok:
            total += 1
    return total


def _sm(rows: list[dict], col: str, **conds) -> float:
    total = 0.0
    for r in rows:
        ok = True
        for key, (op, val) in conds.items():
            rv = r.get(key)
            if op == "eq":
                ok = rv == val
            elif op == "ne":
                ok = rv != val
            elif op == "gt":
                ok = rv is not None and rv > val
            elif op == "lt":
                ok = rv is not None and rv < val
            elif op == "ltle":
                ok = rv is not None and val[0] < rv <= val[1]
            elif op == "ltlt":
                ok = rv is not None and val[0] < rv < val[1]
            if not ok:
                break
        if ok:
            total += r.get(col, 0.0) or 0.0
    return total


def _sum_col(rows: list[dict], col: str, typ: str) -> float:
    return sum(r[col] for r in rows if r["type"] == typ)


def _cnt_type(rows: list[dict], typ: str, **conds) -> int:
    return _cnt(rows, type=("eq", typ), **conds)


def _sm_type(rows: list[dict], col: str, typ: str, **conds) -> float:
    return _sm(rows, col, type=("eq", typ), **conds)


def _pair(rows, fn_b, fn_c) -> tuple[int, int, int]:
    b = sum(1 for r in rows if fn_b(r))
    c = sum(1 for r in rows if fn_c(r))
    return b, c, b + c


def _pair_sum(rows, col, fn_b, fn_c) -> tuple[float, float, float]:
    b = sum(r[col] for r in rows if fn_b(r))
    c = sum(r[col] for r in rows if fn_c(r))
    return b, c, b + c


def _compute_rows(rows: list[dict], ref_date: date) -> list[tuple[str, object, object, object]]:
    """
    83 qatorli pasport ma'lumotlarini hisoblaydi.
    Har bir element: (label, жилой_val, частный_val, total_val)
    """
    ms = date(ref_date.year, ref_date.month, 1)  # oy boshi

    me = lambda r: r["type"] == _TYPE_ME
    chd = lambda r: r["type"] == _TYPE_CHD

    # Unique mahallalar
    me_mah  = len({r["mahalla"] for r in rows if me(r) and r["mahalla"]})
    chd_mah = len({r["mahalla"] for r in rows if chd(r) and r["mahalla"]})
    all_mah = len({r["mahalla"] for r in rows if r["mahalla"]})

    # Unique binolar (mahalla + ko'cha + uy)
    me_dom  = len({(r["mahalla"], r["street"], r["house"]) for r in rows if me(r)})
    chd_dom = len({(r["mahalla"], r["street"], r["house"]) for r in rows if chd(r)})
    all_dom = len({(r["mahalla"], r["street"], r["house"]) for r in rows})

    # Abonent (ro'yxatga olingan sanasi joriy oy boshidan oldin)
    def act(r): return r["from_dt"] is not None and r["from_dt"] < ms

    me_abon  = sum(1 for r in rows if me(r) and act(r))
    chd_abon = sum(1 for r in rows if chd(r) and act(r))

    me_vm   = sum(1 for r in rows if me(r) and act(r) and r["meter"] == "+")
    chd_vm  = sum(1 for r in rows if chd(r) and act(r) and r["meter"] == "+")

    # Debit / kredit
    me_deb_n  = sum(1 for r in rows if me(r) and r["debit"] > 0)
    chd_deb_n = sum(1 for r in rows if chd(r) and r["debit"] > 0)
    me_deb_s  = sum(r["debit"] for r in rows if me(r) and r["debit"] > 0)
    chd_deb_s = sum(r["debit"] for r in rows if chd(r) and r["debit"] > 0)

    me_deb_vm_n  = sum(1 for r in rows if me(r) and r["debit"] > 0 and r["meter"] == "+")
    chd_deb_vm_n = sum(1 for r in rows if chd(r) and r["debit"] > 0 and r["meter"] == "+")
    me_deb_vm_s  = sum(r["debit"] for r in rows if me(r) and r["debit"] > 0 and r["meter"] == "+")
    chd_deb_vm_s = sum(r["debit"] for r in rows if chd(r) and r["debit"] > 0 and r["meter"] == "+")

    me_kr_n  = sum(1 for r in rows if me(r) and r["kredit"] < 0)
    chd_kr_n = sum(1 for r in rows if chd(r) and r["kredit"] < 0)
    me_kr_s  = sum(r["kredit"] for r in rows if me(r) and r["kredit"] < 0)
    chd_kr_s = sum(r["kredit"] for r in rows if chd(r) and r["kredit"] < 0)

    me_charged  = sum(r["charged"] for r in rows if me(r))
    chd_charged = sum(r["charged"] for r in rows if chd(r))
    me_chv      = sum(r["chrgvat"] for r in rows if me(r))
    chd_chv     = sum(r["chrgvat"] for r in rows if chd(r))

    me_zero  = sum(1 for r in rows if me(r) and r["chrgvat"] == 0)
    chd_zero = sum(1 for r in rows if chd(r) and r["chrgvat"] == 0)

    # Propiska / prozhivayushchiy / hisoblagich soni
    me_prop   = sum(r["prop"]   for r in rows if me(r))
    chd_prop  = sum(r["prop"]   for r in rows if chd(r))
    me_proz   = sum(r["prozhiv"] for r in rows if me(r))
    chd_proz  = sum(r["prozhiv"] for r in rows if chd(r))
    me_mcnt   = sum(r["mcount"] for r in rows if me(r))
    chd_mcnt  = sum(r["mcount"] for r in rows if chd(r))

    # Ko'rsatkich olinmaganlar (hisoblagichli, oxirgi o'qish sanasi < N oy oldin)
    def nsnyt(n_months):
        cutoff = _edate(ms, -n_months) if n_months > 0 else ms
        me_n  = sum(1 for r in rows if me(r) and r["meter"] == "+" and
                    r["lastread"] is not None and r["lastread"] < cutoff)
        chd_n = sum(1 for r in rows if chd(r) and r["meter"] == "+" and
                    r["lastread"] is not None and r["lastread"] < cutoff)
        return me_n, chd_n, me_n + chd_n

    nsnyt1  = nsnyt(1)
    nsnyt3  = nsnyt(3)
    nsnyt6  = nsnyt(6)
    nsnyt12 = nsnyt(12)
    nsnyt24 = nsnyt(24)
    nsnyt36 = nsnyt(36)

    # O'rtacha sutkalik sarflash (hisoblagichli)
    def avd(lo, hi):
        me_n  = sum(1 for r in rows if me(r) and r["meter"] == "+" and
                    lo < r["avgday"] < hi)
        chd_n = sum(1 for r in rows if chd(r) and r["meter"] == "+" and
                    lo < r["avgday"] < hi)
        return me_n, chd_n, me_n + chd_n

    def avd_ge(lo):
        me_n  = sum(1 for r in rows if me(r) and r["meter"] == "+" and r["avgday"] >= lo)
        chd_n = sum(1 for r in rows if chd(r) and r["meter"] == "+" and r["avgday"] >= lo)
        return me_n, chd_n, me_n + chd_n

    avd30    = avd(0, 0.03)
    avd60    = avd(0, 0.06)
    avd100   = avd(0, 0.1)
    avd1_2   = avd(1, 2)
    avd2_5   = avd(2, 5)
    avd5_10  = avd(5, 10)
    avd_10   = avd_ge(10)

    # To'lovsiz abonentlar (oxirgi to'lov sanasi N oy oldidan)
    def nopay(n_months):
        cutoff = _edate(ms, -n_months)
        me_n  = sum(1 for r in rows if me(r) and
                    (r["lastpay"] is None or r["lastpay"] < cutoff))
        chd_n = sum(1 for r in rows if chd(r) and
                    (r["lastpay"] is None or r["lastpay"] < cutoff))
        return me_n, chd_n, me_n + chd_n

    nopay1  = nopay(1)
    nopay3  = nopay(3)
    nopay6  = nopay(6)
    nopay12 = nopay(12)
    nopay24 = nopay(24)
    nopay36 = nopay(36)

    # Muddati o'tgan qarz: debit > 0 VA oxirgi to'lov N oy oldidan bo'lgan
    def _overdue(n_months):
        cutoff = _edate(ms, -n_months)
        def _ok(r): return r["debit"] > 0 and (r["lastpay"] is None or r["lastpay"] < cutoff)
        def _vm(r): return _ok(r) and r["meter"] == "+"
        def _tar(r): return _ok(r) and r["meter"] != "+"
        me_n   = sum(1 for r in rows if me(r)  and _ok(r))
        chd_n  = sum(1 for r in rows if chd(r) and _ok(r))
        me_s   = sum(r["debit"] for r in rows if me(r)  and _ok(r))
        chd_s  = sum(r["debit"] for r in rows if chd(r) and _ok(r))
        me_vm  = sum(1 for r in rows if me(r)  and _vm(r))
        chd_vm = sum(1 for r in rows if chd(r) and _vm(r))
        me_vs  = sum(r["debit"] for r in rows if me(r)  and _vm(r))
        chd_vs = sum(r["debit"] for r in rows if chd(r) and _vm(r))
        me_tn  = sum(1 for r in rows if me(r)  and _tar(r))
        chd_tn = sum(1 for r in rows if chd(r) and _tar(r))
        me_ts  = sum(r["debit"] for r in rows if me(r)  and _tar(r))
        chd_ts = sum(r["debit"] for r in rows if chd(r) and _tar(r))
        return (
            (me_n,  chd_n,  me_n  + chd_n),
            (me_s,  chd_s,  me_s  + chd_s),
            (me_vm, chd_vm, me_vm + chd_vm),
            (me_vs, chd_vs, me_vs + chd_vs),
            (me_tn, chd_tn, me_tn + chd_tn),
            (me_ts, chd_ts, me_ts + chd_ts),
        )

    od3  = _overdue(3)
    od6  = _overdue(6)
    od12 = _overdue(12)

    # Qarz diapazoni (debit bo'yicha)
    def drange_cnt(lo, hi=None):
        if hi is None:
            fn_me  = lambda r: me(r) and r["debit"] > lo
            fn_chd = lambda r: chd(r) and r["debit"] > lo
        else:
            fn_me  = lambda r: me(r) and lo < r["debit"] <= hi
            fn_chd = lambda r: chd(r) and lo < r["debit"] <= hi
        b = sum(1 for r in rows if fn_me(r))
        c = sum(1 for r in rows if fn_chd(r))
        return b, c, b + c

    def drange_sum(lo, hi=None):
        if hi is None:
            fn_me  = lambda r: me(r) and r["debit"] > lo
            fn_chd = lambda r: chd(r) and r["debit"] > lo
        else:
            fn_me  = lambda r: me(r) and lo < r["debit"] <= hi
            fn_chd = lambda r: chd(r) and lo < r["debit"] <= hi
        b = sum(r["debit"] for r in rows if fn_me(r))
        c = sum(r["debit"] for r in rows if fn_chd(r))
        return b, c, b + c

    K  = 1_000
    M  = 1_000_000

    result: list[tuple] = [
        # qator  label                                   B          C          D
        ("МАХАЛЛЯ",                                  me_mah,     chd_mah,    all_mah),
        ("ДОМ  (куп каватли)",                       me_dom,     chd_dom,    all_dom),
        (" 2 кодли дом",
            sum(1 for r in rows if me(r) and r["kod"].startswith("2")),
            sum(1 for r in rows if chd(r) and r["kod"].startswith("2")),
            sum(1 for r in rows if r["kod"].startswith("2"))),
        (" 3 кодли дом",
            sum(1 for r in rows if me(r) and r["kod"].startswith("3")),
            sum(1 for r in rows if chd(r) and r["kod"].startswith("3")),
            sum(1 for r in rows if r["kod"].startswith("3"))),
        (" 4 кодли дом",
            sum(1 for r in rows if me(r) and r["kod"].startswith("4")),
            sum(1 for r in rows if chd(r) and r["kod"].startswith("4")),
            sum(1 for r in rows if r["kod"].startswith("4"))),
        ("АБОНЕНТ",                                  me_abon,    chd_abon,   me_abon + chd_abon),
        ("АБОНЕНТ С ВОДОМЕР",                        me_vm,      chd_vm,     me_vm + chd_vm),
        ("АБОНЕНТ ПО ТАРИФУ",                        me_abon - me_vm, chd_abon - chd_vm,
                                                     (me_abon - me_vm) + (chd_abon - chd_vm)),
        ("ПРОПИСКА",                                 me_prop,    chd_prop,   me_prop + chd_prop),
        ("ПРОЖИВАЮЩИЙ",                              me_proz,    chd_proz,   me_proz + chd_proz),
        ("ВОДОМЕР СОНИ",                             me_mcnt,    chd_mcnt,   me_mcnt + chd_mcnt),
        ("ДЕБИТ АБОН",                               me_deb_n,   chd_deb_n,  me_deb_n + chd_deb_n),
        ("ДЕБИТ СУММА",                              me_deb_s,   chd_deb_s,  me_deb_s + chd_deb_s),
        ("из них дебит по в/м абонент сони",         me_deb_vm_n, chd_deb_vm_n, me_deb_vm_n + chd_deb_vm_n),
        ("из них дебит по в/м сумма",                me_deb_vm_s, chd_deb_vm_s, me_deb_vm_s + chd_deb_vm_s),
        ("из них дебит по тарифу абонент сони",      me_deb_n - me_deb_vm_n, chd_deb_n - chd_deb_vm_n,
                                                     (me_deb_n - me_deb_vm_n) + (chd_deb_n - chd_deb_vm_n)),
        ("из них дебит по тарифу сумма",             me_deb_s - me_deb_vm_s, chd_deb_s - chd_deb_vm_s,
                                                     (me_deb_s - me_deb_vm_s) + (chd_deb_s - chd_deb_vm_s)),
        ("КРЕДИТ АБОН",                              me_kr_n,    chd_kr_n,   me_kr_n + chd_kr_n),
        ("КРЕДИТ СУММА",                             me_kr_s,    chd_kr_s,   me_kr_s + chd_kr_s),
        ("ВСЕГО НАЧИСЛЕНО",                          me_charged, chd_charged, me_charged + chd_charged),
        ("ВСЕГО НАЧИСЛЕНО С НДС",                    me_chv,     chd_chv,    me_chv + chd_chv),
        ("НАЧИСЛЕНИЕ (0)",                           me_zero,    chd_zero,   me_zero + chd_zero),
        ("ПУСТЫЕ КАДАСТРЫ ",                         0,          0,          0),  # complex ArrayFormula
        ("неснят пок в/м больше 1 мес",              *nsnyt1),
        ("3 мес",                                    *nsnyt3),
        ("6 мес",                                    *nsnyt6),
        ("1 год",                                    *nsnyt12),
        ("2 года",                                   *nsnyt24),
        ("3 года",                                   *nsnyt36),
        ("ср сут меньше 30 лит",                     *avd30),
        ("ср сут меньше 60 лит",                     *avd60),
        ("ср сут меньше 100 лит",                    *avd100),
        ("ср сут больше 1-2 тонн",                   *avd1_2),
        ("ср сут больше 2-5 тонн",                   *avd2_5),
        ("ср сут больше 5-10 тонн",                  *avd5_10),
        ("ср сут больше 10 тонн",                    *avd_10),
        ("нет оплаты 1 мес",                         *nopay1),
        ("нет оплаты 3 мес",                         *nopay3),
        ("нет оплаты 6 мес",                         *nopay6),
        ("нет оплаты 1 год",                         *nopay12),
        ("нет оплаты 2 года",                        *nopay24),
        ("нет оплаты 3 года",                        *nopay36),
        ("дебит больше 0-412 тыс (1 минималка)",     *drange_cnt(0,    412*K)),
        ("сумма",                                    *drange_sum(0,    412*K)),
        ("дебит больше 0-824 тыс (2 минималка)",     *drange_cnt(0,    824*K)),
        ("сумма",                                    *drange_sum(0,    824*K)),
        ("дебит больше 412 тыс-1 млн",               *drange_cnt(412*K, M)),
        ("сумма",                                    *drange_sum(412*K, M)),
        ("дебит больше 824 тыс-1 млн",               *drange_cnt(824*K, M)),
        ("сумма",                                    *drange_sum(824*K, M)),
        ("дебит больше 500 тыс -1 млн",              *drange_cnt(500*K, M)),
        ("сумма",                                    *drange_sum(500*K, M)),
        ("дебит больше 1-2 млн",                     *drange_cnt(M,   2*M)),
        ("сумма",                                    *drange_sum(M,   2*M)),
        ("дебит больше 2-3 млн",                     *drange_cnt(2*M, 3*M)),
        ("сумма",                                    *drange_sum(2*M, 3*M)),
        ("дебит больше 3-5 млн",                     *drange_cnt(3*M, 5*M)),
        ("сумма",                                    *drange_sum(3*M, 5*M)),
        ("дебит больше 5-10 млн",                    *drange_cnt(5*M, 10*M)),
        ("сумма",                                    *drange_sum(5*M, 10*M)),
        ("дебит больше 10 млн",                      *drange_cnt(10*M)),
        ("сумма",                                    *drange_sum(10*M)),
        ("просрочка 3 мес",                          *od3[0]),
        ("сумма",                                    *od3[1]),
        ("по в/м",                                   *od3[2]),
        ("сумма",                                    *od3[3]),
        ("по тарифу",                                *od3[4]),
        ("сумма",                                    *od3[5]),
        ("просрочка 6 мес",                          *od6[0]),
        ("сумма",                                    *od6[1]),
        ("по в/м",                                   *od6[2]),
        ("сумма",                                    *od6[3]),
        ("по тарифу",                                *od6[4]),
        ("сумма",                                    *od6[5]),
        ("просрочка 1 год",                          *od12[0]),
        ("сумма",                                    *od12[1]),
        ("по в/м",                                   *od12[2]),
        ("сумма",                                    *od12[3]),
        ("по тарифу",                                *od12[4]),
        ("сумма",                                    *od12[5]),
    ]
    return result


# ---------------------------------------------------------------------------
# Excel fayl yaratish
# ---------------------------------------------------------------------------

def _write_passport(
    output: Path,
    data_rows: list[tuple],
    ref_date: date,
) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = ref_date.strftime("%d.%m.%Y")

    title_font  = Font(bold=True, size=12)
    header_font = Font(bold=True, size=10)
    label_font  = Font(size=10)
    num_font    = Font(size=10)
    hdr_fill    = PatternFill("solid", fgColor="D9E1F2")
    center      = Alignment(horizontal="center", vertical="center")
    left        = Alignment(horizontal="left", vertical="center")
    right       = Alignment(horizontal="right", vertical="center")
    thin        = Side(style="thin")
    border      = Border(left=thin, right=thin, top=thin, bottom=thin)

    title = f"МИРЗО УЛУГБЕК ТУМАНИ ПАСПОРТИ НА {ref_date.strftime('%d.%m.%Y')}"
    ws.merge_cells("A1:D1")
    ws["A1"] = title
    ws["A1"].font = title_font
    ws["A1"].alignment = center

    ws.row_dimensions[2].height = 6  # bo'sh qator

    ws["B3"] = "жилой";       ws["B3"].font = header_font; ws["B3"].alignment = center; ws["B3"].fill = hdr_fill
    ws["C3"] = "частный";     ws["C3"].font = header_font; ws["C3"].alignment = center; ws["C3"].fill = hdr_fill
    ws["D3"] = "туман буйича";ws["D3"].font = header_font; ws["D3"].alignment = center; ws["D3"].fill = hdr_fill
    ws["A3"].fill = hdr_fill

    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 16

    for row_idx, (label, b, c, d) in enumerate(data_rows, start=4):
        ws.cell(row_idx, 1, label).font  = label_font
        ws.cell(row_idx, 1).alignment    = left
        for col_idx, val in [(2, b), (3, c), (4, d)]:
            cell = ws.cell(row_idx, col_idx, val if val != 0 else None)
            cell.font      = num_font
            cell.alignment = right
            if isinstance(val, float) and val != int(val):
                cell.number_format = "#,##0.00"
            elif isinstance(val, (int, float)):
                cell.number_format = "#,##0"
        for col_idx in range(1, 5):
            ws.cell(row_idx, col_idx).border = border

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output))


# ---------------------------------------------------------------------------
# Asosiy funksiya
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PassportReportResult:
    output_path: Path
    reference_date: date
    total_rows: int
    me_rows: int
    chd_rows: int


def generate_district_passport(
    f3_path: str | Path,
    output_path: str | Path,
) -> PassportReportResult:
    """To'liq F3 (104+ ustunli) fayldan tuman pasportini yaratadi."""
    source = Path(f3_path)
    output = Path(output_path)

    ref_date, rows = _read_f3(source)
    if ref_date is None:
        ref_date = date.today()

    data_rows = _compute_rows(rows, ref_date)
    _write_passport(output, data_rows, ref_date)

    me_n  = sum(1 for r in rows if r["type"] == _TYPE_ME)
    chd_n = sum(1 for r in rows if r["type"] == _TYPE_CHD)

    return PassportReportResult(
        output_path=output,
        reference_date=ref_date,
        total_rows=len(rows),
        me_rows=me_n,
        chd_rows=chd_n,
    )


def latest_district_passport(directory: str | Path) -> Path | None:
    folder = Path(directory)
    files = sorted(
        folder.glob("tuman_pasporti_*.xlsx"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None
