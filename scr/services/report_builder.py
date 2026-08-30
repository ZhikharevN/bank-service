from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from scr.audit.audit_report_service import AuditReportService
from scr.models.bank import Bank
from scr.models.client import Client
from scr.models.transaction import Transaction
from scr.services.report_service import ReportService


def _client_name(client: Client) -> str:
    return f"{client.last_name} {client.first_name}"


def _tx_row(tx: Transaction) -> dict[str, str]:
    return {
        "id": str(tx.id),
        "type": tx.type.value,
        "status": tx.status.value,
        "amount": str(tx.amount),
        "commission": str(tx.commission),
        "currency": tx.currency.value,
        "sender": _client_name(tx.sender),
        "receiver": _client_name(tx.receiver),
        "errors": "; ".join(error.message for error in tx.errors),
        "suspicious": "; ".join(tx.suspicious_actions),
    }

def _account_rows(client: Client) -> list[dict[str, str]]:
    return [
        {
            "client": _client_name(client),
            "id": str(account.id),
            "type": account.type.value,
            "status": account.status.value,
            "currency": getattr(account, "currency", None) and account.currency.value or "",
            "balance": str(account.balance),
        }
        for account in client.accounts
    ]


@dataclass
class Report:
    title: str
    kind: str
    tables: dict[str, list[dict[str, str]]]

    def to_text(self) -> str:
        lines = [self.title, ""]
        for table_name, rows in self.tables.items():
            lines.append(table_name)
            if not rows:
                lines.append("  (empty)")
                lines.append("")
                continue
            headers = list(rows[0].keys())
            lines.append("  " + " | ".join(headers))
            for row in rows:
                lines.append("  " + " | ".join(row.get(header, "") for header in headers))
            lines.append("")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {"title": self.title, "kind": self.kind, "tables": self.tables},
            ensure_ascii=False,
            indent=2,
        )

    def export_to_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    def export_to_csv(self, directory: Path) -> list[Path]:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for table_name, rows in self.tables.items():
            file_path = directory / f"{self.kind}_{table_name}.csv"
            fieldnames = list(rows[0].keys()) if rows else []
            with file_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            written.append(file_path)
        return written


class ReportBuilder:
    @staticmethod
    def for_client(client: Client) -> Report:
        transactions = sorted(client.history, key=lambda tx: tx.timestamp)
        return Report(
            title=f"Client report: {_client_name(client)}",
            kind="client",
            tables={
                "profile": [
                    {
                        "name": _client_name(client),
                        "email": client.email,
                        "phone": client.phone,
                        "status": client.status.value,
                        "accounts": str(len(client.accounts)),
                        "balance": str(client.get_sum_balance()),
                        "transactions": str(len(transactions)),
                    }
                ],
                "accounts": _account_rows(client),
                "transactions": [_tx_row(tx) for tx in transactions],
            },
        )

    @staticmethod
    def for_bank(bank: Bank) -> Report:
        clients = bank.clients
        accounts = [row for client in clients for row in _account_rows(client)]
        transactions = sorted(
            AuditReportService._unique_transactions(bank),
            key=lambda tx: tx.timestamp,
        )
        type_stats = ReportService.transactions_statistic(bank)
        return Report(
            title="Bank report",
            kind="bank",
            tables={
                "summary": [
                    {
                        "clients": str(len(clients)),
                        "accounts": str(len(accounts)),
                        "balance": str(ReportService.sum_balance(bank)),
                        "transactions": str(len(transactions)),
                    }
                ],
                "clients": [
                    {
                        "name": _client_name(client),
                        "email": client.email,
                        "status": client.status.value,
                        "accounts": str(len(client.accounts)),
                        "balance": str(client.get_sum_balance()),
                        "transactions": str(len(client.history)),
                    }
                    for client in clients
                ],
                "accounts": accounts,
                "transaction_types": [
                    {"type": tx_type, "count": str(len(txs))}
                    for tx_type, txs in type_stats.items()
                ],
                "transactions": [_tx_row(tx) for tx in transactions],
            },
        )

    @staticmethod
    def for_risks(bank: Bank) -> Report:
        errors = AuditReportService.error_stats(bank)
        suspicious = AuditReportService.suspicious_by_reason(bank)
        error_rows = [
            _tx_row(tx) | {"reason": reason}
            for reason, txs in errors.items()
            for tx in txs
        ]
        suspicious_rows = [
            _tx_row(tx) | {"reason": reason}
            for reason, txs in suspicious.items()
            for tx in txs
        ]
        return Report(
            title="Risk report",
            kind="risk",
            tables={
                "error_summary": [
                    {"reason": reason, "count": str(len(txs))}
                    for reason, txs in errors.items()
                ],
                "suspicious_summary": [
                    {"reason": reason, "count": str(len(txs))}
                    for reason, txs in suspicious.items()
                ],
                "errors": error_rows,
                "suspicious": suspicious_rows,
            },
        )
