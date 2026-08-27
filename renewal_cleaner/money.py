import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

CURRENCY_RE = re.compile(r"(?i)(\bpkr\b|\brupees?\b|\busd\b|\brs\.?|us\$|\$)")
USD_RE = re.compile(r"(?i)(\busd\b|us\$|\$)")


@dataclass(frozen=True)
class MoneyParseResult:
    amount_pkr: Decimal | None
    currency: str | None
    problem: str | None
    kind: str


def parse_money(raw) -> MoneyParseResult:
    if raw is None or not str(raw).strip():
        return MoneyParseResult(None, None, "blank amount", "blank")

    text = str(raw).strip()
    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    if USD_RE.search(str(raw)) and not re.search(r"(?i)\bpkr\b|\brs\.?\b", str(raw)):
        return MoneyParseResult(None, "USD", "USD amount without authorised PKR conversion", "usd")

    cleaned = CURRENCY_RE.sub(" ", text).replace(",", "").strip()
    if cleaned.startswith("-"):
        negative = True
        cleaned = cleaned[1:].strip()
    elif cleaned.startswith("+"):
        cleaned = cleaned[1:].strip()

    if not cleaned or not re.fullmatch(r"\d+(\.\d+)?", cleaned):
        return MoneyParseResult(None, None, "malformed amount", "malformed")

    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return MoneyParseResult(None, None, "malformed amount", "malformed")

    if negative:
        value = -value
    return MoneyParseResult(value, "PKR", None, "ok")


def format_amount(value: Decimal | None) -> str:
    if value is None:
        return ""
    if "." in str(value) or value % 1:
        value = value.quantize(Decimal("0.01"))
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
