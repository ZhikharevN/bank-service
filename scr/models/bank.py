from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal

from scr.enums.account_status import AccountStatus
from scr.enums.client_status import ClientStatus
from scr.exceptions.client_blocked_error import ClientBlockedError
from scr.exceptions.night_operations_error import NightOperationsError
from scr.models.abstract_account import AbstractAccount
from scr.models.client import Client
from scr.models.suspicious_action import SuspiciousAction


@dataclass
class Bank:
    clients: list[Client] = field(default_factory=list)
    NIGHT_START = time(0, 0)
    NIGHT_END = time(5, 0)
    SUSPICIOUS_AMOUNT = Decimal("100000")

    def add_client(self, client: Client):
        self.clients.append(client)

    @staticmethod
    def open_account(account: AbstractAccount):
        account.status = AccountStatus.ACTIVE

    @staticmethod
    def close_account(account: AbstractAccount):
        account.status = AccountStatus.CLOSED

    @staticmethod
    def freeze_account(account: AbstractAccount):
        account.status = AccountStatus.FROZEN

    @staticmethod
    def unfreeze_account(account: AbstractAccount):
        account.status = AccountStatus.ACTIVE

    @staticmethod
    def authenticate_client(client: Client, password: str):
        if client.status == ClientStatus.BLOCKED:
            raise ClientBlockedError()

        if client.password != password:
            client.bad_entries += 1

        if client.bad_entries == 3:
            client.status = ClientStatus.BLOCKED

    @staticmethod
    def search_accounts(client: Client):
        return client.accounts

    @staticmethod
    def get_total_balance(client: Client) -> Decimal:
        total_balance = Decimal(0)
        for account in client.accounts:
            total_balance += account.balance
        return total_balance

    def execute_deposit(
        self,
        client: Client,
        account: AbstractAccount,
        amount: Decimal,
    ) -> None:
        self._prepare_operation(client, account, amount, "deposit")
        account.deposit(amount)

    def execute_withdraw(
        self,
        client: Client,
        account: AbstractAccount,
        amount: Decimal,
    ) -> None:
        self._prepare_operation(client, account, amount, "withdraw")
        account.withdraw(amount)

    def _prepare_operation(
        self,
        client: Client,
        account: AbstractAccount,
        amount: Decimal,
        operation: str,
    ) -> None:
        if client.status == ClientStatus.BLOCKED:
            raise ClientBlockedError()
        self._assert_operating_hours()
        self._flag_if_suspicious(client, account, amount, operation)

    def _assert_operating_hours(self) -> None:
        current = datetime.now().time()
        if self.NIGHT_START <= current < self.NIGHT_END:
            raise NightOperationsError(str(self.NIGHT_START), str(self.NIGHT_END))

    def _flag_if_suspicious(
        self,
        client: Client,
        account: AbstractAccount,
        amount: Decimal,
        operation: str,
    ) -> None:
        reasons = []
        if amount >= self.SUSPICIOUS_AMOUNT:
            reasons.append("large amount")
        if account.balance > Decimal("10000") and amount > account.balance / 2:
            reasons.append("more than half of balance")
        if not reasons:
            return
        client.suspicious_actions.append(
            SuspiciousAction(
                at=datetime.now(),
                operation=operation,
                amount=amount,
                reason="; ".join(reasons),
            )
        )
