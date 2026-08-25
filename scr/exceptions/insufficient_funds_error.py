class InsufficientFundsError(Exception):
    def __init__(self, message: str = "Operation impossible: insufficient funds"):
        super().__init__(message)
