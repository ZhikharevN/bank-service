class ClientBlockedError(Exception):
    def __init__(self, message: str = "Client is blocked"):
        super().__init__(message)
