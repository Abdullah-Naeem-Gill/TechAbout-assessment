import csv
from pathlib import Path

from renewal_cleaner.constants import CLEAN_COLUMNS, ISSUE_COLUMNS
from renewal_cleaner.issues import IssueLog
from renewal_cleaner.models import CleanRow


def read_input_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def write_clean_csv(path: Path, rows: list[CleanRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CLEAN_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def write_issues_csv(path: Path, issues: IssueLog) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ISSUE_COLUMNS)
        writer.writeheader()
        for item in issues.items:
            writer.writerow(
                {
                    "record_id": item.record_id,
                    "field": item.field,
                    "raw_value": item.raw_value,
                    "problem": item.problem,
                    "action_taken": item.action_taken,
                }
            )
