import json
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from techi_scraper.dates import parse_article_date
from techi_scraper.discover import slug_from_url


@dataclass
class ArticleMeta:
    url: str
    slug: str
    title: str
    category: str
    author_handle: str
    date_text: str
    date_iso: str

    def as_dict(self) -> dict[str, str]:
        return {
            "url": self.url,
            "slug": self.slug,
            "title": self.title,
            "category": self.category,
            "author_handle": self.author_handle,
            "date_text": self.date_text,
            "date_iso": self.date_iso,
        }


def meta_content(soup, *keys: str) -> str:
    for key in keys:
        tag = soup.find("meta", property=key) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return ""


def author_handle(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("name", "url", "@id"):
            if value.get(key):
                return author_handle(value[key])
        return ""

    text = str(value).strip()
    if text.startswith("http"):
        parts = urlparse(text).path.strip("/").split("/")
        text = parts[-1] if parts and parts[-1] else ""
    return text.lstrip("@").strip()


def clean_title(title: str) -> str:
    text = title.strip()
    for suffix in (" | TECHi", " | techi", " - TECHi"):
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
    return text


def load_json_ld(soup) -> list[dict]:
    items = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            items.extend(x for x in data if isinstance(x, dict))
        elif isinstance(data, dict):
            if isinstance(data.get("@graph"), list):
                items.extend(x for x in data["@graph"] if isinstance(x, dict))
            else:
                items.append(data)
    return items


def extract_article_metadata(html: str, fetched_url: str, reference=None) -> ArticleMeta:
    soup = BeautifulSoup(html, "html.parser")

    link = soup.find("link", rel="canonical")
    url = (link.get("href") if link else "") or meta_content(soup, "og:url") or fetched_url
    url = str(url).strip()

    title = meta_content(soup, "og:title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else ""

    category = meta_content(soup, "article:section", "og:section")
    author = meta_content(soup, "author", "article:author", "og:article:author")
    date_text = meta_content(
        soup,
        "article:published_time",
        "og:article:published_time",
        "publish-date",
        "date",
        "DC.date.issued",
    )

    for obj in load_json_ld(soup):
        if not title and obj.get("headline"):
            title = str(obj["headline"]).strip()
        if not date_text:
            for key in ("datePublished", "dateCreated", "dateModified"):
                if obj.get(key):
                    date_text = str(obj[key]).strip()
                    break
        if not author and obj.get("author"):
            author = author_handle(obj["author"])
        if not category:
            section = obj.get("articleSection") or obj.get("genre")
            if isinstance(section, list) and section:
                category = str(section[0])
            elif section:
                category = str(section).strip()

    time_tag = soup.find("time")
    visible = time_tag.get_text(" ", strip=True) if time_tag else ""
    if not date_text and time_tag:
        date_text = (time_tag.get("datetime") or visible or "").strip()

    if not author:
        rel = soup.find("a", rel="author")
        if rel:
            author = rel.get_text(" ", strip=True)

    if not category:
        crumb = soup.select_one(".cat-links a, .category a, a[rel=category tag]")
        if crumb:
            category = crumb.get_text(" ", strip=True)

    display = visible or date_text
    parsed = parse_article_date(display or date_text, reference=reference) if (display or date_text) else None
    date_iso = parsed.date_iso if parsed else ""

    return ArticleMeta(
        url=url,
        slug=slug_from_url(url),
        title=clean_title(title),
        category=category,
        author_handle=author_handle(author),
        date_text=display or date_text,
        date_iso=date_iso,
    )
