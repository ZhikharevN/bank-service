from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from scr.audit.audit_report_service import AuditReportService
from scr.enums.client_status import ClientStatus
from scr.enums.currency import Currency
from scr.models.bank import Bank
from scr.models.bank_account import BankAccount
from scr.models.client import Client
from scr.models.premium_account import PremiumAccount
from scr.models.savings_account import SavingsAccount

DAYTIME = datetime(2026, 8, 29, 12, 0)
NIGHT = datetime(2026, 8, 29, 2, 0)


# Мокаем время
@contextmanager
def at(moment: datetime):
    with (
        patch("scr.services.risk_analyzer.datetime") as risk_dt,
        patch("scr.services.transaction_processor.datetime") as proc_dt,
    ):
        risk_dt.now.return_value = moment
        proc_dt.now.return_value = moment
        yield


def _client(first: str, last: str, accounts, *, n: int) -> Client:
    return Client(
        first_name=first,
        last_name=last,
        surname="Ivanovich" if n % 2 else "Petrovna",
        accounts=accounts,
        phone=f"7900123456{n}",
        email=f"{first.lower()}@bank.test",
        age=20 + n,
        account_number=f"ACC-{n:03d}",
        password="secret",
    )


def _drain(bank: Bank, times: int) -> None:
    for _ in range(times):
        bank.process_next()


# Демонстрация
def demonstration_day_6() -> None:
    bank = Bank(fx_rates={(Currency.USD, Currency.RUB): Decimal("30")})

    ivan_main = BankAccount(currency=Currency.RUB, balance=Decimal("50000.00"))
    ivan_extra = BankAccount(currency=Currency.RUB, balance=Decimal("5000.00"))
    maria_save = SavingsAccount(currency=Currency.RUB, balance=Decimal("15000.00"))
    maria_card = BankAccount(currency=Currency.RUB, balance=Decimal("2000.00"))
    petr_prem = PremiumAccount(currency=Currency.RUB, balance=Decimal("8000.00"))
    olga_vip = BankAccount(currency=Currency.RUB, balance=Decimal("250000.00"))
    olga_pocket = BankAccount(currency=Currency.RUB, balance=Decimal("500.00"))
    sergey_big = BankAccount(currency=Currency.RUB, balance=Decimal("25000.00"))
    sergey_small = BankAccount(currency=Currency.RUB, balance=Decimal("3000.00"))
    anna_main = BankAccount(currency=Currency.RUB, balance=Decimal("1000.00"))
    anna_save = SavingsAccount(currency=Currency.RUB, balance=Decimal("4000.00"))
    dmitry_main = BankAccount(currency=Currency.RUB, balance=Decimal("10000.00"))
    elena_a = BankAccount(currency=Currency.RUB, balance=Decimal("2000.00"))
    elena_b = BankAccount(currency=Currency.RUB, balance=Decimal("7000.00"))

    ivan = _client("Ivan", "Sidorov", [ivan_main, ivan_extra], n=1)
    maria = _client("Maria", "Orlova", [maria_save, maria_card], n=2)
    petr = _client("Petr", "Volkov", [petr_prem], n=3)
    olga = _client("Olga", "Kozlova", [olga_vip, olga_pocket], n=4)
    sergey = _client("Sergey", "Novikov", [sergey_big, sergey_small], n=5)
    anna = _client("Anna", "Lebedeva", [anna_main, anna_save], n=6)
    dmitry = _client("Dmitry", "Morozov", [dmitry_main], n=7)
    elena = _client("Elena", "Frolova", [elena_a, elena_b], n=8)

    clients = [ivan, maria, petr, olga, sergey, anna, dmitry, elena]

    for client in clients:
        bank.add_client(client)

    ivan, maria, petr, olga, sergey, anna, dmitry, elena = clients

    # Формируем операции, в результате чего формируются транзакции, попадающие в очередь
    accounts = [acc for client in clients for acc in client.accounts]
    queued = 0
    with at(DAYTIME):
        for amount in ("200.00", "350.00", "80.00", "120.00", "45.00"):
            bank.submit_deposit(ivan, ivan_extra, Decimal(amount))
            queued += 1
        for amount in ("100.00", "250.00", "60.00"):
            bank.submit_withdraw(maria, maria_card, Decimal(amount))
            queued += 1
        for amount in ("500.00", "75.00", "30.00", "90.00"):
            bank.submit_deposit(petr, petr_prem, Decimal(amount))
            queued += 1
        for amount in ("40.00", "55.00"):
            bank.submit_withdraw(dmitry, dmitry_main, Decimal(amount))
            queued += 1
        bank.submit_deposit(anna, anna_main, Decimal("300.00"))
        bank.submit_deposit(elena, elena_a, Decimal("150.00"))
        queued += 2
        bank.submit_transfer(ivan, ivan_main, maria, maria_card, Decimal("400.00"))
        bank.submit_transfer(maria, maria_save, petr, petr_prem, Decimal("200.00"))
        bank.submit_transfer(petr, petr_prem, dmitry, dmitry_main, Decimal("150.00"))
        bank.submit_transfer(dmitry, dmitry_main, elena, elena_b, Decimal("100.00"))
        bank.submit_transfer(olga, olga_pocket, anna, anna_save, Decimal("50.00"))
        queued += 5
        bank.submit_withdraw(olga, olga_vip, Decimal("100000.00"))
        bank.submit_withdraw(olga, olga_vip, Decimal("120000.00"))
        bank.submit_deposit(olga, olga_vip, Decimal("100000.00"))
        bank.submit_withdraw(sergey, sergey_big, Decimal("15000.00"))
        bank.submit_withdraw(sergey, sergey_big, Decimal("13000.00"))
        queued += 5
        bank.submit_withdraw(olga, olga_pocket, Decimal("10000.00"))
        bank.submit_withdraw(anna, anna_main, Decimal("5000.00"))
        bank.submit_withdraw(elena, elena_a, Decimal("9000.00"))
        queued += 3
        Bank.freeze_account(maria_save)
        bank.submit_withdraw(maria, maria_save, Decimal("100.00"))
        bank.submit_deposit(maria, maria_save, Decimal("50.00"))
        queued += 2
        Bank.unfreeze_account(maria_save)
        Bank.close_account(sergey_small)
        bank.submit_deposit(sergey, sergey_small, Decimal("10.00"))
        queued += 1
        Bank.open_account(sergey_small)
        anna.status = ClientStatus.BLOCKED
        bank.submit_withdraw(anna, anna_save, Decimal("20.00"))
        queued += 1
        anna.status = ClientStatus.ACTIVE
        _drain(bank, queued)
    night_queued = 0

    with at(NIGHT):
        bank.submit_withdraw(ivan, ivan_main, Decimal("10.00"))
        bank.submit_deposit(elena, elena_b, Decimal("25.00"))
        bank.submit_transfer(sergey, sergey_big, ivan, ivan_extra, Decimal("80.00"))
        night_queued += 3
        _drain(bank, night_queued)

    errors = AuditReportService.error_stats(bank)
    suspicious = AuditReportService.suspicious_by_reason(bank)
    print("Clients and accounts:")
    for client in clients:
        print(f"clients={client} accounts={client.accounts}")
    print("errors:")
    for reason, txs in errors.items():
        print(f"  {reason}: {len(txs)}")
    print("suspicious:")
    for reason, txs in suspicious.items():
        print(f"  {reason}: {len(txs)}")

demonstration_day_6()
