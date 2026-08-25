from decimal import Decimal

import pytest

from scr.exceptions.account_frozen_error import AccountFrozenError
from scr.models.bank_account import BankAccount


def test_deposit_and_withdraw_update_balance(active_account: BankAccount) -> None:
    active_account.deposit(Decimal("50.00"))
    assert active_account.balance == Decimal("150.00")

    active_account.withdraw(Decimal("30.00"))
    assert active_account.balance == Decimal("120.00")


@pytest.mark.parametrize("operation,amount", [
    ("deposit", Decimal("50.00")),
    ("withdraw", Decimal("10.00")),
])
def test_operations_on_frozen_account_are_rejected(
    frozen_account: BankAccount,
    operation: str,
    amount: Decimal,
) -> None:
    original_balance = frozen_account.balance

    with pytest.raises(AccountFrozenError, match="account frozen"):
        getattr(frozen_account, operation)(amount)

    assert frozen_account.balance == original_balance
