from dataclasses import dataclass

from scr.models.asset import Asset


@dataclass
class Position:
    asset: Asset
    quantity: int
