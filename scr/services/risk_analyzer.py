from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from scr.audit.audit_logger import audit_logger
from scr.enums.risk_level import RiskLevel
from scr.enums.transaction_type import TransactionType
from scr.exceptions.invalid_operation_error import InvalidOperationError
from scr.exceptions.night_operations_error import NightOperationsError
from scr.models.abstract_account import AbstractAccount
from scr.models.client import Client
from scr.models.transaction import Transaction


@dataclass
class RiskAnalyzer:
    NIGHT_START = time(0, 0)
    NIGHT_END = time(5, 0)
    LARGE_AMOUNT = Decimal("100000")
    HIGH_BALANCE = Decimal("10000")
    FREQUENT_WINDOW = timedelta(minutes=10)
    FREQUENT_LIMIT = 5
    _known_destinations: set[UUID] = field(default_factory=set)
    _recent_ops: dict[UUID, list[datetime]] = field(default_factory=dict)

    def review(self, tx: Transaction) -> None:
        self._assert_operating_hours()
        client, account = self._client_and_account(tx)
        reasons = self._reasons(tx, account)
        tx.risk_level = self._level(reasons)
        if not reasons:
            return
        reason = "; ".join(reasons)
        tx.suspicious_actions = reasons
        audit_logger.warn(
            f"suspicious {tx.type.value} account={account.id} amount={tx.amount} "
            f"risk={tx.risk_level.value} reason={reason}"
        )
        if tx.risk_level == RiskLevel.HIGH:
            raise InvalidOperationError("high risk operation blocked")

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
        if self._is_frequent(account.id):
            reasons.append("frequent operations")
        return reasons

    def _is_frequent(self, account_id: UUID) -> bool:
        now = datetime.now()
        cutoff = now - self.FREQUENT_WINDOW
        stamps = [stamp for stamp in self._recent_ops.get(account_id, []) if stamp >= cutoff]
        stamps.append(now)
        self._recent_ops[account_id] = stamps
        return len(stamps) >= self.FREQUENT_LIMIT

    @staticmethod
    def _level(reasons: list[str]) -> RiskLevel:
        if len(reasons) >= 2:
            return RiskLevel.HIGH
        if reasons:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _client_and_account(tx: Transaction) -> tuple[Client, AbstractAccount]:
        if tx.type == TransactionType.DEPOSIT:
            if tx.receiver_account is None:
                raise InvalidOperationError("receiver_account is required")
            return tx.receiver, tx.receiver_account
        if tx.sender_account is None:
            raise InvalidOperationError("sender_account is required")
        return tx.sender, tx.sender_account
