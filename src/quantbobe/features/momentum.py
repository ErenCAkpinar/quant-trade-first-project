from __future__ import annotations

import numpy as np
import pandas as pd


def _compute_return(
    prices: pd.Series, lookback: int, skip_months: int = 1
) -> pd.Series:
    offset = skip_months * 21
    lag = lookback * 21 + offset
    shifted = prices.shift(lag)
    reference = prices.shift(offset)
    return (reference / shifted) - 1.0


def cross_sectional_momentum(
    prices: pd.DataFrame,
    sectors: dict[str, str],
    lookback_months: int = 12,
    skip_recent_month: bool = True,
) -> pd.DataFrame:
    """Compute 12-1M momentum ranks by sector."""
    if prices.empty:
        return pd.DataFrame()
    skip = 1 if skip_recent_month else 0
    momentum = prices.groupby(level="symbol")[["adj_close"]].apply(
        lambda df: _compute_return(df["adj_close"], lookback_months, skip)
    )
    momentum = momentum.reset_index(level=0, drop=True).to_frame("momentum")
    momentum = momentum.dropna()
    if momentum.empty:
        return pd.DataFrame()
    df = (
        momentum.reset_index().rename(columns={"level_0": "date"})
        if "level_0" in momentum.index.names
        else momentum.reset_index()
    )
    df.columns = ["date", "symbol", "momentum"]
    df["sector"] = df["symbol"].map(sectors)
    results: list[pd.DataFrame] = []
    for _date, group in df.groupby("date"):
        ranked = group.copy()
        ranked["rank"] = ranked.groupby("sector")["momentum"].transform(
            lambda x: x.rank(pct=True)
        )
        ranked["signal"] = np.where(
            ranked["rank"] >= 0.8, 1.0, np.where(ranked["rank"] <= 0.2, -1.0, 0.0)
        )
        ranked["weight_hint"] = ranked["rank"] - 0.5
        results.append(ranked)
    combined = pd.concat(results, ignore_index=True)
    combined.set_index(["date", "symbol"], inplace=True)
    return combined[["signal", "weight_hint", "momentum", "sector"]]
