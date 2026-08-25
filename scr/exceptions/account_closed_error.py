class AccountClosedError(Exception):
    def __init__( self, message: str = "Operation impossible: account closed"):
        super().__init__(message)