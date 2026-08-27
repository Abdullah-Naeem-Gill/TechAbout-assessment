import re
from dataclasses import dataclass

from renewal_cleaner.constants import STATUS_MAP

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


@dataclass(frozen=True)
class StatusParseResult:
    status: str
    problem: str | None
    changed: bool


@dataclass(frozen=True)
class EmailParseResult:
    email: str
    problem: str | None
    kind: str


def normalize_status(raw) -> StatusParseResult:
    text = "" if raw is None else str(raw).strip()
    key = re.sub(r"\s+", " ", text.lower())
    mapped = STATUS_MAP.get(key)

    if mapped is None:
        return StatusParseResult("unknown", f"unrecognised status '{text}'", True)

    if not text:
        return StatusParseResult(mapped, "blank status", True)

    if text != mapped:
        return StatusParseResult(mapped, "status casing/wording normalised", True)

    return StatusParseResult(mapped, None, False)


def validate_email(raw) -> EmailParseResult:
    if raw is None:
        return EmailParseResult("", "blank email", "blank")

    text = str(raw).strip()
    if not text:
        return EmailParseResult("", "blank email", "blank")

    if not EMAIL_RE.match(text):
        return EmailParseResult("", "malformed email", "malformed")

    return EmailParseResult(text.lower(), None, "ok")


def parse_billing_cycle(raw) -> tuple[int | None, str | None]:
    if raw is None or str(raw).strip() == "":
        return None, "blank billing_cycle_months"

    text = str(raw).strip()
    try:
        value = int(text)
    except ValueError:
        return None, "non-integer billing_cycle_months"

    if value <= 0:
        return None, "non-positive billing_cycle_months"

    return value, None
