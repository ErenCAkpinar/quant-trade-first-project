from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _ensure_wide(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return prices
    if prices.index.nlevels == 2 and "symbol" in prices.index.names:
        # data provided as MultiIndex rows (date, symbol)
        if isinstance(prices, pd.Series):
            return prices.unstack("symbol")
        if isinstance(prices, pd.DataFrame):
            if {"adj_close", "close"}.intersection(prices.columns):
                column = "adj_close" if "adj_close" in prices.columns else "close"
                return prices[column].unstack("symbol")
    return prices


@dataclass
class MomentumConfig:
    timeframes: List[Tuple[int, float]]
    skip_recent_month: bool = True
    min_history_months: int = 15


class MultiTimeframeMomentum:
    """Blend multiple lookbacks with quality and crash protection filters."""

    def __init__(self, config: MomentumConfig | None = None) -> None:
        if config is None:
            config = MomentumConfig(
                timeframes=[(3, 0.25), (6, 0.35), (12, 0.40)],
                skip_recent_month=True,
                min_history_months=15,
            )
        total_weight = sum(weight for _, weight in config.timeframes)
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"Momentum weights must sum to 1.0, got {total_weight}")
        self.config = config

    def compute_single_momentum(
        self, prices: pd.DataFrame, lookback_months: int, skip_recent: bool
    ) -> pd.DataFrame:
        lookback_days = lookback_months * 21
        skip_days = 21 if skip_recent else 0
        ref = prices.shift(skip_days)
        hist = prices.shift(lookback_days + skip_days)
        momentum = (ref / hist) - 1.0
        return momentum

    def compute_momentum_quality(
        self, returns: pd.DataFrame, lookback_days: int
    ) -> pd.DataFrame:
        rolling = returns.rolling(window=lookback_days, min_periods=lookback_days // 2)
        mean = rolling.mean()
        std = rolling.std(ddof=0).replace(0, np.nan)
        quality = (mean / std).replace([np.inf, -np.inf], np.nan)
        return quality

    def compute_combined_momentum(
        self, prices: pd.DataFrame, use_quality_filter: bool = True
    ) -> pd.DataFrame:
        wide = _ensure_wide(prices)
        if wide.empty:
            return wide
        returns = wide.pct_change(fill_method=None)
        combined = pd.DataFrame(0.0, index=wide.index, columns=wide.columns)
        for lookback, weight in self.config.timeframes:
            mom = self.compute_single_momentum(
                wide, lookback, self.config.skip_recent_month
            )
            if use_quality_filter:
                quality = self.compute_momentum_quality(returns, lookback * 21)
                mom = mom * quality
            ranked = mom.rank(axis=1, pct=True, method="average")
            combined = combined.add(ranked.fillna(0) * weight, fill_value=0)
        combined = combined.rank(axis=1, pct=True, method="average")
        return combined.fillna(0)

    def compute_momentum_crash_scale(
        self,
        returns: pd.DataFrame,
        vol_window: int = 60,
        long_window: int = 252,
    ) -> pd.Series:
        if returns.empty:
            return pd.Series(dtype=float)
        vol = returns.rolling(
            window=vol_window,
            min_periods=vol_window // 2,
        ).std(ddof=0)
        realized = vol.mean(axis=1)
        long_ma = realized.rolling(
            window=long_window,
            min_periods=long_window // 4,
        ).mean()
        long_std = realized.rolling(
            window=long_window,
            min_periods=long_window // 4,
        ).std(ddof=0)
        z = (realized - long_ma) / long_std.replace(0, np.nan)
        z = z.clip(lower=-3, upper=3).fillna(0)
        scale = 1.0 - (z.clip(lower=0) / 3.0) * 0.5
        return scale.clip(lower=0.4, upper=1.0)

    def _sector_neutral_long_short(
        self,
        ranks: pd.Series,
        sectors: Dict[str, str],
        top_quantile: float,
        bottom_quantile: float,
    ) -> pd.Series:
        weights = pd.Series(0.0, index=ranks.index)
        by_sector: Dict[str, List[str]] = {}
        for symbol, sector in sectors.items():
            by_sector.setdefault(sector or "Unknown", []).append(symbol)
        if not by_sector:
            by_sector = {"Universe": ranks.index.tolist()}
        sector_count = max(len(by_sector), 1)
        sectors_iter = by_sector.items()
        for _sector, members in sectors_iter:
            symbols = ranks.reindex(members).dropna()
            if symbols.empty:
                continue
            n = len(symbols)
            n_long = max(1, int(n * top_quantile))
            n_short = max(1, int(n * bottom_quantile))
            longs = symbols.nlargest(n_long)
            shorts = symbols.nsmallest(n_short)
            long_weight = 1.0 / (sector_count * n_long)
            short_weight = -1.0 / (sector_count * n_short)
            weights.loc[longs.index] = long_weight
            weights.loc[shorts.index] = short_weight
        return weights

    def generate_long_short_portfolio(
        self,
        prices: pd.DataFrame,
        sectors: Dict[str, str],
        top_quantile: float = 0.2,
        bottom_quantile: float = 0.2,
        sector_neutral: bool = True,
        rebal_freq: str = "M",
        scores: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        wide = _ensure_wide(prices)
        if wide.empty:
            return pd.DataFrame(columns=wide.columns)
        combined = (
            scores.reindex(columns=wide.columns)
            if scores is not None
            else self.compute_combined_momentum(wide, use_quality_filter=True)
        )
        returns = wide.pct_change(fill_method=None).fillna(0)
        crash_scale = self.compute_momentum_crash_scale(returns)
        freq = "ME" if rebal_freq == "M" else rebal_freq
        grouped = combined.groupby(pd.Grouper(freq=freq))
        weights: list[pd.Series] = []
        for _, frame in grouped:
            if frame.empty:
                continue
            date = frame.index.max()
            if date not in combined.index:
                continue
            ranks = combined.loc[date].dropna()
            if ranks.empty:
                continue
            if sector_neutral:
                weight = self._sector_neutral_long_short(
                    ranks, sectors, top_quantile, bottom_quantile
                )
            else:
                n = len(ranks)
                n_long = max(1, int(n * top_quantile))
                n_short = max(1, int(n * bottom_quantile))
                longs = ranks.nlargest(n_long).index
                shorts = ranks.nsmallest(n_short).index
                weight = pd.Series(0.0, index=ranks.index)
                weight.loc[longs] = 1.0 / n_long
                weight.loc[shorts] = -1.0 / n_short
            scale = float(crash_scale.get(date, 1.0)) if not crash_scale.empty else 1.0
            weight = weight * float(scale)
            weights.append(pd.Series(weight, name=date))
        if not weights:
            return pd.DataFrame(columns=wide.columns)
        result = pd.DataFrame(weights).sort_index()
        return result.reindex(columns=wide.columns).fillna(0.0)
