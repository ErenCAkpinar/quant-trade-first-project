from __future__ import annotations

import pandas as pd
import pytest

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
    initial_equity = 1_000_000.0
    result = engine.run(prices, {"test": target}, initial_equity=initial_equity)

    assert result.trades, "Expected at least one trade"

    first_trade = result.trades[0]
    first_date = dates[0]
    open_price = prices.loc[(first_date, "AAA"), "open"]
    close_price = prices.loc[(first_date, "AAA"), "close"]
    participation = abs(target.loc[first_date, "AAA"])
    expected_trade_price = open_price * (1 + engine.slippage.estimate_cost(participation))

    assert first_trade.price == pytest.approx(expected_trade_price)

    execution_cost = first_trade.quantity * (first_trade.price - open_price)
    mark_to_market = first_trade.quantity * (close_price - open_price)
    expected_equity = initial_equity + mark_to_market - execution_cost

    assert execution_cost > 0
    assert result.equity_curve.iloc[0] == pytest.approx(expected_equity)
