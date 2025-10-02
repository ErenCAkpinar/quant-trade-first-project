from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class RegimeState:
    level: str
    weights: dict[str, float]


def _select_price_field(prices: pd.DataFrame) -> pd.DataFrame:
    columns = prices.columns

    if isinstance(columns, pd.MultiIndex):
        fields = columns.get_level_values(0)
        for field in ("adj_close", "close"):
            if field in fields:
                return prices.xs(field, axis=1, level=0)
        available = ", ".join(sorted(set(map(str, fields))))
        raise KeyError(f"No price column found. Available column groups: {available}")

    for field in ("adj_close", "close"):
        if field in columns:
            selected = prices[field]
            # For MultiIndex rows (date, symbol), reshape to wide by symbol
            if isinstance(selected, pd.Series) and selected.index.nlevels > 1:
                return selected.unstack("symbol")
            return selected

    available = ", ".join(map(str, columns))
    raise KeyError(f"No price column found. Available columns: {available}")


def trend_breadth(prices: pd.DataFrame, window: int = 200) -> pd.Series:
    closes = _select_price_field(prices)
    ma = closes.rolling(window=window).mean()
    breadth = (closes > ma).sum(axis=1) / closes.count(axis=1)
    return breadth


def corr_spike(prices: pd.DataFrame, window: int = 60) -> pd.Series:
    closes = _select_price_field(prices)
    returns = closes.pct_change().dropna()
    rolling_corr = returns.rolling(window).corr().groupby(level=0).median()
    return rolling_corr


def vix_curve_state(vix_front: pd.Series, vix_back: pd.Series) -> pd.Series:
    align = pd.concat([vix_front, vix_back], axis=1, join="inner").dropna()
    align.columns = ["front", "back"]
    return np.where(align["back"] > align["front"], 1.0, -1.0)


def regime_weights(
    breadth: pd.Series,
    thresholds: Dict[str, float],
    base_allocations: Dict[str, Dict[str, float]],
    neutral_weights: Dict[str, float],
) -> dict[pd.Timestamp, dict[str, float]]:
    weights: dict[pd.Timestamp, dict[str, float]] = {}
    risk_off_cut = thresholds["risk_off"]
    risk_on_cut = thresholds["risk_on"]
    for ts, value in breadth.items():
        if value <= risk_off_cut:
            weights[ts] = base_allocations.get("risk_off", neutral_weights)
        elif value >= risk_on_cut:
            weights[ts] = base_allocations.get("risk_on", neutral_weights)
        else:
            # Interpolate to neutral weights when in the middle
            weights[ts] = neutral_weights
    return weights
