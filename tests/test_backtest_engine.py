from __future__ import annotations

import pandas as pd

from quantbobe.backtest.engine import BacktestEngine
from quantbobe.config.schema import CostConfig


def test_backtest_engine_executes_trades_and_applies_costs():
    dates = pd.date_range("2020-01-01", periods=5, freq="B")
    records = []
    for date in dates:
        records.append({"date": date, "symbol": "AAA", "open": 100.0, "close": 102.0, "adj_close": 102.0})
    prices = pd.DataFrame(records).set_index(["date", "symbol"])
    cost = CostConfig(spread_bps=2, impact_k=0.9, borrow_bps_month=30)
    engine = BacktestEngine(cost)
    target = pd.DataFrame(0.1, index=dates, columns=["AAA"])
    result = engine.run(prices, {"test": target})
    assert result.trades, "Expected at least one trade"
    assert result.equity_curve.iloc[-1] != result.equity_curve.iloc[0]
