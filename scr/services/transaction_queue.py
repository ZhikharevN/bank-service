import heapq
from dataclasses import dataclass, field
from itertools import count
from uuid import UUID

from scr.enums.transaction_status import TransactionStatus
from scr.exceptions.transaction_not_queue_error import TransactionNotInQueueError
from scr.models.transaction import Transaction


@dataclass
class TransactionQueue:
    _heap: list[tuple[int, int, Transaction]] = field(default_factory=list)
    _active: dict[UUID, Transaction] = field(default_factory=dict)
    _seq: count = field(default_factory=count)

    def add(self, transaction: Transaction, priority: int) -> None:
        heapq.heappush(self._heap, (priority, next(self._seq), transaction))
        self._active[transaction.id] = transaction

    def cancel(self, transaction: Transaction) -> None:
        tx = self._active.pop(transaction.id, None)
        if tx is None:
            raise TransactionNotInQueueError()
        tx.status = TransactionStatus.CANCELED

    def pop(self) -> Transaction | None:
        while self._heap:
            _, _, transaction = heapq.heappop(self._heap)
            if self._active.get(transaction.id) is transaction:
                del self._active[transaction.id]
                return transaction
        return None
