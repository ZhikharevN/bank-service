from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from scr.enums.currency import Currency
from scr.enums.risk_level import RiskLevel
from scr.enums.transaction_type import TransactionType
from scr.exceptions.invalid_operation_error import InvalidOperationError
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
    target = make_account(BankAccount)
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


def _withdraw(make_client, make_account, amount, *, balance: Decimal | None = None) -> Transaction:
    account = make_account(BankAccount)
    if balance is not None:
        account._balance = balance
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
    assert second.risk_level == RiskLevel.LOW


def test_ordinary_operation_is_low_risk(make_client, make_account, frozen_now) -> None:
    tx = _withdraw(make_client, make_account, Decimal("10.00"))
    RiskAnalyzer().review(tx)
    assert tx.suspicious_actions == []
    assert tx.risk_level == RiskLevel.LOW


def test_single_flag_is_medium_risk(make_client, make_account, frozen_now) -> None:
    tx = _withdraw(
        make_client,
        make_account,
        Decimal("100000.00"),
        balance=Decimal("200000.00"),
    )
    RiskAnalyzer().review(tx)
    assert tx.suspicious_actions == ["large amount"]
    assert tx.risk_level == RiskLevel.MEDIUM


def test_frequent_operations_are_flagged(make_client, make_account, frozen_now) -> None:
    analyzer = RiskAnalyzer()
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    txs = []
    for _ in range(RiskAnalyzer.FREQUENT_LIMIT):
        tx = Transaction(
            type=TransactionType.WITHDRAW,
            sender=client,
            receiver=client,
            amount=Decimal("1.00"),
            currency=Currency.RUB,
            commission=Decimal("0"),
            priority=0,
            sender_account=account,
        )
        analyzer.review(tx)
        txs.append(tx)

    assert "frequent operations" not in txs[0].suspicious_actions
    assert txs[-1].suspicious_actions == ["frequent operations"]
    assert txs[-1].risk_level == RiskLevel.MEDIUM


def test_several_flags_are_high_risk(make_client, make_account, frozen_now) -> None:
    analyzer = RiskAnalyzer()
    account = make_account(BankAccount)
    account._balance = Decimal("200000.00")
    client = make_client(accounts=[account])
    for _ in range(RiskAnalyzer.FREQUENT_LIMIT - 1):
        warmup = Transaction(
            type=TransactionType.WITHDRAW,
            sender=client,
            receiver=client,
            amount=Decimal("1.00"),
            currency=Currency.RUB,
            commission=Decimal("0"),
            priority=0,
            sender_account=account,
        )
        analyzer.review(warmup)

    tx = Transaction(
        type=TransactionType.WITHDRAW,
        sender=client,
        receiver=client,
        amount=Decimal("100000.00"),
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=0,
        sender_account=account,
    )
    with pytest.raises(InvalidOperationError, match="high risk"):
        analyzer.review(tx)
    assert "large amount" in tx.suspicious_actions
    assert "frequent operations" in tx.suspicious_actions
    assert tx.risk_level == RiskLevel.HIGH
