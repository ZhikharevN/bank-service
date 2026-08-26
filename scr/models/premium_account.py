from dataclasses import dataclass, field
from decimal import Decimal

from scr.enums.account_type import AccountType
from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.models.bank_account import BankAccount


@dataclass
class PremiumAccount(BankAccount):
    overdraft_limit: Decimal = Decimal("0.00")
    commission: Decimal = Decimal("10.00")
    type: AccountType = field(default=AccountType.PREMIUM_ACCOUNT, init=False)

    def withdraw(self, amount):
        self._validate_status()
        new_balance = self.balance - amount - self.commission
        if new_balance < -self.overdraft_limit:
            raise InsufficientFundsError()
        self.balance = new_balance

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update({
            "overdraft_limit": self.overdraft_limit,
            "commission": self.commission,
        })
        return info

    def __str__(self) -> str:
        return (f"Type: {self.type}, name: {self.first_name}, last name: {self.last_name},"
                f"status: {self.status}, balance: {self.balance}, currency: {self.currency}, "
                f"overdraft_limit: {self.overdraft_limit}, commission: {self.commission}")
