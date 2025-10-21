from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


def _extract_prices(data: pd.DataFrame, field: str) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    if field not in data.columns:
        raise KeyError(f"{field} not found in daily data columns")
    series = data[field]
    if isinstance(series, pd.Series) and series.index.nlevels == 2:
        return series.unstack("symbol")
    if isinstance(series, pd.DataFrame):
        return series
    raise TypeError("Unsupported data format for mean reversion extraction")


@dataclass
class MeanReversionConfig:
    lookback_window: int = 20
    z_score_threshold: float = 2.0
    min_observations: int = 10
    vol_scaling: bool = True
    trend_window: int = 50
    gap_weight: float = 0.5


class MeanReversionSignals:
    """Daily mean reversion model with multiple filters."""

    def __init__(self, config: MeanReversionConfig | None = None) -> None:
        self.config = config or MeanReversionConfig()

    def _rolling_stats(self, returns: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        mean = returns.rolling(
            window=self.config.lookback_window,
            min_periods=self.config.min_observations,
        ).mean()
        std = returns.rolling(
            window=self.config.lookback_window,
            min_periods=self.config.min_observations,
        ).std(ddof=0)
        return mean, std.replace(0, np.nan)

    def compute_z_scores(self, returns: pd.DataFrame) -> pd.DataFrame:
        mean, std = self._rolling_stats(returns)
        z = (returns - mean) / std
        z = z.replace([np.inf, -np.inf], np.nan)
        return z.fillna(0.0)

    def filter_trending(self, closes: pd.DataFrame) -> pd.DataFrame:
        sma_short = closes.rolling(window=10, min_periods=10).mean()
        sma_long = closes.rolling(
            window=self.config.trend_window, min_periods=self.config.trend_window // 2
        ).mean()
        spread = (sma_short - sma_long) / sma_long.replace(0, np.nan)
        return (spread.abs() < 0.02).fillna(False)

    def compute_overnight_gaps(self, data: pd.DataFrame) -> pd.DataFrame:
        if {"open", "close"}.isdisjoint(data.columns):
            return pd.DataFrame()
        opens = _extract_prices(data, "open")
        closes = _extract_prices(data, "close")
        prev_close = closes.shift(1)
        gaps = (opens - prev_close) / prev_close.replace(0, np.nan)
        return gaps.replace([np.inf, -np.inf], 0).fillna(0)

    def gap_signals(self, gaps: pd.DataFrame) -> pd.DataFrame:
        if gaps.empty:
            return gaps
        z = self.compute_z_scores(gaps)
        capped = (-z.clip(-3, 3)) / 3.0
        return capped.fillna(0.0)

    def volatility_scale(self, returns: pd.DataFrame) -> pd.DataFrame:
        vol = returns.rolling(20, min_periods=5).std(ddof=0)
        inv_vol = 1 / vol.replace(0, np.nan)
        inv_vol = inv_vol.replace([np.inf, -np.inf], np.nan)
        norm = inv_vol.sum(axis=1, skipna=True)
        scale = inv_vol.div(norm, axis=0)
        return scale.fillna(0.0)

    def generate_signals(
        self,
        data: pd.DataFrame,
        regime_filter: Optional[pd.Series] = None,
    ) -> pd.DataFrame:
        closes = _extract_prices(data, "adj_close") if "adj_close" in data.columns else _extract_prices(data, "close")
        if closes.empty:
            return closes
        returns = closes.pct_change(fill_method=None).fillna(0)
        price_filter = self.filter_trending(closes)
        z_scores = self.compute_z_scores(returns)
        extremes = (z_scores.abs() >= self.config.z_score_threshold)
        signals = -z_scores.where(extremes & price_filter, 0.0)
        if self.config.gap_weight > 0:
            gaps = self.compute_overnight_gaps(data)
            gap_signal = self.gap_signals(gaps)
            signals = (1 - self.config.gap_weight) * signals + self.config.gap_weight * gap_signal.reindex(signals.index).fillna(0.0)
        if regime_filter is not None:
            signals = signals.mul(regime_filter.clip(lower=0.0), axis=0)
        if self.config.vol_scaling:
            scale = self.volatility_scale(returns)
            signals = signals * scale
        signals = signals.clip(-1.0, 1.0).fillna(0.0)
        return signals

    def latest_target(
        self,
        signals: pd.DataFrame,
        risk_budget: float,
    ) -> pd.Series:
        if signals.empty:
            return pd.Series(dtype=float)
        latest = signals.iloc[-1].copy()
        total = latest.abs().sum()
        if total > 0:
            latest *= risk_budget / total
        return latest
