from decimal import Decimal

import pytest

from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.models.premium_account import PremiumAccount


def test_get_account_info_includes_premium_fields(make_account) -> None:
    info = make_account(PremiumAccount, overdraft_limit = Decimal("99.00") ).get_account_info()
    assert info["overdraft_limit"] == Decimal("99.00")
    assert info["commission"] == Decimal("10.00")

def test_withdraw_respects_overdraft_limit(make_account) -> None:
    account = make_account(PremiumAccount, overdraft_limit=Decimal("100.00"))
    with pytest.raises(InsufficientFundsError, match="Operation impossible: insufficient funds"):
        account.withdraw(Decimal("201.00"))
    assert account.balance == Decimal("100.00")

def test_withdraw_balance_can_be_negative(make_account) -> None:
    account = make_account(PremiumAccount, overdraft_limit=Decimal("100.00"))
    account.withdraw(Decimal("190.00"))
    assert account.balance == Decimal("-100.00")
