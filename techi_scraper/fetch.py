import logging
import time
from urllib import robotparser
from urllib.parse import urldefrag

import requests

from techi_scraper.cache import DiskCache
from techi_scraper.constants import (
    MIN_REQUEST_INTERVAL_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    ROBOTS_URL,
    USER_AGENT,
)

logger = logging.getLogger("techi_audit")


class PoliteFetcher:
    def __init__(
        self,
        cache: DiskCache,
        user_agent: str = USER_AGENT,
        min_interval: float = MIN_REQUEST_INTERVAL_SECONDS,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.cache = cache
        self.user_agent = user_agent
        self.min_interval = min_interval
        self.timeout = timeout
        self.last_activity_at = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.robots = robotparser.RobotFileParser()
        self.robots_loaded = False
        self.robots_text = ""

    def load_robots(self, robots_url: str = ROBOTS_URL) -> bool:
        try:
            text = self.fetch_text(robots_url, respect_robots=False)
            if text is None:
                logger.warning("Unable to download robots.txt; crawl will be denied by default")
                self.robots_loaded = False
                return False
            self.robots.parse(text.splitlines())
            self.robots_loaded = True
            self.robots_text = text
            logger.info("Loaded robots.txt rules from %s", robots_url)
            return True
        except Exception as exc:
            logger.warning("Failed to parse robots.txt: %s", exc)
            self.robots_loaded = False
            self.robots_text = ""
            return False

    def allowed(self, url: str) -> bool:
        if not self.robots_loaded:
            return False
        try:
            return self.robots.can_fetch(self.user_agent, url)
        except Exception:
            return False

    def wait_before_next(self, label: str = "request") -> None:
        if self.last_activity_at == 0.0:
            return
        elapsed = time.monotonic() - self.last_activity_at
        remaining = self.min_interval - elapsed
        if remaining <= 0:
            return
        logger.info(
            "Waiting %.1f seconds before next %s (polite %ss gap)",
            remaining,
            label,
            self.min_interval,
        )
        time.sleep(remaining)

    def mark_activity(self) -> None:
        self.last_activity_at = time.monotonic()

    def fetch_text(self, url: str, respect_robots: bool = True) -> str | None:
        url, _ = urldefrag(url)

        cached = self.cache.get(url)
        if cached is not None:
            status = int(cached.get("status_code", 0))
            if 200 <= status < 300:
                logger.info("Cache hit [%s] %s", status, url)
                return str(cached.get("body", ""))
            logger.info("Cache hit (non-success %s) %s", status, url)
            return None

        if respect_robots and not self.allowed(url):
            logger.info("Blocked by robots.txt: %s", url)
            return None

        self.wait_before_next("request")
        logger.info("GET %s", url)
        self.mark_activity()

        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.Timeout:
            logger.warning("Request timed out: %s", url)
            return None
        except requests.RequestException as exc:
            logger.warning("Request error for %s: %s", url, exc)
            return None

        body = response.text or ""
        content_type = response.headers.get("Content-Type", "")
        size = len(body.encode("utf-8", errors="ignore"))
        self.mark_activity()

        if 200 <= response.status_code < 300:
            self.cache.set(url, response.status_code, body, content_type)
            logger.info("Response %s (%s bytes) %s", response.status_code, size, url)
            return body

        self.cache.set(url, response.status_code, "", content_type)
        logger.warning("Response %s %s", response.status_code, url)
        return None
