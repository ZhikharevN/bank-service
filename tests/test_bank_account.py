from decimal import Decimal

import pytest

from scr.enums.account_status import AccountStatus
from scr.models.bank_account import BankAccount


def test_deposit_and_withdraw_update_balance(make_account) -> None:
    account = make_account(BankAccount, status=AccountStatus.ACTIVE)
    account.deposit(Decimal("50.00"))
    assert account.balance == Decimal("150.00")

    account.withdraw(Decimal("30.00"))
    assert account.balance == Decimal("120.00")


def test_get_account_info_includes_currency(make_account) -> None:
    info = make_account(BankAccount).get_account_info()
    assert info["currency"] == "RUB"
    assert info["balance"] == Decimal("100.00")


def test_post_init_rejects_invalid_currency(make_account) -> None:
    with pytest.raises(TypeError, match="currency"):
        make_account(BankAccount, currency="RUB")


def test_post_init_rejects_invalid_status(make_account) -> None:
    with pytest.raises(TypeError, match="status"):
        make_account(BankAccount, status="ACTIVE")
