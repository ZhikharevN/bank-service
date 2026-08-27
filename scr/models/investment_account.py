from dataclasses import dataclass, field
from decimal import Decimal

from scr.enums.account_type import AccountType
from scr.enums.asset_type import AssetType
from scr.exceptions.insufficient_funds_error import InsufficientFundsError
from scr.models.asset import Asset
from scr.models.bank_account import BankAccount
from scr.models.position import Position


@dataclass
class InvestmentAccount(BankAccount):
    positions: dict[AssetType, Position] = field(default_factory=dict)
    type: AccountType = field(default=AccountType.INVESTMENT_ACCOUNT, init=False)

    def add_asset(self, asset: Asset, quantity: int) -> None:
        self._validate_status()
        if asset.asset_type in self.positions.keys():
            position = self.positions[asset.asset_type]
            position.quantity += quantity
        else:
            self.positions[asset.asset_type] = Position(asset, quantity)

    def sell_asset(self, asset_type: AssetType, quantity: int) -> None:
        self._validate_status()
        position = self.positions.get(asset_type)
        if position is None or position.quantity < quantity:
            raise InsufficientFundsError()
        self.balance += quantity * position.asset.current_price
        position.quantity -= quantity

    # Calculates the projected value of all assets after a specified number of years
    def project_yearly_growth(self, years: int) -> Decimal:
        total_projected_value = Decimal("0")

        for pos in self.positions.values():
            # We calculate the future value of the position: PV * (1 + r)^years
            pv = pos.asset.current_price * pos.quantity
            r = pos.asset.expected_annual_return
            fv = pv * ((1 + r) ** years)
            total_projected_value += fv

        return Decimal(round(total_projected_value, 2))

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update({
            "positions": self.positions.copy(),
            "total_balance": self._get_balance_with_actives()
        })
        return info

    def _get_balance_with_actives(self) -> Decimal:
        total_balance = self.balance
        for position in self.positions.values():
            total_balance += position.asset.current_price * position.quantity
        return total_balance

    def __str__(self) -> str:
        return (f"Type: {self.type}, status: {self.status}, balance: {self.balance}, currency: {self.currency}, "
                f"positions: {self.positions}, balance with all actives: {self._get_balance_with_actives()}")
