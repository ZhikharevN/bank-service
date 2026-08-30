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
            "currency": Currency.RUB,
            "status": status,
        }
        params.update(overrides)
        initial_balance = params.pop("balance", None)
        requested_status = params["status"]
        reopen = (
            isinstance(requested_status, AccountStatus)
            and requested_status != AccountStatus.ACTIVE
        )
        if reopen:
            params["status"] = AccountStatus.ACTIVE
        account = cls(**params)
        if initial_balance is not None:
            account._balance = initial_balance
        else:
            account.deposit(Decimal("100.00"))
        if reopen:
            account.status = requested_status
        return account

    return _make
