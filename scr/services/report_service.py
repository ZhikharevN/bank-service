from dataclasses import dataclass
from decimal import Decimal

from scr.audit.audit_report_service import AuditReportService
from scr.models.bank import Bank
from scr.models.client import Client
from scr.models.transaction import Transaction


@dataclass
class ReportService:

    @staticmethod
    def top_n_clients(bank: Bank, n: int) -> list[Client]:
        return sorted(
            bank.clients,
            key=lambda client: client.get_sum_balance(),
            reverse=True,
        )[:n]

    @staticmethod
    def sum_balance(bank: Bank) -> Decimal:
        return sum(
            (client.get_sum_balance() for client in bank.clients),
            start=Decimal(0)
        )

    @staticmethod
    def transactions_statistic(bank: Bank) -> dict[str, list[Transaction]]:
        return AuditReportService.group(bank, lambda tx: [tx.type.value])





