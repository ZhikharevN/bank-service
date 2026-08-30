from dataclasses import dataclass, field

from scr.enums.account_status import AccountStatus
from scr.enums.account_type import AccountType
from scr.enums.currency import Currency
from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.exceptions.invalid_operation_error import InvalidOperationError
from scr.models.abstract_account import AbstractAccount


@dataclass(kw_only=True)
class BankAccount(AbstractAccount):
    currency: Currency
    type: AccountType = field(default=AccountType.BANK_ACCOUNT, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be type Currency")

        if not isinstance(self.status, AccountStatus):
            raise TypeError("status must be type AccountStatus")

    def deposit(self, amount):
        self._validate_status()
        if amount < 0:
            raise InvalidOperationError()
        self._balance += amount

    def withdraw(self, amount):
        self._validate_status()
        if amount < 0:
            raise InvalidOperationError()
        new_balance = self.balance - amount
        if new_balance < 0:
            raise InsufficientFundsError()
        self._balance = new_balance

    def get_account_info(self) -> dict:
         return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "balance": self.balance,
            "currency": self.currency.value,
            "number": self.number,
        }

    def __str__(self) -> str:
        return (f"Type: {self.type}, status: {self.status}, balance: {self.balance}, currency: {self.currency}"
                f"number: {self.number[-4:]}")
