from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import pandas as pd


@dataclass
class DummyBroker:
    cash: float
    positions: Dict[str, float] = field(default_factory=dict)

    def submit_order(self, symbol: str, quantity: float, price: float) -> None:
        self.cash -= quantity * price
        self.positions[symbol] = self.positions.get(symbol, 0.0) + quantity

    def mark_to_market(self, prices: pd.Series) -> float:
        equity = self.cash
        for symbol, qty in self.positions.items():
            equity += qty * prices.get(symbol, 0.0)
        return equity

    def snapshot(self) -> dict[str, float]:
        return {"cash": self.cash, **self.positions}
