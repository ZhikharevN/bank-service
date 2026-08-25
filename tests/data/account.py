from decimal import Decimal

import pytest

from scr.enums.account_status import AccountStatus
from scr.enums.currency import Currency
from scr.models.bank_account import BankAccount


@pytest.fixture
def active_account() -> BankAccount:
    return BankAccount(
        first_name="Ivan",
        last_name="Petrov",
        currency=Currency.RUB,
        balance=Decimal("100.00"),
    )


@pytest.fixture
def frozen_account() -> BankAccount:
    return BankAccount(
        first_name="Ivan",
        last_name="Petrov",
        currency=Currency.RUB,
        status=AccountStatus.FROZEN,
        balance=Decimal("100.00"),
    )
