from pathlib import Path

CLEAN_COLUMNS = [
    "record_id",
    "customer_id",
    "domain",
    "service",
    "billing_cycle_months",
    "amount_pkr",
    "registered_on",
    "renews_on",
    "status",
    "contact_email",
]

ISSUE_COLUMNS = [
    "record_id",
    "field",
    "raw_value",
    "problem",
    "action_taken",
]

STATUS_MAP = {
    "active": "active",
    "actve": "active",
    "enabled": "active",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "cancel": "cancelled",
    "suspended": "suspended",
    "suspend": "suspended",
    "paused": "suspended",
    "unknown": "unknown",
    "other": "unknown",
    "": "unknown",
}

CANONICAL_STATUSES = frozenset({"active", "cancelled", "suspended", "unknown"})

DEFAULT_INPUT_CSV = Path("data/raw/renewals_raw.csv")
DEFAULT_CLEAN_CSV = Path("data/processed/clean.csv")
DEFAULT_ISSUES_CSV = Path("data/processed/issues.csv")
