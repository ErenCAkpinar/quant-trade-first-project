from __future__ import annotations

import numpy as np
import pandas as pd


def enforce_sector_neutrality(weights: pd.Series, sectors: dict[str, str]) -> pd.Series:
    df = pd.DataFrame({"weight": weights})
    df["sector"] = df.index.map(sectors)
    adj = df.groupby("sector")["weight"].transform(lambda x: x - x.mean())
    return adj


def clamp_beta(weights: pd.Series, betas: dict[str, float], max_abs_beta: float = 0.05) -> pd.Series:
    beta_series = pd.Series(betas)
    beta_series = beta_series.reindex(weights.index).fillna(1.0)
    portfolio_beta = float((weights * beta_series).sum())
    if abs(portfolio_beta) <= max_abs_beta:
        return weights
    adjustment = portfolio_beta
    hedge = (beta_series ** 2).sum()
    if hedge == 0:
        return weights
    scaled = weights - (adjustment / hedge) * beta_series
    return scaled


def max_weight_clip(weights: pd.Series, max_weight: float) -> pd.Series:
    clipped = weights.clip(lower=-max_weight, upper=max_weight)
    scale = max(1.0, clipped.abs().sum())
    return clipped / scale
