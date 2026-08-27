import argparse
import logging
from pathlib import Path

from techi_scraper.cache import DiskCache
from techi_scraper.constants import DEFAULT_CACHE_DIR, DEFAULT_OUTPUT, MAX_ARTICLES
from techi_scraper.crawl import collect_articles, write_articles_csv
from techi_scraper.dates import ArticleDateResult, parse_article_date
from techi_scraper.discover import (
    discover_article_urls,
    extract_sitemap_urls_from_robots,
    is_techi_article_url,
    slug_from_url,
)
from techi_scraper.fetch import PoliteFetcher
from techi_scraper.metadata import ArticleMeta, extract_article_metadata


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Collect TECHi article metadata")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--limit", type=int, default=MAX_ARTICLES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("techi_audit").setLevel(
        logging.DEBUG if args.verbose else logging.INFO
    )

    articles = collect_articles(
        cache_dir=args.cache_dir,
        output_path=args.output,
        limit=args.limit,
    )
    print(f"Collected {len(articles)} article(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
