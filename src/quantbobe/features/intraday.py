from __future__ import annotations

import numpy as np
import pandas as pd


def compute_vwap(df: pd.DataFrame) -> float:
    volume = df["volume"].sum()
    if volume == 0:
        return float(df["close"].iloc[-1])
    return float((df["close"] * df["volume"]).sum() / volume)


def vwap_zscores(
    intraday: pd.DataFrame,
    latest_daily: pd.DataFrame,
    sectors: dict[str, str],
    sector_proxies: dict[str, str] | None = None,
    z_entry: float = 1.5,
    earnings_blackout: list[str] | None = None,
    min_dollar_vol: float = 5_000_000,
) -> pd.DataFrame:
    """Compute VWAP deviation Z-scores for intraday mean-reversion sleeve."""
    if intraday.empty:
        return pd.DataFrame()
    sector_proxies = sector_proxies or {}
    blackout: set[str] = set(earnings_blackout) if earnings_blackout else set()

    intraday = intraday.copy()
    intraday.index.names = ["timestamp", "symbol"]
    latest_daily = latest_daily.reset_index()
    latest_daily = latest_daily.sort_values("date").groupby("symbol").tail(1)

    signals: list[dict[str, float | str]] = []
    for symbol, group in intraday.groupby(level="symbol"):
        if symbol in blackout:
            continue
        daily = latest_daily[latest_daily["symbol"] == symbol]
        if daily.empty:
            continue
        last_close = float(daily["close"].iloc[-1])
        dollar_volume = float(daily["close"].iloc[-1] * daily["volume"].iloc[-1])
        if dollar_volume < min_dollar_vol:
            continue
        vwap = compute_vwap(group.reset_index(level="symbol", drop=True))
        zscore = (last_close - vwap) / max(np.std(group["close"].values[-20:]), 1e-3)
        sector = sectors.get(symbol, "Unknown")
        signals.append(
            {
                "symbol": symbol,
                "sector": sector,
                "zscore": zscore,
                "signal": float(np.clip(-zscore / z_entry, -1.5, 1.5)),
            }
        )
    if not signals:
        return pd.DataFrame()
    df = pd.DataFrame(signals)
    df.set_index("symbol", inplace=True)
    return df
