import argparse
import sys
from pathlib import Path

from renewal_cleaner.constants import (
    CLEAN_COLUMNS,
    DEFAULT_CLEAN_CSV,
    DEFAULT_INPUT_CSV,
    DEFAULT_ISSUES_CSV,
    ISSUE_COLUMNS,
)
from renewal_cleaner.csv_io import read_input_csv, write_clean_csv, write_issues_csv
from renewal_cleaner.dates import parse_date
from renewal_cleaner.domains import canonicalize_domain
from renewal_cleaner.duplicates import resolve_duplicates
from renewal_cleaner.issues import IssueLog
from renewal_cleaner.models import CleanRow
from renewal_cleaner.money import parse_money
from renewal_cleaner.pipeline import clean_file, run_pipeline
from renewal_cleaner.status import normalize_status, validate_email


def resolve_input_csv(path: Path) -> Path | None:
    if path.exists():
        return path

    under_raw = Path("data/raw") / path.name
    if under_raw.exists():
        return under_raw

    if DEFAULT_INPUT_CSV.exists() and path.name == DEFAULT_INPUT_CSV.name:
        return DEFAULT_INPUT_CSV

    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Clean PKHosting renewals CSV")
    parser.add_argument("input_csv", type=Path, nargs="?", default=DEFAULT_INPUT_CSV)
    parser.add_argument("--clean-out", type=Path, default=DEFAULT_CLEAN_CSV)
    parser.add_argument("--issues-out", type=Path, default=DEFAULT_ISSUES_CSV)
    args = parser.parse_args(argv)

    input_csv = resolve_input_csv(args.input_csv)
    if input_csv is None:
        print(f"Input not found: {args.input_csv}", file=sys.stderr)
        return 1

    clean_file(input_csv, args.clean_out, args.issues_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
