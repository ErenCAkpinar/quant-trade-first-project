from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def realized_vol(returns: pd.DataFrame, window: int = 20) -> pd.Series:
    return returns.rolling(window).std(ddof=0) * np.sqrt(TRADING_DAYS)


def scale_to_target(
    weights: pd.DataFrame, returns: pd.DataFrame, target_vol: float
) -> pd.DataFrame:
    portfolio_returns = (weights.shift().multiply(returns, axis=0)).sum(axis=1)
    vol = realized_vol(portfolio_returns.to_frame("ptf"), window=20)["ptf"]
    scale = target_vol / vol.replace(0, np.nan)
    scale = scale.clip(upper=3.0).fillna(1.0)
    return weights.multiply(scale, axis=0)
