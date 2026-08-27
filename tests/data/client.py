import pytest

from scr.models.client import Client


@pytest.fixture
def make_client():
    def _make(*, accounts=None, **overrides) -> Client:
        params = {
            "first_name": "Ivan",
            "last_name": "Petrov",
            "surname": "Ivanovich",
            "accounts": accounts if accounts is not None else [],
            "phone": "79001234567",
            "email": "ivan@test.com",
            "age": 25,
            "account_number": "ACC-001",
            "password": "secret",
        }
        params.update(overrides)
        return Client(**params)

    return _make
