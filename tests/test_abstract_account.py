from decimal import Decimal

import pytest

from scr.enums.account_status import AccountStatus
from scr.exceptions.account_closed_error import AccountClosedError
from scr.exceptions.account_frozen_error import AccountFrozenError
from tests.data.account import ACCOUNT_TYPES


@pytest.mark.parametrize("account_cls", ACCOUNT_TYPES)
@pytest.mark.parametrize("operation,amount", [
    ("deposit", Decimal("50.00")),
    ("withdraw", Decimal("10.00")),
])
def test_operations_on_frozen_account_are_rejected(
        make_account,
        account_cls,
        operation,
        amount
) -> None:
    account = make_account(account_cls, status=AccountStatus.FROZEN)
    original_balance = account.balance

    with pytest.raises(AccountFrozenError, match="account frozen"):
        getattr(account, operation)(amount)

    assert account.balance == original_balance


@pytest.mark.parametrize("account_cls", ACCOUNT_TYPES)
@pytest.mark.parametrize("operation,amount", [
    ("deposit", Decimal("50.00")),
    ("withdraw", Decimal("10.00")),
])
def test_operations_on_closed_account_are_rejected(
        make_account,
        account_cls,
        operation,
        amount,
) -> None:
    account = make_account(account_cls, status=AccountStatus.CLOSED)
    original_balance = account.balance
    with pytest.raises(AccountClosedError, match="account closed"):
        getattr(account, operation)(amount)
    assert account.balance == original_balance
