from __future__ import annotations

import numpy as np
import pandas as pd

from quantbobe.features.momentum import cross_sectional_momentum


def build_prices():
    dates = pd.date_range("2020-01-01", periods=260, freq="B")
    symbols = ["AAA", "AAB", "ABA", "ABB"]
    frames = []
    for symbol in symbols:
        df = pd.DataFrame(
            {
                "date": dates,
                "open": 100 + np.arange(len(dates)),
                "close": 100 + np.arange(len(dates)),
                "adj_close": 100 + np.arange(len(dates)),
            }
        )
        df["symbol"] = symbol
        frames.append(df)
    prices = pd.concat(frames)
    prices.set_index(["date", "symbol"], inplace=True)
    return prices


def test_cross_sectional_momentum_sector_neutral():
    prices = build_prices()
    sectors = {"AAA": "Tech", "AAB": "Tech", "ABA": "Health", "ABB": "Health"}
    signals = cross_sectional_momentum(
        prices,
        sectors,
        lookback_months=3,
        skip_recent_month=False,
    )
    latest = signals.groupby(level="date").tail(1)
    grouped = latest.groupby("sector")
    for _, group in grouped:
        assert abs(group["signal"].sum()) < 1e-6
