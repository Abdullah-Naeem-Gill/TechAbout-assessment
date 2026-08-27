import re
from dataclasses import dataclass
from urllib.parse import urlparse

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


@dataclass(frozen=True)
class DomainParseResult:
    domain: str | None
    problem: str | None
    kind: str


def canonicalize_domain(raw) -> DomainParseResult:
    if raw is None:
        return DomainParseResult(None, "blank domain", "blank")

    text = str(raw).strip()
    if not text:
        return DomainParseResult(None, "blank domain", "blank")

    value = text
    if "://" in value or value.lower().startswith("www."):
        to_parse = value if "://" in value else f"http://{value}"
        parsed = urlparse(to_parse)
        host = parsed.hostname or ""
        if not host and parsed.path:
            host = parsed.path.split("/")[0]
        value = host or value

    value = value.strip().strip("/")
    if "/" in value:
        value = value.split("/", 1)[0]
    if "?" in value:
        value = value.split("?", 1)[0]

    value = value.strip(".").lower()
    if value.startswith("www."):
        value = value[4:]

    if not value or " " in value or not DOMAIN_RE.match(value):
        return DomainParseResult(None, "malformed domain", "malformed")

    return DomainParseResult(value, None, "ok")
