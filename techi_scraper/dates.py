import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

RELATIVE_RE = re.compile(
    r"(?i)^\s*(?:updated\s+)?(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago\s*$"
)


@dataclass(frozen=True)
class ArticleDateResult:
    date_text: str
    date_iso: str
    problem: str | None = None


def parse_article_date(raw, reference: datetime | None = None) -> ArticleDateResult:
    if raw is None:
        return ArticleDateResult("", "", "blank date")

    text = str(raw).strip()
    if not text:
        return ArticleDateResult("", "", "blank date")

    cleaned = re.sub(r"(?i)^(updated|published|posted)\s+", "", text).strip()
    ref = reference or datetime.now(timezone.utc)

    relative = RELATIVE_RE.match(text) or RELATIVE_RE.match(cleaned)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2).lower()
        deltas = {
            "second": timedelta(seconds=amount),
            "minute": timedelta(minutes=amount),
            "hour": timedelta(hours=amount),
            "day": timedelta(days=amount),
            "week": timedelta(weeks=amount),
            "month": timedelta(days=30 * amount),
            "year": timedelta(days=365 * amount),
        }
        resolved = ref - deltas[unit]
        if resolved.tzinfo is not None:
            day = resolved.astimezone(timezone.utc).date()
        else:
            day = resolved.date()
        return ArticleDateResult(text, day.isoformat())

    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        return ArticleDateResult(text, dt.date().isoformat())
    except ValueError:
        pass

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return ArticleDateResult(text, dt.date().isoformat())
        except ValueError:
            continue

    found = re.search(
        r"(?i)\b("
        r"January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
        r")\s+\d{1,2},\s+\d{4}\b",
        text,
    )
    if found:
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                dt = datetime.strptime(found.group(0), fmt)
                return ArticleDateResult(text, dt.date().isoformat())
            except ValueError:
                continue

    return ArticleDateResult(text, "", "unrecognised article date")
