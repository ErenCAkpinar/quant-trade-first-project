from __future__ import annotations

import pandas as pd

from quantbobe.portfolio.constraints import clamp_beta


def test_beta_clamp_limits_portfolio_beta():
    weights = pd.Series({"A": 0.1, "B": -0.1, "C": 0.2})
    betas = {"A": 1.2, "B": 0.8, "C": 1.5}
    adjusted = clamp_beta(weights, betas, max_abs_beta=0.05)
    beta_series = pd.Series(betas).reindex(adjusted.index).fillna(1.0)
    portfolio_beta = float((adjusted * beta_series).sum())
    assert abs(portfolio_beta) <= 0.051
