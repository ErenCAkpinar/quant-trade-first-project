from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .constraints import clamp_beta, enforce_sector_neutrality, max_weight_clip


def inverse_vol_weights(returns: pd.DataFrame, risk_budget: float = 1.0) -> pd.Series:
    vol = returns.rolling(60).std(ddof=0).iloc[-1]
    inv_vol = 1 / vol.replace(0, pd.NA)
    inv_vol = inv_vol.replace([np.inf, -np.inf], pd.NA).fillna(0)
    weights = inv_vol / inv_vol.abs().sum()
    return weights * risk_budget


def apply_constraints(
    target: pd.Series,
    sectors: Dict[str, str],
    betas: Dict[str, float],
    max_name_weight: float,
    beta_limit: float,
    enforce_sector: bool,
) -> pd.Series:
    weights = target.copy()
    if enforce_sector:
        weights = enforce_sector_neutrality(weights, sectors)
    weights = clamp_beta(weights, betas, max_abs_beta=beta_limit)
    weights = max_weight_clip(weights, max_name_weight)
    return weights


def combine_sleeves(weights: Dict[str, pd.Series]) -> pd.Series:
    aggregate = sum(weights.values())
    total = aggregate.abs().sum()
    if total == 0:
        return aggregate
    return aggregate / total
