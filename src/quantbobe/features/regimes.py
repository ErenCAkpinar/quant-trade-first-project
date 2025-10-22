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
    returns = closes.pct_change(fill_method=None).dropna()
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


@dataclass
class RegimeOutcome:
    label: str
    momentum_scale: float
    mean_reversion_scale: float


class RegimeDetector:
    """Multi-factor regime scores for risk scaling."""

    def __init__(
        self,
        breadth_window: int = 200,
        vol_window: int = 20,
        corr_window: int = 60,
        dispersion_window: int = 20,
    ) -> None:
        self.breadth_window = breadth_window
        self.vol_window = vol_window
        self.corr_window = corr_window
        self.dispersion_window = dispersion_window

    def _wide_prices(self, prices: pd.DataFrame) -> pd.DataFrame:
        return _select_price_field(prices)

    def _realized_vol(self, returns: pd.DataFrame) -> pd.Series:
        vol = returns.rolling(
            window=self.vol_window,
            min_periods=self.vol_window // 2,
        ).std(ddof=0)
        return vol.mean(axis=1).ffill()

    def _corr_score(self, returns: pd.DataFrame) -> pd.Series:
        if returns.shape[1] < 2:
            return pd.Series(0.0, index=returns.index)
        rolling = returns.rolling(
            window=self.corr_window,
            min_periods=self.corr_window // 2,
        )
        correlations = rolling.corr().groupby(level=0).apply(
            lambda mat: mat.where(
                np.triu(np.ones(mat.shape), k=1).astype(bool)
            ).stack().mean()
        )
        return correlations.ffill().fillna(0.0)

    def _dispersion(self, returns: pd.DataFrame) -> pd.Series:
        dispersion = returns.rolling(
            window=self.dispersion_window,
            min_periods=5,
        ).std(ddof=0)
        return dispersion.mean(axis=1).ffill().fillna(0.0)

    def evaluate(self, prices: pd.DataFrame) -> pd.DataFrame:
        wide = self._wide_prices(prices)
        if wide.empty:
            return pd.DataFrame(
                columns=["label", "momentum_scale", "mean_reversion_scale"]
            )
        returns = wide.pct_change(fill_method=None).dropna()
        breadth = trend_breadth(prices, window=self.breadth_window)
        breadth = breadth.reindex(returns.index).ffill()
        realized_vol = self._realized_vol(returns)
        corr = self._corr_score(returns)
        dispersion = self._dispersion(returns)

        breadth_score = (1 - breadth.clip(0, 1)).fillna(0.5)
        long_mean = realized_vol.rolling(252, min_periods=60).mean()
        long_std = realized_vol.rolling(252, min_periods=60).std(ddof=0)
        vol_z = (realized_vol - long_mean) / long_std
        vol_score = vol_z.clip(lower=-2, upper=4)
        vol_min = vol_score.min()
        vol_max = vol_score.max()
        vol_range = vol_max - vol_min
        if pd.isna(vol_range) or vol_range == 0:
            vol_score = vol_score.fillna(0.5)
        else:
            vol_score = (vol_score - vol_min) / vol_range
        corr_score = corr.clip(lower=-1, upper=1).abs()
        median_disp = (
            dispersion.rolling(252, min_periods=60)
            .median()
            .replace(0, np.nan)
        )
        disp_score = dispersion / median_disp
        disp_score = disp_score.clip(lower=0, upper=5)
        disp_min = disp_score.min()
        disp_max = disp_score.max()
        disp_range = disp_max - disp_min
        if pd.isna(disp_range) or disp_range == 0:
            disp_score = disp_score.fillna(0.3)
        else:
            disp_score = (disp_score - disp_min) / disp_range

        risk_level = (
            0.45 * breadth_score
            + 0.30 * vol_score.fillna(0.5)
            + 0.15 * corr_score.fillna(0.3)
            + 0.10 * disp_score.fillna(0.3)
        )

        records: list[tuple[pd.Timestamp, RegimeOutcome]] = []
        for date, score in risk_level.items():
            breadth_val = float(breadth_score.get(date, 0.5))
            vol_val = float(vol_score.get(date, 0.5))
            corr_val = float(corr_score.get(date, 0.3))
            if score >= 0.7:
                outcome = RegimeOutcome("risk_off", 0.6, 0.3)
            elif vol_val >= 0.7 and breadth_val <= 0.5:
                outcome = RegimeOutcome("volatile", 0.6, 0.4)
            elif score <= 0.4 and breadth_val >= 0.55:
                outcome = RegimeOutcome("risk_on", 1.0, 1.0)
            else:
                mean_rev = 0.7 if corr_val < 0.6 else 0.5
                outcome = RegimeOutcome("transition", 0.85, mean_rev)
            records.append((date, outcome))

        index = [ts for ts, _ in records]
        df = pd.DataFrame(
            {
                "label": [outcome.label for _, outcome in records],
                "momentum_scale": [
                    outcome.momentum_scale for _, outcome in records
                ],
                "mean_reversion_scale": [
                    outcome.mean_reversion_scale for _, outcome in records
                ],
            },
            index=index,
        )
        return df.sort_index()
