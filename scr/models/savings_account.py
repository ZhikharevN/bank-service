from dataclasses import dataclass, field
from decimal import Decimal

from scr.enums.account_type import AccountType
from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.models.bank_account import BankAccount


@dataclass
class SavingsAccount(BankAccount):
    min_balance: Decimal = field(default=Decimal('0.00'))
    monthly_interest: Decimal = Decimal('0.01')
    type: AccountType = field(default=AccountType.SAVINGS_ACCOUNT, init=False)

    def apply_monthly_interest(self) -> None:
        self.balance += self.balance * self.monthly_interest

    def withdraw(self, amount):
        self._validate_status()
        new_balance = self.balance - amount
        if new_balance < self.min_balance:
            raise InsufficientFundsError()
        self.balance = new_balance

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update({
            "min_balance": self.min_balance,
            "monthly_interest": self.monthly_interest,
        })
        return info

    def __str__(self) -> str:
        return (f"Type: {self.type}, status: {self.status}, balance: {self.balance}, currency: {self.currency}, "
                f"min_balance: {self.min_balance}, monthly_interest: {self.monthly_interest}")
