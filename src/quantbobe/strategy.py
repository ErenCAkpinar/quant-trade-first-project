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
from .features.mean_reversion import MeanReversionConfig, MeanReversionSignals
from .features.momentum_multi import MomentumConfig, MultiTimeframeMomentum
from .features.quality_value import compute_quality_value
from .features.regimes import RegimeDetector
from .features.risk import scale_to_target
from .portfolio.costs import TransactionCostModel
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
    start_dt = datetime.combine(settings.data.start, datetime.min.time())
    end_date = settings.data.end
    end_dt = (
        datetime.combine(end_date, datetime.min.time())
        if end_date is not None
        else datetime.now()
    )
    daily = load_daily_history(provider, symbols, start_dt, end_dt)
    fundamentals = load_fundamentals(provider, symbols)
    return StrategyContext(
        settings=settings,
        provider=provider,
        meta=meta,
        daily=daily,
        fundamentals=fundamentals,
    )


def _sector_map(meta: Iterable[SymbolMeta]) -> Dict[str, str]:
    return {m.symbol: m.sector or "Unknown" for m in meta}


def compute_sleeve_weights(ctx: StrategyContext) -> Dict[str, pd.DataFrame]:
    data = ctx.daily.copy()
    settings = ctx.settings
    sectors = _sector_map(ctx.meta)
    closes = (
        data["adj_close"].unstack("symbol")
        if "adj_close" in data.columns
        else data["close"].unstack("symbol")
    )
    returns = closes.pct_change(fill_method=None)
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")

    detector = RegimeDetector(
        breadth_window=settings.regimes.breadth_window_days,
        vol_window=settings.regimes.vol_window_days,
        corr_window=settings.regimes.corr_window_days,
        dispersion_window=settings.regimes.dispersion_window_days,
    )
    regime_frame = detector.evaluate(data)
    if regime_frame.empty:
        momentum_scale_series = pd.Series(1.0, index=closes.index)
        mean_rev_scale_series = pd.Series(1.0, index=closes.index)
    else:
        regime_frame = regime_frame.reindex(closes.index).ffill()
        momentum_scale_series = regime_frame["momentum_scale"].fillna(1.0)
        mean_rev_scale_series = regime_frame["mean_reversion_scale"].fillna(1.0)
    regime_scale_c = float(momentum_scale_series.iloc[-1]) if not momentum_scale_series.empty else 1.0
    regime_scale_d = float(mean_rev_scale_series.iloc[-1]) if not mean_rev_scale_series.empty else 1.0

    sleeve_weights: dict[str, pd.DataFrame] = {}

    sleeves = settings.sleeves
    if sleeves.C_xsec_qv.enabled:
        params = sleeves.C_xsec_qv.params
        if params and params.lookback_mom_months:
            timeframes = [(params.lookback_mom_months, 1.0)]
        else:
            timeframes = [(3, 0.25), (6, 0.35), (12, 0.40)]
        momentum_config = MomentumConfig(
            timeframes=timeframes,
            skip_recent_month=params.skip_recent_month if params else True,
        )
        momentum_model = MultiTimeframeMomentum(momentum_config)
        mom_scores = momentum_model.compute_combined_momentum(closes)
        if not mom_scores.empty:
            qv = compute_quality_value(
                ctx.fundamentals,
                fields=params.qv_fields if params and params.qv_fields else None,
            )
            if not qv.empty and "qv_score" in qv.columns:
                qv_wide = (
                    qv["qv_score"]
                    .unstack("symbol")
                    .reindex(mom_scores.index)
                    .ffill()
                    .fillna(0.0)
                )
                qv_ranks = qv_wide.rank(axis=1, pct=True, method="average").fillna(0.5)
            else:
                qv_ranks = pd.DataFrame(
                    0.5, index=mom_scores.index, columns=mom_scores.columns
                )
            blended_scores = (
                0.65 * mom_scores.reindex_like(qv_ranks).fillna(0.5)
                + 0.35 * qv_ranks.reindex_like(mom_scores).fillna(0.5)
            )
            top_q = params.top_quantile if params and params.top_quantile else 0.2
            bottom_q = (
                params.bottom_quantile if params and params.bottom_quantile else 0.2
            )
            rebal_freq = sleeves.C_xsec_qv.rebalance or "M"

            weights_df = momentum_model.generate_long_short_portfolio(
                closes,
                sectors,
                top_quantile=top_q,
                bottom_quantile=bottom_q,
                sector_neutral=settings.portfolio.sector_neutral,
                rebal_freq=rebal_freq,
                scores=blended_scores,
            )
            if not weights_df.empty:
                betas = {symbol: 1.0 for symbol in weights_df.columns}
                rows: list[pd.Series] = []
                base_budget = sleeves.C_xsec_qv.risk_budget or 0.85
                for date, row in weights_df.iterrows():
                    hist_returns = returns.loc[:date].tail(60)
                    budget = base_budget * float(
                        momentum_scale_series.reindex([date]).fillna(regime_scale_c).iloc[0]
                    )
                    if hist_returns.empty or budget == 0:
                        scaled = pd.Series(0.0, index=row.index)
                    else:
                        inv_vol = inverse_vol_weights(hist_returns, budget)
                        scaled = row * inv_vol.reindex(row.index).fillna(0.0)
                    constrained = apply_constraints(
                        scaled,
                        sectors,
                        betas,
                        settings.portfolio.max_name_weight,
                        0.05,
                        settings.portfolio.sector_neutral,
                    )
                    rows.append(pd.Series(constrained, name=date))
                if rows:
                    sleeve_weights["C_xsec_qv"] = pd.DataFrame(rows).sort_index()

    if sleeves.D_intraday_rev.enabled:
        params = sleeves.D_intraday_rev.params
        rev_config = MeanReversionConfig(
            lookback_window=20,
            z_score_threshold=params.z_entry if params and params.z_entry else 2.0,
        )
        mean_rev_model = MeanReversionSignals(rev_config)
        regime_filter = mean_rev_scale_series.reindex(closes.index).ffill().fillna(
            regime_scale_d
        )
        signals = mean_rev_model.generate_signals(data, regime_filter=regime_filter)
        if not signals.empty:
            latest_date = signals.index[-1]
            latest = signals.loc[latest_date].copy()
            budget = (sleeves.D_intraday_rev.risk_budget or 0.15) * regime_scale_d
            total = latest.abs().sum()
            if total > 0 and budget > 0:
                latest = latest * (budget / total)
            else:
                latest = latest * 0
            sleeve_weights["D_intraday_rev"] = pd.DataFrame([latest], index=[latest_date])

    if not sleeve_weights:
        raise ValueError(
            "No sleeves enabled; ensure configuration enables at least one sleeve"
        )

    return sleeve_weights


