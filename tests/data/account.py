from decimal import Decimal
from typing import Type

import pytest

from scr.enums.account_status import AccountStatus
from scr.enums.currency import Currency
from scr.models.abstract_account import AbstractAccount
from scr.models.bank_account import BankAccount
from scr.models.investment_account import InvestmentAccount
from scr.models.premium_account import PremiumAccount
from scr.models.savings_account import SavingsAccount

ACCOUNT_TYPES = (BankAccount, SavingsAccount, PremiumAccount, InvestmentAccount)


@pytest.fixture
def make_account():
    def _make(
            cls: Type[AbstractAccount] = BankAccount,
            *,
            status: AccountStatus = AccountStatus.ACTIVE,
            **overrides,
    ) -> AbstractAccount:
        params = {
            "first_name": "Ivan",
            "last_name": "Petrov",
            "currency": Currency.RUB,
            "balance": Decimal("100.00"),
            "status": status,
        }
        params.update(overrides)
        return cls(**params)

    return _make
