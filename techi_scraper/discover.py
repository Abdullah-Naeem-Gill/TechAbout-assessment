import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import urldefrag, urlparse

from techi_scraper.constants import MAX_ARTICLES, ROBOTS_URL
from techi_scraper.fetch import PoliteFetcher

logger = logging.getLogger("techi_audit")

SITEMAP_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)

SKIP_PATHS = (
    "/tag/",
    "/tags/",
    "/category/",
    "/categories/",
    "/author/",
    "/authors/",
    "/page/",
    "/search",
    "/login",
    "/wp-admin",
    "/wp-json",
    "/feed",
    "/cdn-cgi/",
)

SKIP_EXTENSIONS = (
    ".xml",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".css",
    ".js",
    ".zip",
    ".pdf",
)


def extract_sitemap_urls_from_robots(robots_text: str) -> list[str]:
    urls = []
    for line in robots_text.splitlines():
        if line.lower().startswith("sitemap:"):
            loc = line.split(":", 1)[1].strip()
            if loc:
                urls.append(loc)
    return urls


def iter_sitemap_locs(xml_text: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
        locs = []
        for el in root.iter():
            if el.tag.lower().endswith("loc") and el.text:
                locs.append(el.text.strip())
        if locs:
            return locs
    except ET.ParseError:
        pass

    return [match.group(1).strip() for match in SITEMAP_LOC_RE.finditer(xml_text)]


def is_techi_article_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    host = (parsed.hostname or "").lower()
    if host not in ("techi.com", "www.techi.com"):
        return False

    path = parsed.path or "/"
    if path in ("", "/"):
        return False

    lower = path.lower()
    if any(part in lower for part in SKIP_PATHS):
        return False
    if lower.endswith(SKIP_EXTENSIONS):
        return False
    if "sitemap" in lower or lower.endswith("robots.txt"):
        return False

    slug = path.strip("/").split("/")[-1]
    if not slug or slug.isdigit():
        return False
    if "." in slug and not slug.endswith(".html"):
        return False

    return True


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return ""
    slug = path.split("/")[-1]
    if slug.endswith(".html"):
        slug = slug[:-5]
    return slug


def discover_article_urls(fetcher: PoliteFetcher, limit: int = MAX_ARTICLES) -> list[str]:
    if fetcher.robots_loaded and fetcher.robots_text:
        robots_body = fetcher.robots_text
    else:
        robots_body = fetcher.fetch_text(ROBOTS_URL, respect_robots=False)
        if robots_body is None:
            logger.error("Discovery aborted: robots.txt is unavailable")
            return []
        fetcher.robots.parse(robots_body.splitlines())
        fetcher.robots_loaded = True
        fetcher.robots_text = robots_body

    sitemap_urls = extract_sitemap_urls_from_robots(robots_body)
    if not sitemap_urls:
        sitemap_urls = [
            "https://www.techi.com/sitemap.xml",
            "https://www.techi.com/sitemap_index.xml",
        ]

    pending = list(dict.fromkeys(sitemap_urls))
    seen_sitemaps = set()
    articles = []
    seen_articles = set()

    while pending and len(articles) < limit:
        sm_url = pending.pop(0)
        if sm_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sm_url)

        if not fetcher.allowed(sm_url):
            logger.info("Sitemap skipped (robots.txt): %s", sm_url)
            continue

        body = fetcher.fetch_text(sm_url, respect_robots=True)
        if not body:
            continue

        for loc in iter_sitemap_locs(body):
            loc, _ = urldefrag(loc)

            if loc.endswith(".xml") or "sitemap" in loc.lower():
                if loc not in seen_sitemaps:
                    pending.append(loc)
                continue

            if not is_techi_article_url(loc):
                continue
            if not fetcher.allowed(loc):
                continue
            if loc in seen_articles:
                continue

            seen_articles.add(loc)
            articles.append(loc)
            if len(articles) >= limit:
                break

    return articles
