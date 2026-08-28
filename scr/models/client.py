from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from scr.enums.client_status import ClientStatus
from scr.models.abstract_account import AbstractAccount

if TYPE_CHECKING:
    from scr.models.transaction import Transaction


@dataclass
class Client:
    first_name: str
    last_name: str
    surname: str
    accounts: list[AbstractAccount]
    phone: str
    email: str
    age: int
    account_number: str = field(repr=False)
    password: str = field(repr=False)
    bad_entries: int = field(default=0)
    status: ClientStatus = field(default=ClientStatus.ACTIVE, init=False)
    history: set[Transaction] = field(default_factory=set)

    def __post_init__(self):
        if self.age < 18:
            raise ValueError("Age must be greater than or equal to 18")
