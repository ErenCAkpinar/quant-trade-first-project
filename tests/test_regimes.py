from __future__ import annotations

import pandas as pd

from quantbobe.features.regimes import regime_weights


def test_regime_weights_interpolates_between_states():
    breadth = pd.Series(
        [0.4, 0.5, 0.7],
        index=pd.date_range("2020-01-01", periods=3, freq="D"),
    )
    thresholds = {"risk_off": 0.45, "risk_on": 0.60}
    base = {
        "risk_off": {"C": 0.6, "D": 0.4},
        "risk_on": {"C": 0.8, "D": 0.2},
    }
    neutral = {"C": 0.7, "D": 0.3}
    weights = regime_weights(breadth, thresholds, base, neutral)
    assert weights[breadth.index[0]] == base["risk_off"]
    assert weights[breadth.index[-1]] == base["risk_on"]
    mid = weights[breadth.index[1]]
    assert abs(mid["C"] - 0.7) < 1e-6
    assert abs(mid["D"] - 0.3) < 1e-6
