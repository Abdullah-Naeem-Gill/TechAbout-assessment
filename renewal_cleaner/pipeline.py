from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from renewal_cleaner.constants import DEFAULT_CLEAN_CSV, DEFAULT_ISSUES_CSV
from renewal_cleaner.csv_io import read_input_csv, write_clean_csv, write_issues_csv
from renewal_cleaner.duplicates import resolve_duplicates
from renewal_cleaner.issues import IssueLog
from renewal_cleaner.models import CleanRow
from renewal_cleaner.money import format_amount
from renewal_cleaner.validate import (
    WINDOW_END,
    WINDOW_START,
    is_synthetic_fixture,
    normalize_row,
    payable_window_total,
)


@dataclass
class PipelineResult:
    rows_in: int
    kept_rows: list[CleanRow]
    dropped: int
    flagged: int
    issues: IssueLog


def run_pipeline(raw_rows: list[dict]) -> PipelineResult:
    issues = IssueLog()
    cleaned = []
    dropped = 0

    for raw in raw_rows:
        row = normalize_row(raw, issues)
        if row is None:
            dropped += 1
        else:
            cleaned.append(row)

    before_ids = {row.record_id for row in cleaned}
    kept = resolve_duplicates(cleaned, issues)
    after_ids = {row.record_id for row in kept}
    dropped += len(before_ids - after_ids)

    flagged = sum(1 for row in kept if row.flagged)
    return PipelineResult(
        rows_in=len(raw_rows),
        kept_rows=kept,
        dropped=dropped,
        flagged=flagged,
        issues=issues,
    )


def print_summary(result: PipelineResult) -> None:
    status_counts = Counter(row.status for row in result.kept_rows)
    print("PKHosting renewals cleanup summary")
    print(f"  rows in : {result.rows_in}")
    print(f"  kept    : {len(result.kept_rows)}")
    print(f"  dropped : {result.dropped}")
    print(f"  flagged : {result.flagged}")
    print("  totals by status:")
    if status_counts:
        for status in sorted(status_counts):
            print(f"    {status}: {status_counts[status]}")
    else:
        print("    (none)")
    print(f"  issue rows written: {len(result.issues.items)}")

    window_total = payable_window_total(result.kept_rows)
    print(
        f"  payable window {WINDOW_START.isoformat()}..{WINDOW_END.isoformat()}: "
        f"PKR {format_amount(window_total)}"
    )
    if is_synthetic_fixture(result.kept_rows):
        print(
            "  note: synthetic SYN-* fixture only - this is not the official "
            "34-row TechAbout total (see NOTES.md)"
        )


def clean_file(
    input_path: Path,
    clean_path: Path | None = None,
    issues_path: Path | None = None,
) -> PipelineResult:
    clean_path = clean_path or DEFAULT_CLEAN_CSV
    issues_path = issues_path or DEFAULT_ISSUES_CSV
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    issues_path.parent.mkdir(parents=True, exist_ok=True)

    result = run_pipeline(read_input_csv(input_path))
    write_clean_csv(clean_path, result.kept_rows)
    write_issues_csv(issues_path, result.issues)
    print_summary(result)
    print(f"Wrote {clean_path}")
    print(f"Wrote {issues_path}")
    return result
