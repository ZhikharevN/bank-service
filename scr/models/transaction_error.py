from dataclasses import dataclass
from datetime import datetime


@dataclass
class TransactionError:
    at: datetime
    attempt: int
    message: str
