from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from ..config.schema import CostConfig


@dataclass
class TransactionCostBreakdown:
    commission_cost: float
    spread_cost: float
    impact_cost: float
    timing_cost: float
    total_cost: float
    total_bps: float
    turnover: float


class TransactionCostModel:
    """Estimate and limit transaction costs for rebalancing."""

    def __init__(self, costs: CostConfig) -> None:
        self.commission_bps = getattr(costs, "commission_bps", 0.5)
        self.spread_bps = costs.spread_bps
        self.market_impact_coef = costs.impact_k
        self.timing_slippage_bps = getattr(costs, "timing_slippage_bps", 1.0)

    def estimate_costs(
        self,
        target_weights: pd.Series,
        current_weights: pd.Series,
        adv: pd.Series,
        portfolio_value: float = 1_000_000.0,
    ) -> Dict[str, float]:
        weight_changes = (target_weights - current_weights).fillna(0.0)
        dollar_trades = (weight_changes.abs() * portfolio_value).fillna(0.0)
        total_notional = float(dollar_trades.sum())
        turnover = total_notional / max(portfolio_value, 1e-6)

        commission_cost = total_notional * (self.commission_bps / 10000.0)
        spread_cost = total_notional * (self.spread_bps / 2 / 10000.0)

        adv = adv.reindex(target_weights.index).replace({0: np.nan})
        participation = (
            dollar_trades / adv.replace({0: np.nan})
        ).clip(upper=1.0).fillna(0.0)
        impact_bps = self.market_impact_coef * np.sqrt(participation)
        impact_cost = float((dollar_trades * impact_bps / 10000.0).sum())

        timing_cost = total_notional * (self.timing_slippage_bps / 10000.0)
        total_cost = commission_cost + spread_cost + impact_cost + timing_cost
        total_bps = total_cost / max(portfolio_value, 1e-6) * 10000.0

        return {
            "commission_cost": commission_cost,
            "spread_cost": spread_cost,
            "impact_cost": impact_cost,
            "timing_cost": timing_cost,
            "total_cost": total_cost,
            "total_bps": total_bps,
            "turnover": turnover,
        }

    def optimize_rebalance_threshold(
        self,
        target_weights: pd.Series,
        current_weights: pd.Series,
        adv: pd.Series,
        min_threshold_bps: float = 5.0,
        max_threshold_bps: float = 50.0,
        portfolio_value: float = 1_000_000.0,
    ) -> pd.Series:
        adjusted = target_weights.copy()
        min_threshold = min_threshold_bps / 10000.0
        max_threshold = max_threshold_bps / 10000.0
        weight_changes = (target_weights - current_weights).fillna(0.0)
        for symbol, change in weight_changes.items():
            abs_change = abs(change)
            if abs_change < min_threshold:
                adjusted[symbol] = current_weights.get(symbol, 0.0)
                continue
            if abs_change > max_threshold:
                continue
            adv_value = adv.get(symbol, np.nan)
            if pd.isna(adv_value) or adv_value <= 0:
                continue
            costs = self.estimate_costs(
                pd.Series({symbol: target_weights.get(symbol, 0.0)}),
                pd.Series({symbol: current_weights.get(symbol, 0.0)}),
                pd.Series({symbol: adv_value}),
                portfolio_value=portfolio_value,
            )
            expected_benefit = abs_change * portfolio_value * 0.01
            if costs["total_cost"] > expected_benefit:
                adjusted[symbol] = current_weights.get(symbol, 0.0)
        return adjusted.fillna(0.0)
