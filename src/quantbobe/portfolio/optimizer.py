from __future__ import annotations

import numpy as np
import pandas as pd


def shrink_covariance(returns: pd.DataFrame, shrinkage: float = 0.1) -> pd.DataFrame:
    sample = returns.cov()
    diag = pd.DataFrame(
        np.diag(np.diag(sample.values)), index=sample.index, columns=sample.columns
    )
    return (1 - shrinkage) * sample + shrinkage * diag


def risk_parity_weights(cov: pd.DataFrame) -> pd.Series:
    inv_var = 1 / np.diag(cov)
    weights = inv_var / inv_var.sum()
    return pd.Series(weights, index=cov.index)


def solve_inverse_vol(returns: pd.DataFrame, shrinkage: float = 0.1) -> pd.Series:
    cov = shrink_covariance(returns, shrinkage)
    weights = risk_parity_weights(cov)
    return weights
