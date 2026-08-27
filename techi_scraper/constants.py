from pathlib import Path

USER_AGENT = (
    "TechAboutAssessmentBot/1.0 (+assessment; polite metadata reader; contact: candidate)"
)
DEFAULT_OUTPUT = Path("data/processed/techi_articles.csv")
DEFAULT_CACHE_DIR = Path(".cache/techi")
MAX_ARTICLES = 20
MIN_REQUEST_INTERVAL_SECONDS = 5.0
REQUEST_TIMEOUT_SECONDS = 20
ROBOTS_URL = "https://www.techi.com/robots.txt"
BASE_NETLOC = "www.techi.com"

OUTPUT_COLUMNS = [
    "url",
    "slug",
    "title",
    "category",
    "author_handle",
    "date_text",
    "date_iso",
]
