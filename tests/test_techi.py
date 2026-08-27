from __future__ import annotations

from datetime import datetime, timezone

import techi_audit as techi


SAMPLE_HTML = """
<!doctype html>
<html>
<head>
  <title>Fallback Title | TECHi</title>
  <link rel="canonical" href="https://www.techi.com/sample-article/" />
  <meta property="og:title" content="Sample Article Title | TECHi" />
  <meta property="og:url" content="https://www.techi.com/sample-article/" />
  <meta property="article:section" content="Gadgets" />
  <meta name="author" content="https://www.techi.com/author/@techiwriter/" />
  <meta property="article:published_time" content="2026-08-20" />
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Sample Article Title | TECHi",
    "datePublished": "2026-08-20T10:00:00+00:00",
    "author": {"@type": "Person", "name": "techiwriter"},
    "articleSection": "Gadgets"
  }
  </script>
</head>
<body>
  <h1>Sample Article Title</h1>
  <time datetime="2026-08-20">August 20, 2026</time>
</body>
</html>
"""


class TestArticleDateParser:
    def test_absolute_named(self):
        result = techi.parse_article_date("August 20, 2026")
        assert result.date_iso == "2026-08-20"
        assert result.date_text == "August 20, 2026"

    def test_iso(self):
        result = techi.parse_article_date("2026-08-20")
        assert result.date_iso == "2026-08-20"

    def test_relative_with_fixed_reference(self):
        ref = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)
        result = techi.parse_article_date("Updated 6 days ago", reference=ref)
        assert result.date_iso == "2026-08-20"
        assert result.date_text == "Updated 6 days ago"

    def test_blank(self):
        result = techi.parse_article_date("")
        assert result.date_iso == ""
        assert result.problem == "blank date"


class TestUrlHelpers:
    def test_article_url_filter(self):
        assert techi.is_techi_article_url("https://www.techi.com/some-cool-gadget/")
        assert not techi.is_techi_article_url("https://www.techi.com/category/phones/")
        assert not techi.is_techi_article_url("https://www.techi.com/tag/ai/")
        assert not techi.is_techi_article_url("https://www.techi.com/author/jane/")
        assert not techi.is_techi_article_url("https://www.techi.com/sitemap.xml")
        assert not techi.is_techi_article_url("https://example.com/post/")

    def test_slug_from_url(self):
        assert techi.slug_from_url("https://www.techi.com/sample-article/") == "sample-article"


class TestHtmlExtraction:
    def test_extract_from_fixture_html(self):
        meta = techi.extract_article_metadata(
            SAMPLE_HTML,
            "https://www.techi.com/sample-article/",
            reference=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
        assert meta.url == "https://www.techi.com/sample-article/"
        assert meta.slug == "sample-article"
        assert meta.title == "Sample Article Title"
        assert meta.category == "Gadgets"
        assert meta.author_handle == "techiwriter"
        assert meta.date_text == "August 20, 2026"
        assert meta.date_iso == "2026-08-20"

    def test_robots_sitemap_extraction(self):
        robots = "User-agent: *\nAllow: /\nSitemap: https://www.techi.com/sitemap_index.xml\n"
        assert techi.extract_sitemap_urls_from_robots(robots) == [
            "https://www.techi.com/sitemap_index.xml"
        ]
