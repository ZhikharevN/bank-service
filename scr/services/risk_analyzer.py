from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from scr.audit.audit_logger import audit_logger
from scr.enums.transaction_type import TransactionType
from scr.exceptions.invalid_operation_error import InvalidOperationError
from scr.exceptions.night_operations_error import NightOperationsError
from scr.models.abstract_account import AbstractAccount
from scr.models.client import Client
from scr.models.suspicious_action import SuspiciousAction
from scr.models.transaction import Transaction


@dataclass
class RiskAnalyzer:
    NIGHT_START = time(0, 0)
    NIGHT_END = time(5, 0)
    LARGE_AMOUNT = Decimal("100000")
    HIGH_BALANCE = Decimal("10000")
    _known_destinations: set[UUID] = field(default_factory=set)

    def review(self, tx: Transaction) -> None:
        self._assert_operating_hours()
        client, account = self._client_and_account(tx)
        reasons = self._reasons(tx, account)
        if not reasons:
            return
        reason = "; ".join(reasons)
        tx.suspicious_actions = reasons
        audit_logger.warn(
            f"suspicious {tx.type.value} account={account.id} amount={tx.amount} reason={reason}"
        )

    def remember(self, tx: Transaction) -> None:
        if tx.type == TransactionType.TRANSFER and tx.receiver_account is not None:
            self._known_destinations.add(tx.receiver_account.id)

    def _assert_operating_hours(self) -> None:
        current = datetime.now().time()
        if self.NIGHT_START <= current < self.NIGHT_END:
            raise NightOperationsError(str(self.NIGHT_START), str(self.NIGHT_END))

    def _reasons(self, tx: Transaction, account: AbstractAccount) -> list[str]:
        reasons = []
        if tx.amount >= self.LARGE_AMOUNT:
            reasons.append("large amount")
        if account.balance > self.HIGH_BALANCE and tx.amount > account.balance / 2:
            reasons.append("more than half of balance")
        if (
            tx.type == TransactionType.TRANSFER
            and tx.receiver_account is not None
            and tx.receiver_account.id not in self._known_destinations
        ):
            reasons.append("transfer to new account")
        return reasons

    @staticmethod
    def _client_and_account(tx: Transaction) -> tuple[Client, AbstractAccount]:
        if tx.type == TransactionType.DEPOSIT:
            if tx.receiver_account is None:
                raise InvalidOperationError("receiver_account is required")
            return tx.receiver, tx.receiver_account
        if tx.sender_account is None:
            raise InvalidOperationError("sender_account is required")
        return tx.sender, tx.sender_account
