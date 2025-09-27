from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable

import numpy as np
import pandas as pd

from .config.loader import load_settings
from .config.schema import Settings
from .data import IDataProvider, build_provider, load_daily_history, load_fundamentals
from .data.base import SymbolMeta
from .features.momentum import cross_sectional_momentum
from .features.quality_value import compute_quality_value
from .features.regimes import trend_breadth
from .features.risk import scale_to_target
from .portfolio.sizing import apply_constraints, inverse_vol_weights


@dataclass
class StrategyContext:
    settings: Settings
    provider: IDataProvider
    meta: list[SymbolMeta]
    daily: pd.DataFrame
    fundamentals: pd.DataFrame


def build_context(config_path: str) -> StrategyContext:
    settings = load_settings(config_path)
    provider = build_provider(settings)
    meta = provider.get_symbol_meta()
    symbols = [m.symbol for m in meta]
    daily = load_daily_history(
        provider,
        symbols,
        datetime.combine(settings.data.start, datetime.min.time()),
        datetime.combine(settings.data.end, datetime.min.time()),
    )
    fundamentals = load_fundamentals(provider, symbols)
    return StrategyContext(settings=settings, provider=provider, meta=meta, daily=daily, fundamentals=fundamentals)


def _sector_map(meta: Iterable[SymbolMeta]) -> Dict[str, str]:
    return {m.symbol: m.sector or "Unknown" for m in meta}


def compute_sleeve_weights(ctx: StrategyContext) -> Dict[str, pd.DataFrame]:
    data = ctx.daily.copy()
    settings = ctx.settings
    sectors = _sector_map(ctx.meta)
    closes = data["adj_close"].unstack("symbol") if "adj_close" in data.columns else data["close"].unstack("symbol")
    returns = closes.pct_change().dropna()

    breadth = trend_breadth(data)
    last_breadth = float(breadth.dropna().iloc[-1]) if not breadth.dropna().empty else 0.5
    risk_off = settings.regimes.breadth_thresholds.get("risk_off", 0.45)
    risk_on = settings.regimes.breadth_thresholds.get("risk_on", 0.6)
    regime_scale_c = 1.0
    regime_scale_d = 1.0
    if last_breadth <= risk_off:
        regime_scale_c = 0.7
        regime_scale_d = 0.5
    elif last_breadth >= risk_on:
        regime_scale_c = 1.0
        regime_scale_d = 1.0
    else:
        alpha = (last_breadth - risk_off) / max(risk_on - risk_off, 1e-6)
        regime_scale_c = 0.7 + 0.3 * alpha
        regime_scale_d = 0.5 + 0.5 * alpha

    sleeve_weights: dict[str, pd.DataFrame] = {}

    sleeves = settings.sleeves
    if sleeves.C_xsec_qv.enabled:
        lookback = sleeves.C_xsec_qv.params.lookback_mom_months if sleeves.C_xsec_qv.params else 12
        skip_recent = sleeves.C_xsec_qv.params.skip_recent_month if sleeves.C_xsec_qv.params else True
        momentum = cross_sectional_momentum(data, sectors, lookback or 12, skip_recent)
        qv = compute_quality_value(
            ctx.fundamentals,
            fields=(sleeves.C_xsec_qv.params.qv_fields if sleeves.C_xsec_qv.params else None),
        )
        if qv.empty or "qv_score" not in qv.columns:
            qv = momentum.copy()[[]]
            qv["qv_score"] = 0.0
        # align indexes
        idx = momentum.index.union(qv.index, sort=False)
        momentum = momentum.reindex(idx).fillna(0)
        qv = qv.reindex(idx).fillna(0)
        combined = momentum.join(qv, how="left")
        combined["combined_score"] = combined[["weight_hint", "qv_score"]].sum(axis=1)
        frame = combined[["combined_score"]].reset_index()
        # Ensure date column is datetime, handling timezone-aware datetimes
        frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None)
        frame["month"] = frame["date"].dt.to_period("M")
        target_rows: list[pd.Series] = []
        top_q = sleeves.C_xsec_qv.params.top_quantile if sleeves.C_xsec_qv.params else 0.2
        bottom_q = sleeves.C_xsec_qv.params.bottom_quantile if sleeves.C_xsec_qv.params else 0.2
        risk_budget = (sleeves.C_xsec_qv.risk_budget or 0.85) * regime_scale_c
        for period, group in frame.groupby("month"):
            latest_date = group["date"].max()
            snapshot = group[group["date"] == latest_date]
            scores = snapshot.set_index("symbol")["combined_score"].sort_values(ascending=False)
            if scores.empty:
                continue
            n = len(scores)
            top_n = max(1, int(n * top_q))
            bottom_n = max(1, int(n * bottom_q))
            longs = scores.head(top_n)
            shorts = scores.tail(bottom_n)
            long_weights = longs / longs.abs().sum() if longs.abs().sum() != 0 else longs
            short_weights = -shorts / shorts.abs().sum() if shorts.abs().sum() != 0 else shorts
            target = pd.concat([long_weights, short_weights])
            target = target.reindex(closes.columns).fillna(0.0)
            returns_window = returns.loc[:latest_date].tail(60)
            inv_vol = inverse_vol_weights(returns_window, risk_budget)
            target = target * inv_vol.reindex(target.index).fillna(0)
            target_rows.append(pd.Series(target, name=latest_date))
        if target_rows:
            weights_df = pd.DataFrame(target_rows).sort_index()
            betas = {symbol: 1.0 for symbol in weights_df.columns}
            constrained = weights_df.apply(
                lambda row: apply_constraints(
                    row,
                    sectors,
                    betas,
                    settings.portfolio.max_name_weight,
                    0.05,
                    settings.portfolio.sector_neutral,
                ),
                axis=1,
            )
            sleeve_weights["C_xsec_qv"] = constrained

    if sleeves.D_intraday_rev.enabled:
        risk_budget = (sleeves.D_intraday_rev.risk_budget or 0.15) * regime_scale_d
        tilts = returns.tail(1)
        if not tilts.empty:
            rev = -tilts.iloc[0]
            vol = returns.rolling(10).std(ddof=0).tail(1).iloc[0]
            rev = rev / vol.replace(0, np.nan)
            rev = rev.replace([np.inf, -np.inf], 0).fillna(0)
            rev = rev.clip(-1.0, 1.0)
            rev = rev * risk_budget / rev.abs().sum() if rev.abs().sum() != 0 else rev
            sleeve_weights["D_intraday_rev"] = pd.DataFrame([rev], index=[tilts.index[-1]])

    if not sleeve_weights:
        raise ValueError("No sleeves enabled; ensure configuration enables at least one sleeve")

    return sleeve_weights


def aggregate_target_weights(ctx: StrategyContext, sleeve_weights: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    closes = ctx.daily["adj_close"].unstack("symbol") if "adj_close" in ctx.daily.columns else ctx.daily["close"].unstack("symbol")
    returns = closes.pct_change().dropna()
    aligned = []
    for df in sleeve_weights.values():
        df = df.reindex(returns.index).ffill().fillna(0)
        aligned.append(df)
    target = sum(aligned)
    target = target.reindex(returns.index).fillna(0.0)
    target = scale_to_target(target, returns, ctx.settings.portfolio.target_vol_ann)
    return target
