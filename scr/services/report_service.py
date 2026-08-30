from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from scr.audit.audit_report_service import AuditReportService
from scr.enums.transaction_status import TransactionStatus
from scr.enums.transaction_type import TransactionType
from scr.models.bank import Bank
from scr.models.client import Client
from scr.models.transaction import Transaction

_SCR_DIR = Path(__file__).resolve().parent.parent
CHARTS_DIR = _SCR_DIR.parent / "reports" / "charts"

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

    @staticmethod
    def pie_chart(names_to_quantities: dict[str, float]) -> None:
        labels = list(names_to_quantities.keys())
        sizes = list(names_to_quantities.values())

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels)
        ReportService._save_chart(fig, "pie_chart.png")

    @staticmethod
    def change_balance(
            txs: set[Transaction],
            start: Decimal = Decimal("0")
    ) -> None:
        ordered = sorted(txs, key=lambda tx: tx.timestamp)
        balance = start
        xs = [0]
        ys = [float(balance)]
        for i, tx in enumerate(ordered, start=1):
            if tx.status == TransactionStatus.COMPLETED:
                balance += ReportService._delta(tx)
            xs.append(i)
            ys.append(float(balance))
        fig, ax = plt.subplots()
        ax.plot(xs, ys, marker="o")
        ax.set(ylabel="balance", title="Balance over transactions")
        ax.grid()
        ReportService._save_chart(fig, "change_balance.png")

    @staticmethod
    def bar_chart(names_to_quantities: dict[str, Decimal]) -> None:
        names = names_to_quantities.keys()
        counts = names_to_quantities.values()
        cmap = plt.colormaps["tab20"]
        colors = [cmap(i / max(len(names) - 1, 1)) for i in range(len(names))]
        fig, ax = plt.subplots()
        bars = ax.bar(names, counts, color=colors)
        ax.legend(bars, names, title="Type")
        ReportService._save_chart(fig, "bar_chart.png")

    @staticmethod
    def _delta(tx: Transaction) -> Decimal:
        if tx.type == TransactionType.DEPOSIT:
            return tx.amount
        if tx.type == TransactionType.WITHDRAW:
            return -(tx.amount + tx.commission)
        return -(tx.amount + tx.commission)

    @staticmethod
    def _save_chart(fig: Figure, filename: str) -> Path:
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        path = CHARTS_DIR / filename
        fig.savefig(path)
        plt.close(fig)
        return path




