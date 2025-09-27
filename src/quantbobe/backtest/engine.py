from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from ..config.schema import CostConfig
from ..execution.slippage import SlippageModel


@dataclass
class Trade:
    date: pd.Timestamp
    symbol: str
    quantity: float
    price: float
    notional: float
    sleeve: str


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    positions: pd.DataFrame
    trades: List[Trade]
    pnl: pd.Series


class BacktestEngine:
    def __init__(self, costs: CostConfig) -> None:
        self.costs = costs
        self.slippage = SlippageModel(costs.spread_bps, costs.impact_k)

    def run(self, prices: pd.DataFrame, target_weights: Dict[str, pd.DataFrame], initial_equity: float = 1_000_000.0) -> BacktestResult:
        closes = prices["close"].unstack("symbol")
        opens = prices["open"].unstack("symbol")
        adj_close = prices.get("adj_close", closes).unstack("symbol") if "adj_close" in prices.columns else closes
        dates = closes.index

        positions = pd.DataFrame(0.0, index=dates, columns=closes.columns)
        cash = pd.Series(initial_equity, index=dates)
        equity = pd.Series(initial_equity, index=dates)
        trades: list[Trade] = []
        current_pos = pd.Series(0.0, index=closes.columns)

        borrow_daily = self.costs.borrow_daily

        for i, date in enumerate(dates):
            price_row = opens.iloc[i] if i < len(opens) else closes.iloc[i]
            day_close = closes.iloc[i]

            desired_weight = sum(df.loc[date] for df in target_weights.values() if date in df.index)
            desired_weight = desired_weight.reindex(closes.columns).fillna(0.0)

            equity_prev = equity.iloc[i - 1] if i > 0 else initial_equity
            target_notional = desired_weight * equity_prev
            current_notional = current_pos * price_row
            need_trade = target_notional - current_notional

            for symbol, notional in need_trade.items():
                if abs(notional) < 1.0:
                    continue
                side = np.sign(notional)
                participation = min(abs(notional) / max(equity_prev, 1.0), 1.0)
                cost = self.slippage.estimate_cost(participation)
                trade_price = price_row[symbol] * (1 + cost if side > 0 else 1 - cost)
                qty = notional / max(trade_price, 1e-6)
                current_pos[symbol] += qty
                cash.iloc[i] -= qty * trade_price
                trades.append(Trade(date=date, symbol=symbol, quantity=qty, price=trade_price, notional=qty * trade_price, sleeve="aggregate"))

            mark_to_market = (current_pos * day_close).sum()
            borrow_cost = (current_pos[current_pos < 0] * day_close[current_pos < 0]).sum() * borrow_daily
            cash.iloc[i] -= borrow_cost
            equity.iloc[i] = cash.iloc[i] + mark_to_market
            positions.iloc[i] = current_pos

            if i + 1 < len(dates):
                cash.iloc[i + 1] = cash.iloc[i]

        pnl = equity.diff().fillna(0.0)
        return BacktestResult(equity_curve=equity, positions=positions, trades=trades, pnl=pnl)
