import enum


class TransactionStatus(enum.Enum):
    CREATED = "created"
    COMPLETED = "completed"
    CANCELED = "canceled"
    REJECTED = "rejected"
