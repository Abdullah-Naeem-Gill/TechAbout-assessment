from collections import defaultdict

from renewal_cleaner.issues import IssueLog
from renewal_cleaner.models import CleanRow
from renewal_cleaner.money import format_amount


def resolve_duplicates(rows: list[CleanRow], issues: IssueLog) -> list[CleanRow]:
    groups = defaultdict(list)
    for row in rows:
        groups[row.identity_key].append(row)

    kept = []
    for key, group in groups.items():
        if len(group) == 1:
            kept.append(group[0])
            continue

        amounts = {format_amount(row.amount_pkr) for row in group}
        ids = ", ".join(row.record_id for row in group)

        if len(amounts) == 1:
            winner = group[0]
            for dup in group[1:]:
                issues.add(
                    dup.record_id,
                    "duplicate",
                    ids,
                    (
                        "identical duplicate of "
                        f"customer={key[0]} domain={key[1]} "
                        f"service={key[2]} renews_on={key[3]}"
                    ),
                    f"merged into {winner.record_id}",
                )
            issues.add(
                winner.record_id,
                "duplicate",
                ids,
                "identical duplicates merged",
                f"kept {winner.record_id}; dropped {len(group) - 1} duplicate(s)",
            )
            winner.flagged = True
            kept.append(winner)
        else:
            for row in group:
                issues.add(
                    row.record_id,
                    "amount_pkr",
                    format_amount(row.amount_pkr),
                    (
                        "duplicate identity with conflicting amounts "
                        f"({', '.join(sorted(amounts))})"
                    ),
                    "row dropped; conflicting duplicates are not silently resolved",
                )

    return kept
