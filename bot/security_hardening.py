from __future__ import annotations

import re
import zipfile
from pathlib import Path


MAX_XLSX_ENTRIES = 2_000
MAX_XLSX_UNCOMPRESSED_BYTES = 300 * 1024 * 1024
MAX_XLSX_MEMBER_BYTES = 250 * 1024 * 1024
MAX_XLSX_COMPRESSION_RATIO = 100
FORBIDDEN_XLSX_PARTS = (
    "vbaproject",
    "activex",
    "embeddings/",
    "oleobject",
    "externallinks/",
    "connections.xml",
)
FORBIDDEN_FORMULA_MARKERS = (
    "WEBSERVICE(",
    "FILTERXML(",
    "HYPERLINK(\"HTTP",
    "HYPERLINK(\"FTP",
    "CMD|",
    "POWERSHELL",
    "MSHTA",
)


class UnsafeOfficeFile(RuntimeError):
    pass


def validate_safe_xlsx(path: str | Path) -> None:
    source = Path(path)
    if not zipfile.is_zipfile(source):
        raise UnsafeOfficeFile("Fayl haqiqiy XLSX/OOXML arxivi emas.")
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_XLSX_ENTRIES:
            raise UnsafeOfficeFile("XLSX ichidagi fayllar soni xavfsizlik limitidan oshgan.")
        names = {item.filename for item in entries}
        if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
            raise UnsafeOfficeFile("XLSX majburiy tuzilmasi topilmadi.")

        total_size = 0
        for item in entries:
            normalized = item.filename.replace("\\", "/").lower()
            if normalized.startswith("/") or ".." in Path(normalized).parts:
                raise UnsafeOfficeFile("XLSX ichida xavfli fayl yo'li aniqlandi.")
            if any(marker in normalized for marker in FORBIDDEN_XLSX_PARTS):
                raise UnsafeOfficeFile(
                    "XLSX ichida makros, tashqi ulanish yoki biriktirilgan obyekt aniqlandi."
                )
            if item.file_size > MAX_XLSX_MEMBER_BYTES:
                raise UnsafeOfficeFile("XLSX ichidagi bitta qism juda katta.")
            total_size += item.file_size
            if total_size > MAX_XLSX_UNCOMPRESSED_BYTES:
                raise UnsafeOfficeFile("XLSX ochilgandagi hajmi xavfsizlik limitidan oshgan.")
            if (
                item.file_size > 1024 * 1024
                and item.file_size / max(item.compress_size, 1)
                > MAX_XLSX_COMPRESSION_RATIO
            ):
                raise UnsafeOfficeFile("XLSX ZIP bomb belgilariga ega.")

            if normalized.startswith("xl/worksheets/") and normalized.endswith(".xml"):
                payload = archive.read(item)
                upper = payload.upper()
                if any(marker.encode("ascii") in upper for marker in FORBIDDEN_FORMULA_MARKERS):
                    raise UnsafeOfficeFile("XLSX ichida xavfli tashqi formula aniqlandi.")


_TOKEN_PATTERNS = (
    re.compile(r"\b\d{6,15}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(
        r"(?i)\b(BOT_TOKEN|OPENAI_API_KEY|UZWATER_ENCRYPTION_PASSWORD)"
        r"\s*[=:]\s*[^\s;,]+"
    ),
)


def redact_sensitive_text(value: object, maximum: int = 1500) -> str:
    text = str(value or "")
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    try:
        project = str(Path.cwd().resolve())
        text = text.replace(project, "<project>")
        text = text.replace(project.replace("\\", "/"), "<project>")
    except OSError:
        pass
    text = re.sub(r"(?i)(password|parol|secret|token)\s*[=:]\s*\S+", r"\1=[REDACTED]", text)
    return text[: max(maximum, 0)]


def safe_exception_summary(error: BaseException) -> str:
    message = redact_sensitive_text(error, 600).strip()
    error_type = type(error).__name__
    return f"{error_type}: {message}" if message else error_type
