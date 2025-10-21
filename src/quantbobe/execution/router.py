from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

import pandas as pd

from .broker_alpaca import OrderTicket
from .slippage import SlippageModel


@dataclass
class OrderSlice:
    symbol: str
    target: float
    current: float
    price: float


class ExecutionRouter:
    def __init__(self, slippage: SlippageModel) -> None:
        self.slippage = slippage

    def build_orders(
        self, slices: Iterable[OrderSlice], equity: float
    ) -> List[OrderTicket]:
        tickets: list[OrderTicket] = []
        for slc in slices:
            notional = equity * (slc.target - slc.current)
            if abs(notional) < 1.0:
                continue
            side = "buy" if notional > 0 else "sell"
            base_qty = abs(notional) / max(slc.price, 1e-4)
            if side == "sell":
                current_qty = max(equity * slc.current / max(slc.price, 1e-4), 0.0)
                closing_qty = min(base_qty, current_qty)
                short_qty = max(base_qty - closing_qty, 0.0)
                short_whole = math.floor(short_qty + 1e-9)
                qty = closing_qty + short_whole
                if qty <= 1e-6:
                    continue
            else:
                qty = base_qty
            participation = min(abs(base_qty) / 1_000_000, 1.0)
            cost = self.slippage.estimate_cost(participation)
            limit_price = slc.price * (1 + cost if side == "buy" else 1 - cost)
            ticket = OrderTicket(
                symbol=slc.symbol,
                qty=qty,
                side=side,
                type="limit",
                limit_price=limit_price,
            )
            tickets.append(ticket)
        return tickets

    def reconcile_positions(
        self,
        target_weights: pd.Series,
        current_weights: pd.Series,
        prices: pd.Series,
        equity: float,
    ) -> List[OrderSlice]:
        slices: list[OrderSlice] = []
        for symbol, target in target_weights.items():
            price = float(prices.get(symbol, 0.0))
            if price == 0:
                continue
            current = float(current_weights.get(symbol, 0.0))
            slices.append(
                OrderSlice(symbol=symbol, target=target, current=current, price=price)
            )
        return slices
