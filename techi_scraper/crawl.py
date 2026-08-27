import csv
import logging
import time
from datetime import datetime
from pathlib import Path

from techi_scraper.cache import DiskCache
from techi_scraper.constants import (
    DEFAULT_CACHE_DIR,
    DEFAULT_OUTPUT,
    MAX_ARTICLES,
    MIN_REQUEST_INTERVAL_SECONDS,
    OUTPUT_COLUMNS,
)
from techi_scraper.discover import discover_article_urls
from techi_scraper.fetch import PoliteFetcher
from techi_scraper.metadata import ArticleMeta, extract_article_metadata

logger = logging.getLogger("techi_audit")


def write_articles_csv(path: Path, rows: list[ArticleMeta]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def collect_articles(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    output_path: Path = DEFAULT_OUTPUT,
    limit: int = MAX_ARTICLES,
    reference: datetime | None = None,
) -> list[ArticleMeta]:
    logger.info("Starting TECHi metadata collection (limit=%s)", limit)
    logger.info(
        "Polite crawl: %.0fs pause between each article request",
        MIN_REQUEST_INTERVAL_SECONDS,
    )

    fetcher = PoliteFetcher(DiskCache(cache_dir))
    fetcher.load_robots()

    urls = discover_article_urls(fetcher, limit=limit)
    logger.info("Discovery complete: %s article URL(s) selected", len(urls))

    write_articles_csv(output_path, [])
    articles = []

    for index, url in enumerate(urls, start=1):
        prefix = f"[{index}/{len(urls)}]"

        if index > 1:
            logger.info(
                "%s Waiting %.0f seconds before next request...",
                prefix,
                MIN_REQUEST_INTERVAL_SECONDS,
            )
            time.sleep(MIN_REQUEST_INTERVAL_SECONDS)
            fetcher.mark_activity()

        logger.info("%s Requesting %s", prefix, url)
        body = fetcher.fetch_text(url, respect_robots=True)
        if not body:
            logger.info("%s Skipped - empty response", prefix)
            continue

        try:
            meta = extract_article_metadata(body, url, reference=reference)
        except Exception as exc:
            logger.warning("%s Parse failed: %s", prefix, exc)
            continue

        if not meta.title and not meta.slug:
            logger.info("%s Skipped - insufficient metadata", prefix)
            continue

        articles.append(meta)
        write_articles_csv(output_path, articles)

        title = (meta.title[:72] + "...") if len(meta.title) > 72 else meta.title
        logger.info("%s Saved (%s/%s) %s", prefix, len(articles), limit, title or meta.slug)

        if len(articles) >= limit:
            break

    logger.info(
        "Collection finished: %s article(s) written to %s",
        len(articles),
        output_path,
    )
    return articles