def aggregate_target_weights(
    ctx: StrategyContext, sleeve_weights: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    closes = (
        ctx.daily["adj_close"].unstack("symbol")
        if "adj_close" in ctx.daily.columns
        else ctx.daily["close"].unstack("symbol")
    )
    returns = closes.pct_change(fill_method=None)
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")
    aligned = []
    for df in sleeve_weights.values():
        df = df.reindex(returns.index).ffill().fillna(0)
        aligned.append(df)
    target = sum(aligned)
    target = target.reindex(returns.index).fillna(0.0)
    target = scale_to_target(target, returns, ctx.settings.portfolio.target_vol_ann)
    cost_model = TransactionCostModel(ctx.settings.costs)
    if "volume" in ctx.daily.columns:
        volume = ctx.daily["volume"].unstack("symbol")
        dollar_volume = (
            closes.reindex(volume.index)
            .mul(volume, fill_value=0.0)
            .rolling(60, min_periods=20)
            .mean()
        )
        adv = dollar_volume.reindex(target.index).ffill().fillna(0.0)
    else:
        adv = pd.DataFrame(0.0, index=target.index, columns=target.columns)
    adjusted = target.copy()
    current = pd.Series(0.0, index=target.columns)
    for date in target.index:
        adv_row = adv.loc[date] if date in adv.index else pd.Series(0.0, index=target.columns)
        desired = target.loc[date]
        optimized = cost_model.optimize_rebalance_threshold(
            desired,
            current,
            adv_row,
            portfolio_value=1_000_000.0,
        )
        adjusted.loc[date] = optimized
        current = optimized
    return adjusted
