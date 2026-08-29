from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from uuid import UUID

from scr.models.bank import Bank
from scr.models.transaction import Transaction


@dataclass
class AuditReportService:

    @staticmethod
    def error_stats(bank: Bank) -> dict[str, list[Transaction]]:
        return AuditReportService.group(bank, lambda tx: [error.message for error in tx.errors])

    @staticmethod
    def suspicious_by_reason(bank: Bank) -> dict[str, list[Transaction]]:
        return AuditReportService.group(bank, lambda tx: tx.suspicious_actions)

    @staticmethod
    def _unique_transactions(bank: Bank) -> list[Transaction]:
        seen: dict[UUID, Transaction] = {}
        for client in bank.clients:
            for tx in client.history:
                seen[tx.id] = tx
        return list(seen.values())

    @staticmethod
    def group(
        bank: Bank,
        keys_of: Callable[[Transaction], Iterable[str]],
    ) -> dict[str, list[Transaction]]:
        grouped: dict[str, list[Transaction]] = defaultdict(list)
        for tx in AuditReportService._unique_transactions(bank):
            for key in keys_of(tx):
                grouped[key].append(tx)
        return dict(grouped)
