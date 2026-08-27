from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import clean as cleaner


FIXTURE = Path(__file__).resolve().parents[1] / "data" / "raw" / "renewals_raw.csv"


class TestDateParser:
    def test_dd_mm_yyyy(self):
        result = cleaner.parse_date("25/12/2025")
        assert result.kind == "ok"
        assert result.value == date(2025, 12, 25)

    def test_mm_dd_yyyy(self):
        result = cleaner.parse_date("12/25/2025")
        assert result.kind == "ok"
        assert result.value == date(2025, 12, 25)

    def test_iso(self):
        result = cleaner.parse_date("2025-11-30")
        assert result.kind == "ok"
        assert result.value == date(2025, 11, 30)

    def test_ambiguous(self):
        result = cleaner.parse_date("03/04/2025")
        assert result.kind == "ambiguous"
        assert result.value is None

    def test_same_under_both_readings(self):
        result = cleaner.parse_date("05/05/2025")
        assert result.kind == "ok"
        assert result.value == date(2025, 5, 5)

    def test_impossible(self):
        result = cleaner.parse_date("31/02/2025")
        assert result.kind == "invalid"
        assert result.value is None

    def test_blank(self):
        result = cleaner.parse_date("  ")
        assert result.kind == "blank"

    def test_malformed(self):
        result = cleaner.parse_date("not-a-date")
        assert result.kind == "invalid"


class TestMoneyParser:
    def test_pkr_prefix_commas(self):
        result = cleaner.parse_money("PKR 2,500")
        assert result.kind == "ok"
        assert result.amount_pkr == Decimal("2500")

    def test_pkr_suffix(self):
        result = cleaner.parse_money("2,500 PKR")
        assert result.kind == "ok"
        assert result.amount_pkr == Decimal("2500")

    def test_rs(self):
        result = cleaner.parse_money("Rs. 2500")
        assert result.kind == "ok"
        assert result.amount_pkr == Decimal("2500")

    def test_plain(self):
        assert cleaner.parse_money("2500").amount_pkr == Decimal("2500")

    def test_decimal(self):
        assert cleaner.parse_money("2500.50").amount_pkr == Decimal("2500.50")

    def test_parentheses(self):
        result = cleaner.parse_money("(2500)")
        assert result.kind == "ok"
        assert result.amount_pkr == Decimal("-2500")

    def test_negative(self):
        assert cleaner.parse_money("-1500").amount_pkr == Decimal("-1500")

    def test_blank(self):
        assert cleaner.parse_money("").kind == "blank"

    def test_malformed(self):
        assert cleaner.parse_money("abc").kind == "malformed"

    def test_usd(self):
        result = cleaner.parse_money("$45.00 USD")
        assert result.kind == "usd"
        assert result.amount_pkr is None


class TestDomainParser:
    def test_case(self):
        assert cleaner.canonicalize_domain("Example.COM").domain == "example.com"

    def test_plain(self):
        assert cleaner.canonicalize_domain("example.com").domain == "example.com"

    def test_https_trailing_slash(self):
        assert cleaner.canonicalize_domain("https://example.com/").domain == "example.com"

    def test_http(self):
        assert cleaner.canonicalize_domain("http://example.com").domain == "example.com"

    def test_www(self):
        assert cleaner.canonicalize_domain("www.example.com").domain == "example.com"

    def test_subdomain_preserved(self):
        assert cleaner.canonicalize_domain("www.blog.example.com").domain == "blog.example.com"

    def test_blank(self):
        assert cleaner.canonicalize_domain("").kind == "blank"

    def test_malformed(self):
        assert cleaner.canonicalize_domain("not a domain!!!").kind == "malformed"


class TestStatusAndEmail:
    def test_status_normalisation(self):
        assert cleaner.normalize_status("ACTIVE").status == "active"
        assert cleaner.normalize_status("Canceled").status == "cancelled"
        assert cleaner.normalize_status("Suspended").status == "suspended"
        assert cleaner.normalize_status("weird").status == "unknown"

    def test_email(self):
        assert cleaner.validate_email("Alice@Example.com").email == "alice@example.com"
        assert cleaner.validate_email("not-an-email").kind == "malformed"
        assert cleaner.validate_email("").kind == "blank"


class TestPipeline:
    def test_fixture_pipeline_schema_and_issues(self, tmp_path: Path):
        assert FIXTURE.exists(), "synthetic renewals_raw.csv fixture must exist"
        raw = cleaner.read_input_csv(FIXTURE)
        result = cleaner.run_pipeline(raw)

        clean_path = tmp_path / "clean.csv"
        issues_path = tmp_path / "issues.csv"
        cleaner.write_clean_csv(clean_path, result.kept_rows)
        cleaner.write_issues_csv(issues_path, result.issues)

        kept_ids = {r.record_id for r in result.kept_rows}
        assert "SYN-005" not in kept_ids
        assert "SYN-006" not in kept_ids
        assert "SYN-008" not in kept_ids
        assert "SYN-009" not in kept_ids
        assert "SYN-011" not in kept_ids
        assert "SYN-014" not in kept_ids and "SYN-015" not in kept_ids
        assert "SYN-020" not in kept_ids
        assert "SYN-012" in kept_ids
        assert "SYN-013" not in kept_ids
        assert any(r.record_id == "SYN-016" and r.status == "cancelled" for r in result.kept_rows)
        assert any(r.record_id == "SYN-017" and r.status == "suspended" for r in result.kept_rows)
        refund = next(r for r in result.kept_rows if r.record_id == "SYN-007")
        assert refund.amount_pkr < 0

        for row in result.kept_rows:
            assert set(row.as_dict()) == set(cleaner.CLEAN_COLUMNS)

        issue_rows = cleaner.read_input_csv(issues_path)
        assert issue_rows
        assert set(issue_rows[0]) == set(cleaner.ISSUE_COLUMNS)
        assert any(i["record_id"] == "SYN-005" for i in issue_rows)
        assert any("conflicting" in i["problem"] for i in issue_rows)
        assert any(i["record_id"] == "SYN-013" for i in issue_rows)

    def test_conflicting_duplicates_unit(self):
        issues = cleaner.IssueLog()
        rows = [
            cleaner.CleanRow(
                record_id="A",
                customer_id="C1",
                domain="x.com",
                service="VPS",
                billing_cycle_months=12,
                amount_pkr=Decimal("100"),
                registered_on=date(2024, 1, 1),
                renews_on=date(2025, 8, 1),
                status="active",
                contact_email="a@x.com",
            ),
            cleaner.CleanRow(
                record_id="B",
                customer_id="C1",
                domain="x.com",
                service="VPS",
                billing_cycle_months=12,
                amount_pkr=Decimal("200"),
                registered_on=date(2024, 1, 1),
                renews_on=date(2025, 8, 1),
                status="active",
                contact_email="a@x.com",
            ),
        ]
        kept = cleaner.resolve_duplicates(rows, issues)
        assert kept == []
        assert len(issues.items) == 2
