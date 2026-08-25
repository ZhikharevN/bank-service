class AccountFrozenError(Exception):
    def __init__(self, message: str = "Operation impossible: account frozen"):
        super().__init__(message)