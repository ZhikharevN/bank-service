from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from scr.enums.currency import Currency
from scr.enums.transaction_status import TransactionStatus
from scr.enums.transaction_type import TransactionType
from scr.exceptions.transaction_not_queue_error import TransactionNotInQueueError
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


def _tx(make_client, make_account, *, tx_type=TransactionType.DEPOSIT, amount=Decimal("30.00"), **overrides):
    account = make_account(BankAccount)
    client = make_client(accounts=[account])
    params = {
        "type": tx_type,
        "sender": client,
        "receiver": client,
        "amount": amount,
        "currency": Currency.RUB,
        "commission": Decimal("0"),
        "priority": 0,
        "receiver_account": account if tx_type == TransactionType.DEPOSIT else None,
        "sender_account": account if tx_type != TransactionType.DEPOSIT else None,
    }
    params.update(overrides)
    return Transaction(**params), client, account


def test_queue_add_and_pop_returns_highest_priority(make_client, make_account) -> None:
    queue = TransactionQueue()
    low, _, _ = _tx(make_client, make_account, amount=Decimal("1.00"))
    high, _, _ = _tx(make_client, make_account, amount=Decimal("2.00"))
    queue.add(low, priority=5)
    queue.add(high, priority=1)
    assert queue.pop() is high
    assert queue.pop() is low


def test_queue_cancel_skips_transaction_on_pop(make_client, make_account) -> None:
    queue = TransactionQueue()
    first, _, _ = _tx(make_client, make_account)
    second, _, _ = _tx(make_client, make_account)
    queue.add(first, priority=1)
    queue.add(second, priority=2)
    queue.cancel(first)
    assert first.status == TransactionStatus.CANCELED
    assert queue.pop() is second
    assert queue.pop() is None


def test_cancel_unknown_transaction_raises(make_client, make_account) -> None:
    tx, _, _ = _tx(make_client, make_account)
    with pytest.raises(TransactionNotInQueueError):
        TransactionQueue().cancel(tx)


def test_processor_deposit_completes(make_client, make_account) -> None:
    queue = TransactionQueue()
    tx, _, account = _tx(make_client, make_account, amount=Decimal("30.00"))
    queue.add(tx, 0)
    TransactionProcessor(queue).process_next()
    assert tx.status == TransactionStatus.COMPLETED
    assert tx.commission == Decimal("0.00")
    assert account.balance == Decimal("130.00")


def test_processor_withdraw_takes_commission(make_client, make_account) -> None:
    queue = TransactionQueue()
    tx, _, account = _tx(
        make_client,
        make_account,
        tx_type=TransactionType.WITHDRAW,
        amount=Decimal("30.00"),
    )
    queue.add(tx, 0)
    TransactionProcessor(queue).process_next()
    assert tx.commission == Decimal("0.30")
    assert account.balance == Decimal("69.70")


def test_processor_converts_currency(make_client, make_account) -> None:
    queue = TransactionQueue()
    account = make_account(BankAccount, currency=Currency.RUB)
    client = make_client(accounts=[account])
    tx = Transaction(
        type=TransactionType.DEPOSIT,
        sender=client,
        receiver=client,
        amount=Decimal("2.00"),
        currency=Currency.USD,
        commission=Decimal("0"),
        priority=0,
        receiver_account=account,
    )
    queue.add(tx, 0)
    TransactionProcessor(queue, rates={(Currency.USD, Currency.RUB): Decimal("90")}).process_next()
    assert account.balance == Decimal("280.00")


def test_processor_rejects_insufficient_funds(make_client, make_account) -> None:
    queue = TransactionQueue()
    tx, _, account = _tx(
        make_client,
        make_account,
        tx_type=TransactionType.WITHDRAW,
        amount=Decimal("100.00"),
    )
    queue.add(tx, 0)
    TransactionProcessor(queue).process_next()
    assert tx.status == TransactionStatus.REJECTED
    assert len(tx.errors) == 1
    assert account.balance == Decimal("100.00")

