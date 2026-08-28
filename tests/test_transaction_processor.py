from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from scr.enums.currency import Currency
from scr.enums.transaction_status import TransactionStatus
from scr.enums.transaction_type import TransactionType
from scr.models.bank_account import BankAccount
from scr.models.transaction import Transaction
from scr.services.transaction_processor import TransactionProcessor
from scr.services.transaction_queue import TransactionQueue

DAYTIME = datetime(2026, 1, 15, 12, 0)


@pytest.fixture(autouse=True)
def daytime():
    with (
        patch("scr.services.risk_analyzer.datetime") as risk_dt,
        patch("scr.services.transaction_processor.datetime") as proc_dt,
    ):
        risk_dt.now.return_value = DAYTIME
        proc_dt.now.return_value = DAYTIME
        yield


def test_processor_completes_ten_different_transactions(make_client, make_account) -> None:
    queue = TransactionQueue()
    transactions = [
        _deposit(make_client, make_account, Decimal("10.00"), priority=9),
        _withdraw(make_client, make_account, Decimal("15.00"), priority=8),
        _transfer(make_client, make_account, Decimal("20.00"), priority=7),
        _deposit(make_client, make_account, Decimal("1.25"), priority=6),
        _withdraw(make_client, make_account, Decimal("40.50"), priority=5),
        _transfer(make_client, make_account, Decimal("5.00"), priority=4),
        _deposit(make_client, make_account, Decimal("80.00"), priority=3),
        _withdraw(make_client, make_account, Decimal("7.10"), priority=2),
        _transfer(make_client, make_account, Decimal("33.33"), priority=1),
        _deposit(make_client, make_account, Decimal("100.00"), priority=0),
    ]
    for tx in transactions:
        queue.add(tx, tx.priority)

    processor = TransactionProcessor(queue)
    for _ in transactions:
        processor.process_next()

    assert all(tx.status == TransactionStatus.COMPLETED for tx in transactions)
    assert all(tx.errors == [] for tx in transactions)
    assert queue.pop() is None


def _deposit(make_client, make_account, amount: Decimal, *, priority: int = 0) -> Transaction:
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    return Transaction(
        type=TransactionType.DEPOSIT,
        sender=client,
        receiver=client,
        amount=amount,
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=priority,
        receiver_account=account,
    )


def _withdraw(make_client, make_account, amount: Decimal, *, priority: int = 0) -> Transaction:
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    return Transaction(
        type=TransactionType.WITHDRAW,
        sender=client,
        receiver=client,
        amount=amount,
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=priority,
        sender_account=account,
    )


def _transfer(make_client, make_account, amount: Decimal, *, priority: int = 0) -> Transaction:
    source = make_account(BankAccount)
    target = make_account(BankAccount, balance=Decimal("20.00"))
    sender = make_client(accounts=[source])
    receiver = make_client(
        accounts=[target],
        email="receiver@test.com",
        account_number="ACC-RECV",
    )
    return Transaction(
        type=TransactionType.TRANSFER,
        sender=sender,
        receiver=receiver,
        amount=amount,
        currency=Currency.RUB,
        commission=Decimal("0"),
        priority=priority,
        sender_account=source,
        receiver_account=target,
    )
