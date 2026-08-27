from dataclasses import dataclass, field

from scr.enums.account_status import AccountStatus
from scr.enums.account_type import AccountType
from scr.enums.currency import Currency
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

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update({
            "currency": self.currency.value,
        })
        return info

    def __str__(self) -> str:
        return f"Type: {self.type}, status: {self.status}, balance: {self.balance}, currency: {self.currency}"
