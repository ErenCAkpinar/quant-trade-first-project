from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = returns - risk_free / TRADING_DAYS
    if excess.std(ddof=0) == 0:
        return 0.0
    return np.sqrt(TRADING_DAYS) * excess.mean() / excess.std(ddof=0)


def sortino_ratio(returns: pd.Series) -> float:
    downside = returns[returns < 0]
    if downside.std(ddof=0) == 0:
        return 0.0
    return np.sqrt(TRADING_DAYS) * returns.mean() / downside.std(ddof=0)


def max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return dd.min()


def calmar_ratio(equity: pd.Series) -> float:
    dd = abs(max_drawdown(equity))
    if dd == 0:
        return 0.0
    cagr = equity.iloc[-1] / equity.iloc[0]
    years = len(equity) / TRADING_DAYS
    cagr = cagr ** (1 / years) - 1
    return cagr / dd if dd else 0.0


def value_at_risk(returns: pd.Series, alpha: float = 0.95) -> float:
    return returns.quantile(1 - alpha)
