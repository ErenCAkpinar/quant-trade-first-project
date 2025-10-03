from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SlippageModel:
    spread_bps: float
    impact_k: float

    def estimate_cost(self, participation: float) -> float:
        participation = max(participation, 1e-6)
        half_spread = 0.5 * self.spread_bps / 10000.0
        impact = self.impact_k * (participation**1.5)
        return half_spread + impact
