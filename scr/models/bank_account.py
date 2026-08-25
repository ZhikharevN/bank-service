import uuid
from decimal import Decimal

from scr.enums.account_status import AccountStatus
from scr.enums.currency import Currency
from scr.models.abstract_account import AbstractAccount


class BankAccount(AbstractAccount):
    type: str = "BankAccount"
    currency: Currency

    def __init__(
        self,
        first_name: str,
        last_name: str,
        currency: Currency,
        id: uuid.UUID | None = None,
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: Decimal = Decimal("0.00"),
    ) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.id = uuid.uuid4() if id is None else id
        self.status = status
        self.balance = balance
        self.currency = currency

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update({
            "type": self.type,
            "currency": self.currency.value,
        })
        return info

    def __str__(self) -> str:
        return (f"Type: {self.type}, name: {self.first_name}, last name: {self.last_name}, "
                f"status: {self.status}, balance: {self.balance}, currency: {self.currency}")
