from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from renewal_cleaner.dates import format_iso
from renewal_cleaner.money import format_amount


@dataclass
class CleanRow:
    record_id: str
    customer_id: str
    domain: str
    service: str
    billing_cycle_months: int
    amount_pkr: Decimal
    registered_on: date
    renews_on: date
    status: str
    contact_email: str
    flagged: bool = False

    def as_dict(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "customer_id": self.customer_id,
            "domain": self.domain,
            "service": self.service,
            "billing_cycle_months": str(self.billing_cycle_months),
            "amount_pkr": format_amount(self.amount_pkr),
            "registered_on": format_iso(self.registered_on),
            "renews_on": format_iso(self.renews_on),
            "status": self.status,
            "contact_email": self.contact_email,
        }

    @property
    def identity_key(self) -> tuple[str, str, str, str]:
        return (
            self.customer_id,
            self.domain,
            self.service.strip().lower(),
            format_iso(self.renews_on),
        )
