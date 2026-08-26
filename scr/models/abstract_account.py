import uuid
from abc import ABC
from dataclasses import field, dataclass
from decimal import Decimal

from scr.enums.account_status import AccountStatus
from scr.enums.account_type import AccountType
from scr.exceptions.account_closed_error import AccountClosedError
from scr.exceptions.account_frozen_error import AccountFrozenError
from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.exceptions.invalid_operation_error import InvalidOperationError


@dataclass
class AbstractAccount(ABC):
    first_name: str
    last_name: str
    type: AccountType
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: AccountStatus = AccountStatus.ACTIVE
    balance: Decimal = field(default=Decimal('0.00'), repr=False)

    def deposit(self, amount):
        self._validate_status()
        if amount < 0:
            raise InvalidOperationError()
        self.balance += amount

    def withdraw(self, amount):
        self._validate_status()
        new_balance = self.balance - amount
        if new_balance < 0:
            raise InsufficientFundsError()
        self.balance = new_balance

    def get_account_info(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "balance": self.balance,
        }

    def _validate_status(self):
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError()
        elif self.status == AccountStatus.FROZEN:
            raise AccountFrozenError()
