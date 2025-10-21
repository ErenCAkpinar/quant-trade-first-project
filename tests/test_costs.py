from __future__ import annotations

import pandas as pd

from quantbobe.config.schema import CostConfig
from quantbobe.portfolio.costs import TransactionCostModel


def test_transaction_cost_model_skips_small_trades():
    costs = CostConfig(
        spread_bps=2.0,
        impact_k=0.1,
        borrow_bps_month=30.0,
        commission_bps=0.5,
        timing_slippage_bps=1.0,
    )
    model = TransactionCostModel(costs)
    current = pd.Series({"AAA": 0.05, "BBB": -0.05})
    target = pd.Series({"AAA": 0.0501, "BBB": -0.0499})
    adv = pd.Series({"AAA": 5_000_000.0, "BBB": 5_000_000.0})
    optimized = model.optimize_rebalance_threshold(
        target, current, adv, min_threshold_bps=5.0, max_threshold_bps=50.0
    )
    pd.testing.assert_series_equal(optimized, current)


def test_transaction_cost_model_estimates_costs():
    costs = CostConfig()
    model = TransactionCostModel(costs)
    current = pd.Series({"AAA": 0.0})
    target = pd.Series({"AAA": 0.1})
    adv = pd.Series({"AAA": 10_000_000.0})
    estimates = model.estimate_costs(target, current, adv, portfolio_value=1_000_000.0)
    assert estimates["total_cost"] > 0
    assert 0 < estimates["total_bps"] < 100
