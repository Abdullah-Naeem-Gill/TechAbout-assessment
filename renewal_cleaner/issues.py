from dataclasses import dataclass, field


@dataclass
class Issue:
    record_id: str
    field: str
    raw_value: str
    problem: str
    action_taken: str


@dataclass
class IssueLog:
    items: list[Issue] = field(default_factory=list)

    def add(self, record_id, field_name, raw_value, problem, action_taken) -> None:
        self.items.append(
            Issue(
                record_id=record_id or "",
                field=field_name,
                raw_value="" if raw_value is None else str(raw_value),
                problem=problem,
                action_taken=action_taken,
            )
        )
