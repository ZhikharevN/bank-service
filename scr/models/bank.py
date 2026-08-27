from dataclasses import dataclass, field
from decimal import Decimal

from scr.enums.account_status import AccountStatus
from scr.enums.client_status import ClientStatus
from scr.enums.currency import Currency
from scr.enums.transaction_type import TransactionType
from scr.exceptions.client_blocked_error import ClientBlockedError
from scr.models.abstract_account import AbstractAccount
from scr.models.client import Client
from scr.models.transaction import Transaction
from scr.services.transaction_processor import TransactionProcessor
from scr.services.transaction_queue import TransactionQueue


@dataclass
class Bank:
    clients: list[Client] = field(default_factory=list)
    queue: TransactionQueue = field(default_factory=TransactionQueue)
    fx_rates: dict[tuple[Currency, Currency], Decimal] = field(default_factory=dict)
    processor: TransactionProcessor = field(init=False)

    def __post_init__(self) -> None:
        self.processor = TransactionProcessor(queue=self.queue, rates=self.fx_rates)

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

    def submit_deposit(
        self,
        client: Client,
        account: AbstractAccount,
        amount: Decimal,
        *,
        priority: int = 0,
    ) -> Transaction:
        tx = Transaction(
            type=TransactionType.DEPOSIT,
            sender=client,
            receiver=client,
            amount=amount,
            currency=self._account_currency(account),
            commission=Decimal("0"),
            priority=priority,
            receiver_account=account,
        )
        self.queue.add(tx, priority)
        return tx

    def submit_withdraw(
        self,
        client: Client,
        account: AbstractAccount,
        amount: Decimal,
        *,
        priority: int = 0,
    ) -> Transaction:
        tx = Transaction(
            type=TransactionType.WITHDRAW,
            sender=client,
            receiver=client,
            amount=amount,
            currency=self._account_currency(account),
            commission=Decimal("0"),
            priority=priority,
            sender_account=account,
        )
        self.queue.add(tx, priority)
        return tx

    def submit_transfer(
        self,
        sender: Client,
        sender_account: AbstractAccount,
        receiver: Client,
        receiver_account: AbstractAccount,
        amount: Decimal,
        *,
        priority: int = 0,
    ) -> Transaction:
        tx = Transaction(
            type=TransactionType.TRANSFER,
            sender=sender,
            receiver=receiver,
            amount=amount,
            currency=self._account_currency(sender_account),
            commission=Decimal("0"),
            priority=priority,
            sender_account=sender_account,
            receiver_account=receiver_account,
        )
        self.queue.add(tx, priority)
        return tx

    def cancel_transaction(self, transaction: Transaction) -> None:
        self.queue.cancel(transaction)

    def process_next(self) -> None:
        self.processor.process_next()

    @staticmethod
    def _account_currency(account: AbstractAccount) -> Currency:
        currency = getattr(account, "currency", None)
        if not isinstance(currency, Currency):
            raise TypeError("account has no currency")
        return currency
