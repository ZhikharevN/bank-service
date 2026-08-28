from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from scr.enums.currency import Currency
from scr.enums.transaction_type import TransactionType
from scr.exceptions.night_operations_error import NightOperationsError
from scr.models.bank_account import BankAccount
from scr.models.transaction import Transaction
from scr.services.risk_analyzer import RiskAnalyzer

DAYTIME = datetime(2026, 1, 15, 12, 0)
NIGHT = datetime(2026, 1, 15, 3, 0)


@pytest.fixture
def frozen_now():
    with patch("scr.services.risk_analyzer.datetime") as mock_datetime:
        mock_datetime.now.return_value = DAYTIME
        yield mock_datetime.now


def _transfer(make_client, make_account, amount=Decimal("40.00")) -> Transaction:
    source = make_account(BankAccount)
    target = make_account(BankAccount, balance=Decimal("0.00"))
    sender = make_client(accounts=[source])
    receiver = make_client(
        accounts=[target],
        email="recv@test.com",
        account_number="ACC-RECV",
    )
    return Transaction(
        type=TransactionType.TRANSFER,
        sender=sender,
        receiver=receiver,
        amount=amount,
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=0,
        sender_account=source,
        receiver_account=target,
    )


def _withdraw(make_client, make_account, amount, *, balance=Decimal("100.00")) -> Transaction:
    account = make_account(BankAccount, balance=balance)
    client = make_client(accounts=[account])
    return Transaction(
        type=TransactionType.WITHDRAW,
        sender=client,
        receiver=client,
        amount=amount,
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=0,
        sender_account=account,
    )


def test_night_operations_are_rejected(make_client, make_account, frozen_now) -> None:
    frozen_now.return_value = NIGHT
    tx = _withdraw(make_client, make_account, Decimal("10.00"))
    with pytest.raises(NightOperationsError, match="00:00"):
        RiskAnalyzer().review(tx)
    assert tx.suspicious_actions == []


def test_large_amount_is_flagged(make_client, make_account, frozen_now) -> None:
    tx = _withdraw(
        make_client,
        make_account,
        Decimal("100000.00"),
        balance=Decimal("200000.00"),
    )
    RiskAnalyzer().review(tx)
    assert tx.suspicious_actions == ["large amount"]


def test_transfer_to_new_account_is_flagged_only_once(make_client, make_account, frozen_now) -> None:
    first = _transfer(make_client, make_account)
    analyzer = RiskAnalyzer()
    analyzer.review(first)
    assert "transfer to new account" in first.suspicious_actions

    analyzer.remember(first)
    second = Transaction(
        type=TransactionType.TRANSFER,
        sender=first.sender,
        receiver=first.receiver,
        amount=Decimal("10.00"),
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=0,
        sender_account=first.sender_account,
        receiver_account=first.receiver_account,
    )
    analyzer.review(second)
    assert second.suspicious_actions == []
