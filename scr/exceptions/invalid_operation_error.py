class InvalidOperationError(Exception):
    def __init__(self, message: str = "Invalid operation"):
        super().__init__(message)
