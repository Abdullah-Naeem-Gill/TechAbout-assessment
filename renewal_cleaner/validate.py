from decimal import Decimal
from datetime import date

from renewal_cleaner.dates import format_iso, parse_date
from renewal_cleaner.domains import canonicalize_domain
from renewal_cleaner.issues import IssueLog
from renewal_cleaner.models import CleanRow
from renewal_cleaner.money import format_amount, parse_money
from renewal_cleaner.status import normalize_status, parse_billing_cycle, validate_email

WINDOW_START = date(2026, 8, 3)
WINDOW_END = date(2026, 9, 2)


def get_field(row: dict, *names: str) -> str:
    fields = {}
    for key, value in row.items():
        if key is None:
            continue
        fields[key.lower().strip()] = "" if value is None else str(value)
    for name in names:
        if name.lower() in fields:
            return fields[name.lower()]
    return ""


def check_date(record_id: str, field: str, raw: str, issues: IssueLog):
    result = parse_date(raw)
    if result.kind != "ok" or result.value is None:
        action = "row dropped"
        if result.kind == "ambiguous":
            action = "row dropped; ambiguous dates are not guessed"
        issues.add(record_id, field, raw, result.problem or "invalid date", action)
        return None

    if raw.strip() and raw.strip() != format_iso(result.value):
        issues.add(
            record_id,
            field,
            raw.strip(),
            "date normalised to ISO",
            f"set to {format_iso(result.value)}",
        )
    return result.value


def normalize_row(raw: dict, issues: IssueLog) -> CleanRow | None:
    record_id = get_field(raw, "record_id").strip()
    if not record_id:
        issues.add("", "record_id", "", "missing record_id", "row dropped")
        return None

    drop = False
    flagged = False

    customer_id = get_field(raw, "customer_id").strip()
    if not customer_id:
        issues.add(record_id, "customer_id", "", "missing customer_id", "row dropped")
        drop = True

    service = get_field(raw, "service").strip()
    if not service:
        issues.add(record_id, "service", "", "missing service", "row dropped")
        drop = True

    billing_raw = get_field(raw, "billing_cycle_months")
    billing, billing_err = parse_billing_cycle(billing_raw)
    if billing_err:
        issues.add(record_id, "billing_cycle_months", billing_raw, billing_err, "row dropped")
        drop = True

    domain_raw = get_field(raw, "domain")
    domain = canonicalize_domain(domain_raw)
    if domain.kind != "ok":
        issues.add(record_id, "domain", domain_raw, domain.problem or "invalid domain", "row dropped")
        drop = True
    elif domain_raw.strip() and domain_raw.strip() != domain.domain:
        issues.add(
            record_id,
            "domain",
            domain_raw.strip(),
            "domain canonicalised",
            f"set to {domain.domain}",
        )

    amount_raw = get_field(raw, "amount", "amount_pkr")
    money = parse_money(amount_raw)
    amount: Decimal | None = None

    if money.kind != "ok" or money.amount_pkr is None:
        action = "row dropped"
        if money.kind == "usd":
            action = "row dropped; USD not converted to PKR"
        issues.add(record_id, "amount", amount_raw, money.problem or "invalid amount", action)
        drop = True
    else:
        amount = money.amount_pkr
        if amount < 0:
            issues.add(
                record_id,
                "amount",
                amount_raw,
                "negative amount treated as refund/credit",
                "kept as negative amount_pkr; excluded from renewal payable totals",
            )
            flagged = True
        if amount_raw.strip() and format_amount(amount) != amount_raw.strip():
            issues.add(
                record_id,
                "amount",
                amount_raw.strip(),
                "amount normalised to PKR numeric",
                f"set to {format_amount(amount)}",
            )

    registered_on = check_date(record_id, "registered_on", get_field(raw, "registered_on"), issues)
    renews_on = check_date(record_id, "renews_on", get_field(raw, "renews_on"), issues)
    if registered_on is None or renews_on is None:
        drop = True

    status_raw = get_field(raw, "status")
    status = normalize_status(status_raw)
    if status.problem:
        issues.add(record_id, "status", status_raw, status.problem, f"set to {status.status}")
    if status.status in ("cancelled", "suspended"):
        issues.add(
            record_id,
            "status",
            status_raw,
            f"service is {status.status}",
            "kept in clean.csv; excluded from renewal payable totals",
        )
        flagged = True

    email_raw = get_field(raw, "contact_email")
    email = validate_email(email_raw)
    if email.kind == "blank":
        issues.add(record_id, "contact_email", email_raw, "blank email", "left blank; row kept if otherwise valid")
        flagged = True
    elif email.kind == "malformed":
        issues.add(record_id, "contact_email", email_raw, "malformed email", "cleared; row kept if otherwise valid")
        flagged = True
    elif email.kind == "ok" and email_raw.strip() and email_raw.strip() != email.email:
        issues.add(
            record_id,
            "contact_email",
            email_raw.strip(),
            "email normalised to lowercase",
            f"set to {email.email}",
        )

    if drop:
        return None

    return CleanRow(
        record_id=record_id,
        customer_id=customer_id,
        domain=domain.domain,
        service=service,
        billing_cycle_months=billing,
        amount_pkr=amount,
        registered_on=registered_on,
        renews_on=renews_on,
        status=status.status,
        contact_email=email.email,
        flagged=flagged,
    )


def payable_window_total(rows: list[CleanRow]) -> Decimal:
    total = Decimal("0")
    for row in rows:
        if row.status != "active":
            continue
        if row.amount_pkr <= 0:
            continue
        if row.renews_on < WINDOW_START or row.renews_on > WINDOW_END:
            continue
        total += row.amount_pkr
    return total


def is_synthetic_fixture(rows: list[CleanRow]) -> bool:
    if not rows:
        return False
    return any(row.record_id.startswith("SYN-") for row in rows)
