class NightOperationsError(Exception):
    def __init__(self, start: str, end: str):
        super().__init__(f"Operations are forbidden from {start} to {end}")
