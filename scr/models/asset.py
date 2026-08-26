from dataclasses import dataclass
from decimal import Decimal

from scr.enums.asset_type import AssetType


@dataclass
class Asset:
    asset_type: AssetType
    current_price: Decimal
    expected_annual_return: Decimal
