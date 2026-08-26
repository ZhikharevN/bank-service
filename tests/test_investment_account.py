from decimal import Decimal

from scr.enums.asset_type import AssetType
from scr.models.asset import Asset
from scr.models.investment_account import InvestmentAccount


def test_add_asset_creates_position(make_account) -> None:
    account = make_account(InvestmentAccount)
    asset = Asset(AssetType.STOCK, Decimal("10.00"), Decimal("0.10"))
    account.add_asset(asset, 5)
    assert account.positions[AssetType.STOCK].quantity == 5


def test_sell_asset_adds_money_and_reduces_quantity(make_account) -> None:
    account = make_account(InvestmentAccount)
    asset = Asset(AssetType.STOCK, Decimal("10.00"), Decimal("0.10"))
    account.add_asset(asset, 5)
    account.sell_asset(AssetType.STOCK, 2)
    assert account.positions[AssetType.STOCK].quantity == 3
    assert account.balance == Decimal("120.00")


def test_project_yearly_growth(make_account) -> None:
    account = make_account(InvestmentAccount)
    asset = Asset(AssetType.STOCK, Decimal("100.00"), Decimal("0.10"))
    account.add_asset(asset, 1)
    assert account.project_yearly_growth(1) == Decimal("110.00")


def test_get_account_info_includes_positions(make_account) -> None:
    info = make_account(InvestmentAccount).get_account_info()
    assert info["positions"] == {}
    assert info["total_balance"] == Decimal("100.00")
