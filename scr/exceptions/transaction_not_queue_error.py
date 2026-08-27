class TransactionNotInQueueError(LookupError):
    def __init__(self):
        super().__init__(f"transaction is not in the queue")