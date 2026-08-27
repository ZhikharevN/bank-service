from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from scr.enums.account_status import AccountStatus
from scr.enums.client_status import ClientStatus
from scr.exceptions.client_blocked_error import ClientBlockedError
from scr.exceptions.night_operations_error import NightOperationsError
from scr.models.bank import Bank
from scr.models.bank_account import BankAccount

DAYTIME = datetime(2026, 1, 15, 12, 0)
NIGHT = datetime(2026, 1, 15, 3, 0)
NIGHT_START = datetime(2026, 1, 15, 0, 0)
JUST_BEFORE_OPENING = datetime(2026, 1, 15, 4, 59)
OPENING = datetime(2026, 1, 15, 5, 0)


@pytest.fixture
def frozen_now():
    with patch("scr.models.bank.datetime") as mock_datetime:
        mock_datetime.now.return_value = DAYTIME
        yield mock_datetime.now


def test_execute_withdraw_in_daytime_updates_balance(make_account, make_client, frozen_now) -> None:
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    Bank().execute_withdraw(client, account, Decimal("30.00"))
    assert account.balance == Decimal("70.00")


def test_execute_deposit_in_daytime_updates_balance(make_account, make_client, frozen_now) -> None:
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    Bank().execute_deposit(client, account, Decimal("30.00"))
    assert account.balance == Decimal("130.00")


@pytest.mark.parametrize("when", [NIGHT, NIGHT_START, JUST_BEFORE_OPENING])
def test_operations_at_night_are_rejected(make_account, make_client, frozen_now, when) -> None:
    frozen_now.return_value = when
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    with pytest.raises(NightOperationsError, match="00:00 to 05:00"):
        Bank().execute_withdraw(client, account, Decimal("30.00"))
    with pytest.raises(NightOperationsError, match="00:00 to 05:00"):
        Bank().execute_deposit(client, account, Decimal("30.00"))
    assert account.balance == Decimal("100.00")


def test_operations_are_allowed_from_opening_hour(make_account, make_client, frozen_now) -> None:
    frozen_now.return_value = OPENING
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    Bank().execute_withdraw(client, account, Decimal("10.00"))
    Bank().execute_deposit(client, account, Decimal("5.00"))
    assert account.balance == Decimal("95.00")


def test_large_withdraw_is_marked_suspicious(make_account, make_client, frozen_now) -> None:
    account = make_account(BankAccount, balance=Decimal("200000.00"))
    client = make_client(accounts=[account])
    Bank().execute_withdraw(client, account, Decimal("100000.00"))
    assert len(client.suspicious_actions) == 1
    action = client.suspicious_actions[0]
    assert action.operation == "withdraw"
    assert action.amount == Decimal("100000.00")
    assert action.at == DAYTIME
    assert "large amount" in action.reason
    assert account.balance == Decimal("100000.00")


def test_withdraw_of_more_than_half_large_balance_is_marked_suspicious(
        make_account, make_client, frozen_now
) -> None:
    account = make_account(BankAccount, balance=Decimal("20000.00"))
    client = make_client(accounts=[account])
    Bank().execute_withdraw(client, account, Decimal("12000.00"))
    assert len(client.suspicious_actions) == 1
    assert "more than half of balance" in client.suspicious_actions[0].reason
    assert account.balance == Decimal("8000.00")


def test_ordinary_withdraw_is_not_marked_suspicious(make_account, make_client, frozen_now) -> None:
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    Bank().execute_withdraw(client, account, Decimal("60.00"))
    assert client.suspicious_actions == []
    assert account.balance == Decimal("40.00")


def test_blocked_client_cannot_withdraw(make_account, make_client, frozen_now) -> None:
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    client.status = ClientStatus.BLOCKED
    with pytest.raises(ClientBlockedError):
        Bank().execute_withdraw(client, account, Decimal("10.00"))
    assert account.balance == Decimal("100.00")


def test_open_close_freeze_and_unfreeze_account(make_account) -> None:
    account = make_account(BankAccount, status=AccountStatus.CLOSED)
    Bank.open_account(account)
    assert account.status == AccountStatus.ACTIVE
    Bank.freeze_account(account)
    assert account.status == AccountStatus.FROZEN
    Bank.unfreeze_account(account)
    assert account.status == AccountStatus.ACTIVE
    Bank.close_account(account)
    assert account.status == AccountStatus.CLOSED


def test_authenticate_client_blocks_after_three_bad_passwords(make_client) -> None:
    client = make_client()
    Bank.authenticate_client(client, "secret")
    assert client.status == ClientStatus.ACTIVE
    assert client.bad_entries == 0

    Bank.authenticate_client(client, "wrong")
    Bank.authenticate_client(client, "wrong")
    assert client.status == ClientStatus.ACTIVE
    Bank.authenticate_client(client, "wrong")
    assert client.status == ClientStatus.BLOCKED

    with pytest.raises(ClientBlockedError):
        Bank.authenticate_client(client, "secret")


def test_search_accounts_and_total_balance(make_account, make_client) -> None:
    first = make_account(BankAccount, balance=Decimal("40.00"))
    second = make_account(BankAccount, balance=Decimal("60.00"))
    client = make_client(accounts=[first, second])
    bank = Bank()
    bank.add_client(client)
    assert bank.clients == [client]
    assert Bank.search_accounts(client) == [first, second]
    assert Bank.get_total_balance(client) == Decimal("100.00")
