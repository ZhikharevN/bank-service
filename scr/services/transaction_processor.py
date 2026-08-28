from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from scr.audit.audit_logger import audit_logger
from scr.enums.client_status import ClientStatus
from scr.enums.currency import Currency
from scr.enums.transaction_status import TransactionStatus
from scr.enums.transaction_type import TransactionType
from scr.exceptions.account_closed_error import AccountClosedError
from scr.exceptions.account_frozen_error import AccountFrozenError
from scr.exceptions.client_blocked_error import ClientBlockedError
from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.exceptions.invalid_operation_error import InvalidOperationError
from scr.exceptions.night_operations_error import NightOperationsError
from scr.models.abstract_account import AbstractAccount
from scr.models.client import Client
from scr.models.transaction import Transaction
from scr.models.transaction_error import TransactionError
from scr.services.risk_analyzer import RiskAnalyzer
from scr.services.transaction_queue import TransactionQueue


@dataclass
class TransactionProcessor:
    queue: TransactionQueue
    rates: dict[tuple[Currency, Currency], Decimal] = field(default_factory=dict)
    risk_analyzer: RiskAnalyzer = field(default_factory=RiskAnalyzer)
    max_attempts: int = 3

    _FATAL = (
        InsufficientFundsError,
        AccountFrozenError,
        AccountClosedError,
        InvalidOperationError,
        ClientBlockedError,
    )
    _RETRYABLE = (NightOperationsError,)
    _COMMISSION_RATE = {
        TransactionType.DEPOSIT: Decimal("0"),
        TransactionType.WITHDRAW: Decimal("0.01"),
        TransactionType.TRANSFER: Decimal("0.01"),
    }

    def process_next(self) -> None:
        tx = self.queue.pop()
        if tx is None:
            return
        self._execute(tx)

    def _execute(self, tx: Transaction) -> Transaction:
        for attempt in range(1, self.max_attempts + 1):
            try:
                self._apply(tx)
                tx.status = TransactionStatus.COMPLETED
                self.risk_analyzer.remember(tx)
                audit_logger.info(
                    f"{tx.type.value} completed id={tx.id} amount={tx.amount} "
                    f"commission={tx.commission} {tx.currency.value}"
                )
                return tx
            except self._FATAL as error:
                self._record_error(tx, attempt, error)
                tx.status = TransactionStatus.REJECTED
                audit_logger.error(
                    f"{tx.type.value} rejected id={tx.id} amount={tx.amount} error={error}"
                )
                return tx
            except self._RETRYABLE as error:
                self._record_error(tx, attempt, error)
                audit_logger.warn(
                    f"{tx.type.value} retry id={tx.id} attempt={attempt} error={error}"
                )
        tx.status = TransactionStatus.REJECTED
        audit_logger.error(
            f"{tx.type.value} rejected id={tx.id} after {self.max_attempts} attempts"
        )
        return tx

    def _apply(self, tx: Transaction) -> None:
        client, account = self._client_and_account(tx)
        if client.status == ClientStatus.BLOCKED:
            raise ClientBlockedError()
        self.risk_analyzer.review(tx)
        tx.commission = (tx.amount * self._COMMISSION_RATE[tx.type]).quantize(Decimal("0.01"))
        match tx.type:
            case TransactionType.DEPOSIT:
                tx.receiver.history.add(tx)
                account.deposit(self._to_account(tx.amount, tx.currency, account))
            case TransactionType.WITHDRAW:
                tx.sender.history.add(tx)
                debit = tx.amount + tx.commission
                account.withdraw(self._to_account(debit, tx.currency, account))
            case TransactionType.TRANSFER:
                tx.receiver.history.add(tx)
                tx.sender.history.add(tx)
                target = self._require(tx.receiver_account, "receiver_account")
                account.withdraw(self._to_account(tx.amount + tx.commission, tx.currency, account))
                target.deposit(self._to_account(tx.amount, tx.currency, target))

    def _client_and_account(self, tx: Transaction) -> tuple[Client, AbstractAccount]:
        match tx.type:
            case TransactionType.DEPOSIT:
                return tx.receiver, self._require(tx.receiver_account, "receiver_account")
            case TransactionType.WITHDRAW | TransactionType.TRANSFER:
                return tx.sender, self._require(tx.sender_account, "sender_account")
            case _:
                raise InvalidOperationError()

    def _to_account(self, amount: Decimal, from_currency: Currency, account: AbstractAccount) -> Decimal:
        to_currency = getattr(account, "currency", None)
        if to_currency is None:
            raise InvalidOperationError("account has no currency")
        if from_currency == to_currency:
            return amount
        rate = self.rates.get((from_currency, to_currency))
        if rate is None:
            raise InvalidOperationError(f"no FX rate for {from_currency.value}->{to_currency.value}")
        return (amount * rate).quantize(Decimal("0.01"))

    @staticmethod
    def _require(account: AbstractAccount | None, name: str) -> AbstractAccount:
        if account is None:
            raise InvalidOperationError(f"{name} is required")
        return account

    @staticmethod
    def _record_error(tx: Transaction, attempt: int, error: Exception) -> None:
        tx.errors.append(
            TransactionError(at=datetime.now(), attempt=attempt, message=str(error))
        )
