import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from scr.enums.currency import Currency
from scr.enums.transaction_status import TransactionStatus
from scr.enums.transaction_type import TransactionType
from scr.models.abstract_account import AbstractAccount
from scr.models.client import Client
from scr.models.suspicious_action import SuspiciousAction
from scr.models.transaction_error import TransactionError


@dataclass
class Transaction:
    type: TransactionType
    sender: Client
    receiver: Client
    amount: Decimal
    currency: Currency
    commission: Decimal
    priority: int
    sender_account: AbstractAccount | None = None
    receiver_account: AbstractAccount | None = None
    suspicious_actions: list[str] = field(default_factory=list)
    status: TransactionStatus = field(default=TransactionStatus.CREATED, init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    errors: list[TransactionError] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.id)
