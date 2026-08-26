from decimal import Decimal

import pytest

from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.models.savings_account import SavingsAccount


def test_apply_monthly_interest_increases_balance(make_account) -> None:
    account = make_account(SavingsAccount)
    account.apply_monthly_interest()
    assert account.balance == Decimal("101.00")


def test_withdraw_respects_min_balance(make_account) -> None:
    account = make_account(SavingsAccount, min_balance=Decimal("50.00"))
    with pytest.raises(InsufficientFundsError, match="Operation impossible: insufficient funds"):
        account.withdraw(Decimal("51.00"))
    assert account.balance == Decimal("100.00")


def test_get_account_info_includes_savings_fields(make_account) -> None:
    info = make_account(SavingsAccount).get_account_info()
    assert info["min_balance"] == Decimal("0.00")
    assert info["monthly_interest"] == Decimal("0.01")
