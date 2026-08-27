import re
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DateParseResult:
    value: date | None
    problem: str | None
    kind: str


def make_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_date(raw) -> DateParseResult:
    if raw is None or not str(raw).strip():
        return DateParseResult(None, "blank date", "blank")

    text = str(raw).strip()

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return DateParseResult(datetime.strptime(text, fmt).date(), None, "ok")
        except ValueError:
            pass

    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%d-%b-%Y", "%d-%B-%Y"):
        try:
            return DateParseResult(datetime.strptime(text, fmt).date(), None, "ok")
        except ValueError:
            pass

    match = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", text)
    if not match:
        return DateParseResult(None, "unrecognised date format", "invalid")

    a = int(match.group(1))
    b = int(match.group(2))
    year = int(match.group(3))

    if a > 31 or b > 31:
        return DateParseResult(None, "impossible date components", "invalid")

    if a > 12 and b <= 12:
        value = make_date(year, b, a)
        if value is None:
            return DateParseResult(None, "impossible calendar date", "invalid")
        return DateParseResult(value, None, "ok")

    if a <= 12 and b > 12:
        value = make_date(year, a, b)
        if value is None:
            return DateParseResult(None, "impossible calendar date", "invalid")
        return DateParseResult(value, None, "ok")

    dmy = make_date(year, b, a)
    mdy = make_date(year, a, b)
    if dmy is None and mdy is None:
        return DateParseResult(None, "impossible calendar date", "invalid")
    if dmy is not None and mdy is not None and dmy != mdy:
        return DateParseResult(None, "ambiguous slash date (DD/MM vs MM/DD)", "ambiguous")
    return DateParseResult(dmy or mdy, None, "ok")


def format_iso(value: date | None) -> str:
    return value.isoformat() if value else ""
