from __future__ import annotations

import numpy as np
import pandas as pd

QUALITY_FIELDS = {
    "ROA": "return_on_assets",
    "GrossMargin": "gross_margin",
    "Accruals": "accruals",
    "EP": "earnings_yield",
}


def _zscore(series: pd.Series) -> pd.Series:
    if series.std(ddof=0) == 0 or series.isna().all():
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / series.std(ddof=0)


def _quality_lite(fundamentals: pd.DataFrame) -> pd.Series:
    gross = fundamentals.get("Gross Profit", fundamentals.get("GrossProfit"))
    assets = fundamentals.get("Total Assets", fundamentals.get("TotalAssets"))
    accruals = fundamentals.get(
        "Operating Cash Flow", fundamentals.get("OperatingCashFlow")
    )
    eps = fundamentals.get("Net Income", fundamentals.get("NetIncome"))
    out = pd.Series(0.0, index=fundamentals.index)
    if gross is not None and assets is not None:
        out = out + _zscore((gross / assets).replace({np.inf: np.nan}))
    if accruals is not None and assets is not None:
        accrual_ratio = 1 - (accruals / assets)
        out = out + _zscore(accrual_ratio.replace({np.inf: np.nan}).fillna(0))
    if eps is not None and assets is not None:
        out = out + _zscore((eps / assets).replace({np.inf: np.nan}).fillna(0))
    return out


def compute_quality_value(
    fundamentals: pd.DataFrame,
    lookahead_guard_days: int = 5,
    fields: list[str] | None = None,
) -> pd.DataFrame:
    """Compute quality-value composite, shifted forward to avoid look-ahead."""
    if fundamentals.empty:
        return pd.DataFrame()
    fields = fields or list(QUALITY_FIELDS.keys())
    fundamentals = fundamentals.copy()
    fundamentals.index = fundamentals.index.set_levels(
        [
            (
                level.tz_localize("UTC")
                if hasattr(level, "tzinfo") and level.tzinfo is None
                else level
            )
            for level in fundamentals.index.levels
        ],
    )
    fundamentals = fundamentals.sort_index()
    fundamentals = fundamentals.groupby(level="symbol").shift(lookahead_guard_days)

    scores: list[pd.DataFrame] = []
    for symbol, group in fundamentals.groupby(level="symbol"):
        frame = group.copy()
        partials = []
        for field in fields:
            if field == "ROA":
                roa = frame.get(
                    "Net Income", frame.get("NetIncome", pd.Series(index=frame.index))
                )
                assets = frame.get(
                    "Total Assets",
                    frame.get("TotalAssets", pd.Series(index=frame.index)),
                )
                val = (roa / assets).replace({np.inf: np.nan})
                partials.append(_zscore(val.fillna(0)))
            elif field == "GrossMargin":
                gross = frame.get(
                    "Gross Profit",
                    frame.get("GrossProfit", pd.Series(index=frame.index)),
                )
                revenue = frame.get(
                    "Total Revenue",
                    frame.get("TotalRevenue", pd.Series(index=frame.index)),
                )
                val = (gross / revenue).replace({np.inf: np.nan})
                partials.append(_zscore(val.fillna(0)))
            elif field == "Accruals":
                net_income = frame.get(
                    "Net Income", frame.get("NetIncome", pd.Series(index=frame.index))
                )
                cash_flow = frame.get(
                    "Operating Cash Flow",
                    frame.get("OperatingCashFlow", pd.Series(index=frame.index)),
                )
                val = (net_income - cash_flow).replace({np.inf: np.nan})
                partials.append(-_zscore(val.fillna(0)))
            elif field == "EP":
                earnings = frame.get(
                    "Net Income", frame.get("NetIncome", pd.Series(index=frame.index))
                )
                equity = frame.get(
                    "Shareholders Equity",
                    frame.get("StockholdersEquity", pd.Series(index=frame.index)),
                )
                val = (earnings / equity).replace({np.inf: np.nan})
                partials.append(_zscore(val.fillna(0)))
        if not partials:
            score = _quality_lite(frame)
        else:
            score = sum(partials) / max(len(partials), 1)
        df = score.to_frame(name="qv_score")
        df["symbol"] = symbol
        scores.append(df)
    if not scores:
        return pd.DataFrame()
    combined = pd.concat(scores)
    combined.index.names = ["date", "symbol"]
    return combined.sort_index()
