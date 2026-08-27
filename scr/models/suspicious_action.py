from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class SuspiciousAction:
    at: datetime
    operation: str
    amount: Decimal
    reason: str
