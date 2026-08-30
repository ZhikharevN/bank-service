import uuid
from abc import ABC, abstractmethod
from dataclasses import field, dataclass
from decimal import Decimal
from itertools import count

from scr.enums.account_status import AccountStatus
from scr.enums.account_type import AccountType
from scr.exceptions.account_closed_error import AccountClosedError
from scr.exceptions.account_frozen_error import AccountFrozenError

_numbers = count(1)

def _account_number() -> str:
    return f"{next(_numbers):012d}"

@dataclass
class AbstractAccount(ABC):
    type: AccountType
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    number: str = field(default_factory=_account_number)
    status: AccountStatus = AccountStatus.ACTIVE
    _balance: Decimal = field(default=Decimal('0.00'), init=False, repr=False)

    @abstractmethod
    def deposit(self, amount: Decimal):
        ...

    @abstractmethod
    def withdraw(self, amount: Decimal):
        ...

    @abstractmethod
    def get_account_info(self) -> dict:
        ...

    @property
    def balance(self) -> Decimal:
        return self._balance

    def _validate_status(self):
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError()
        elif self.status == AccountStatus.FROZEN:
            raise AccountFrozenError()
