from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from statsmodels.tsa.stattools import adfuller

from ..config.schema import Settings
from ..strategy import build_context

# Constants
TRADING_DAYS_PER_YEAR = 252
MAD_SCALE = 1.4826
PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close"]


@dataclass
class CheckResult:
    """Container for primary vs secondary metric comparisons."""

    primary: Any
    cross_check: Any
    tolerance: Optional[float]
    difference: Any
    passed: bool
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": _to_native(self.primary),
            "cross_check": _to_native(self.cross_check),
            "tolerance": self.tolerance,
            "difference": _to_native(self.difference),
            "passed": bool(self.passed),
            "note": self.note,
        }


def _to_native(value: Any) -> Any:
    if isinstance(value, (np.generic, np.bool_)):
        return _to_native(value.item())
    if isinstance(value, dict):
        return {k: _to_native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_native(v) for v in value]
    if isinstance(value, pd.Series):
        return _to_native(value.to_dict())
    if isinstance(value, pd.DataFrame):
        return _to_native(value.to_dict())
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


class MasterFormulaReport:
    """Generates a comprehensive analytics report with redundancy checks."""

    def __init__(
        self,
        settings: Settings,
        daily: pd.DataFrame,
        fundamentals: pd.DataFrame,
        trades: Optional[pd.DataFrame],
        risk_free_rate: float = 0.0,
    ) -> None:
        self.settings = settings
        self.raw_daily = daily
        self.fundamentals = fundamentals
        self.trades = trades
        self.risk_free_rate = risk_free_rate
        self.symbols = sorted({idx[1] for idx in daily.index})

        self._sanitized_daily: Optional[pd.DataFrame] = None
        self._returns: Optional[pd.DataFrame] = None
        self._log_returns: Optional[pd.DataFrame] = None
        self._equity: Optional[pd.DataFrame] = None

    @property
    def sanitized_daily(self) -> pd.DataFrame:
        if self._sanitized_daily is None:
            winsorized, _ = _winsorize_prices(self.raw_daily, PRICE_COLUMNS)
            sanitized, _ = _mad_clamp_prices(winsorized, PRICE_COLUMNS)
            self._sanitized_daily = sanitized.sort_index()
        return self._sanitized_daily

    @property
    def returns(self) -> pd.DataFrame:
        if self._returns is None:
            closes = self.sanitized_daily["adj_close"].unstack("symbol").sort_index()
            self._returns = closes.pct_change().dropna(how="all")
        return self._returns

    @property
    def log_returns(self) -> pd.DataFrame:
        if self._log_returns is None:
            closes = self.sanitized_daily["adj_close"].unstack("symbol").sort_index()
            self._log_returns = np.log(closes / closes.shift(1)).dropna(how="all")
        return self._log_returns

    @property
    def cumulative_equity(self) -> pd.DataFrame:
        if self._equity is None:
            eq = (1 + self.returns).cumprod()
            self._equity = eq
        return self._equity

    def run(self) -> Dict[str, Any]:
        logger.info(
            "Running master formula report for symbols: {}",
            ",".join(self.symbols),
        )
        report = {
            "metadata": {
                "risk_free_rate": self.risk_free_rate,
                "symbols": self.symbols,
                "period_start": self.sanitized_daily.index.get_level_values("date")
                .min()
                .isoformat(),
                "period_end": self.sanitized_daily.index.get_level_values("date")
                .max()
                .isoformat(),
                "observations": int(len(self.returns)),
            },
            "data_sanity": self._data_sanity_checks(),
            "returns_block": self._returns_block(),
            "volatility_risk": self._volatility_block(),
            "drawdown": self._drawdown_block(),
            "signals": self._signals_block(),
            "position_sizing": self._position_sizing_block(),
            "execution_costs": self._execution_block(),
            "risk_performance": self._risk_performance_block(),
            "pairs_mean_reversion": self._pairs_block(),
            "options_greeks": self._options_block(),
            "redundancy_checklist": self._redundancy_checklist(),
        }
        return report

    def _data_sanity_checks(self) -> Dict[str, Any]:
        winsorized, win_stats = _winsorize_prices(self.raw_daily, PRICE_COLUMNS)
        mad_clamped, mad_stats = _mad_clamp_prices(winsorized, PRICE_COLUMNS)
        before = self.raw_daily.groupby("symbol")["adj_close"].describe()["std"]
        after = mad_clamped.groupby("symbol")["adj_close"].describe()["std"]
        std_ratio = (after / before).replace({np.inf: np.nan})
        return {
            "winsorization_quantiles": _to_native(win_stats),
            "mad_bounds": _to_native(mad_stats),
            "stdev_ratio": _to_native(std_ratio.to_dict()),
        }

    def _returns_block(self) -> Dict[str, Any]:
        simple = self.returns
        log_ret = self.log_returns
        identity = {}
        cagr = {}
        log_cagr = {}
        for symbol in self.symbols:
            series = simple[symbol].dropna()
            log_series = log_ret[symbol].dropna()
            if series.empty or log_series.empty:
                identity[symbol] = CheckResult(
                    np.nan, np.nan, 1e-8, np.nan, False, "insufficient data"
                ).to_dict()
                cagr[symbol] = np.nan
                log_cagr[symbol] = np.nan
                continue
            cumulative_log = log_series.sum()
            cagr_primary = _cagr_from_returns(series)
            cagr_log = _cagr_from_log_returns(log_series)
            log_vs_price = abs(cumulative_log - math.log((1 + series).prod()))
            passed = bool(log_vs_price <= 1e-8)
            identity[symbol] = CheckResult(
                cumulative_log,
                math.log((1 + series).prod()),
                1e-8,
                log_vs_price,
                passed,
            ).to_dict()
            cagr[symbol] = cagr_primary
            log_cagr[symbol] = cagr_log
        return {
            "identity": identity,
            "cagr": _to_native(cagr),
            "cagr_log": _to_native(log_cagr),
        }

    def _volatility_block(self) -> Dict[str, Any]:
        sample = self.returns.std(ddof=1)
        population = self.returns.std(ddof=0)
        diff = (sample - population).abs()
        ewma = self.returns.ewm(alpha=1 - 0.94).std()
        latest_ewma = ewma.iloc[-1]
        rolling = self.returns.rolling(window=60, min_periods=20).std()
        latest_rolling = rolling.iloc[-1]
        compare = {}
        for symbol in self.symbols:
            ew = latest_ewma.get(symbol)
            ro = latest_rolling.get(symbol)
            if np.isnan(ew) or np.isnan(ro):
                compare[symbol] = CheckResult(
                    ew, ro, 0.15, np.nan, False, "insufficient data"
                ).to_dict()
            else:
                rel_diff = abs(ew - ro) / max(ro, 1e-9)
                compare[symbol] = CheckResult(
                    ew, ro, 0.15, rel_diff, rel_diff <= 0.15
                ).to_dict()
        return {
            "sample_vol": _to_native(sample.to_dict()),
            "population_vol": _to_native(population.to_dict()),
            "sample_vs_population_diff": _to_native(diff.to_dict()),
            "ewma_latest": _to_native(latest_ewma.to_dict()),
            "rolling_latest": _to_native(latest_rolling.to_dict()),
            "ewma_vs_rolling": compare,
        }

    def _drawdown_block(self) -> Dict[str, Any]:
        dd_primary = {}
        dd_log = {}
        for symbol in self.symbols:
            cumulative = self.cumulative_equity[symbol]
            if cumulative.dropna().empty:
                dd_primary[symbol] = np.nan
                dd_log[symbol] = np.nan
                continue
            dd_primary[symbol] = _max_drawdown(cumulative)
            log_curve = self.log_returns[symbol].cumsum().apply(np.exp)
            dd_log[symbol] = _max_drawdown(log_curve)
        compare = {}
        for symbol in self.symbols:
            p = dd_primary.get(symbol)
            log_value = dd_log.get(symbol)
            if np.isnan(p) or np.isnan(log_value):
                compare[symbol] = CheckResult(
                    p, log_value, 1e-3, np.nan, False, "insufficient data"
                ).to_dict()
            else:
                diff = abs(p - log_value)
                compare[symbol] = CheckResult(
                    p, log_value, 1e-3, diff, diff <= 1e-3
                ).to_dict()
        return {
            "max_drawdown_price": _to_native(dd_primary),
            "max_drawdown_log": _to_native(dd_log),
            "comparison": compare,
        }

    def _signals_block(self) -> Dict[str, Any]:
        momentum = {}
        slope = {}
        mean_rev = {}
        rsi_checks = {}
        bollinger_checks = {}
        atr_checks = {}

        closes = self.sanitized_daily["adj_close"].unstack("symbol").sort_index()
        highs = self.sanitized_daily["high"].unstack("symbol").sort_index()
        lows = self.sanitized_daily["low"].unstack("symbol").sort_index()
        closes_full = self.sanitized_daily["close"].unstack("symbol").sort_index()

        ema_fast = closes.ewm(span=12, adjust=False).mean()
        ema_slow = closes.ewm(span=26, adjust=False).mean()
        for symbol in self.symbols:
            price_series = closes[symbol]
            log_series = self.log_returns[symbol]
            mom_primary = _momentum_12_2(price_series)
            mom_log = _momentum_log_approx(log_series)
            if mom_primary.empty or mom_log.empty:
                momentum[symbol] = CheckResult(
                    np.nan, np.nan, None, np.nan, False, "insufficient history"
                ).to_dict()
            else:
                latest_p = mom_primary.iloc[-1]
                latest_l = mom_log.iloc[-1]
                sign_match = np.sign(latest_p) == np.sign(latest_l)
                momentum[symbol] = CheckResult(
                    latest_p, latest_l, None, latest_p - latest_l, bool(sign_match)
                ).to_dict()

            slope_primary = ema_fast[symbol] - ema_slow[symbol]
            slope_cross = _ema_difference(price_series, 10)
            if slope_primary.dropna().empty or slope_cross.dropna().empty:
                slope[symbol] = CheckResult(
                    np.nan, np.nan, None, np.nan, False, "insufficient history"
                ).to_dict()
            else:
                corr = slope_primary.corr(slope_cross)
                slope[symbol] = {
                    "correlation": corr,
                    "recent_primary": slope_primary.iloc[-1],
                    "recent_cross": slope_cross.iloc[-1],
                }

            returns = self.returns[symbol]
            z_primary = _zscore(returns, window=20)
            z_mad = _zscore_mad(returns, window=20)
            if z_primary.dropna().empty or z_mad.dropna().empty:
                mean_rev[symbol] = CheckResult(
                    np.nan, np.nan, None, np.nan, False, "insufficient history"
                ).to_dict()
            else:
                latest_primary = z_primary.iloc[-1]
                latest_mad = z_mad.iloc[-1]
                mean_rev[symbol] = CheckResult(
                    latest_primary, latest_mad, None, latest_primary - latest_mad, True
                ).to_dict()

            rsi_wilder = _rsi_wilder(price_series, period=14)
            rsi_sma = _rsi_sma(price_series, period=14)
            if rsi_wilder.dropna().empty or rsi_sma.dropna().empty:
                rsi_checks[symbol] = CheckResult(
                    np.nan, np.nan, None, np.nan, False, "insufficient history"
                ).to_dict()
            else:
                rmse = math.sqrt(np.nanmean((rsi_wilder - rsi_sma) ** 2))
                rsi_checks[symbol] = CheckResult(
                    rsi_wilder.iloc[-1], rsi_sma.iloc[-1], None, rmse, True
                ).to_dict()

            boll_sma = _bollinger(price_series, window=20, method="sma")
            boll_ema = _bollinger(price_series, window=20, method="ema")
            if boll_sma["upper"].dropna().empty or boll_ema["upper"].dropna().empty:
                bollinger_checks[symbol] = {"note": "insufficient history"}
            else:
                diff_upper = abs(
                    boll_sma["upper"].iloc[-1] - boll_ema["upper"].iloc[-1]
                )
                diff_lower = abs(
                    boll_sma["lower"].iloc[-1] - boll_ema["lower"].iloc[-1]
                )
                bollinger_checks[symbol] = {
                    "upper_diff": diff_upper,
                    "lower_diff": diff_lower,
                }

            atr_wilder = _atr(
                highs[symbol],
                lows[symbol],
                closes_full[symbol],
                period=14,
                method="wilder",
            )
            atr_sma = _atr(
                highs[symbol],
                lows[symbol],
                closes_full[symbol],
                period=14,
                method="sma",
            )
            if atr_wilder.dropna().empty or atr_sma.dropna().empty:
                atr_checks[symbol] = CheckResult(
                    np.nan, np.nan, None, np.nan, False, "insufficient history"
                ).to_dict()
            else:
                diff = abs(atr_wilder.iloc[-1] - atr_sma.iloc[-1])
                atr_checks[symbol] = CheckResult(
                    atr_wilder.iloc[-1], atr_sma.iloc[-1], None, diff, True
                ).to_dict()

        return {
            "momentum": momentum,
            "macd_vs_ema_diff": slope,
            "zscore_vs_mad": mean_rev,
            "rsi": rsi_checks,
            "bollinger": bollinger_checks,
            "atr": atr_checks,
        }

    def _position_sizing_block(self) -> Dict[str, Any]:
        target_vol_ann = self.settings.portfolio.target_vol_ann
        target_daily = target_vol_ann / math.sqrt(TRADING_DAYS_PER_YEAR)
        latest_vol = self.returns.rolling(window=20, min_periods=10).std().iloc[-1]
        leverage = {}
        for symbol in self.symbols:
            vol = latest_vol.get(symbol, np.nan)
            if np.isnan(vol) or vol == 0:
                leverage[symbol] = np.nan
            else:
                leverage[symbol] = min(3.0, target_daily / vol)

        sigma = self.returns.cov()
        inv_vol = 1 / np.sqrt(np.diag(sigma))
        inv_vol_weights = inv_vol / inv_vol.sum()
        inverse_vol_dict = {
            symbol: float(inv_vol_weights[idx])
            for idx, symbol in enumerate(self.symbols)
        }
        erc_weights, erc_contrib = _equal_risk_contribution(sigma)

        mean_returns = self.returns.mean()
        vol_returns = self.returns.std()
        plain_kelly = {}
        exec_kelly = {}
        live_fraction = {}
        for symbol in self.symbols:
            mu = mean_returns.get(symbol, np.nan)
            sigma_r = vol_returns.get(symbol, np.nan)
            if np.isnan(mu) or np.isnan(sigma_r) or sigma_r == 0:
                plain_kelly[symbol] = np.nan
                exec_kelly[symbol] = np.nan
                live_fraction[symbol] = False
                continue
            k_plain = mu / (sigma_r**2)
            k_exec, live_ok = _execution_aware_kelly(
                mu,
                sigma_r,
                symbol,
                self.trades,
                self.sanitized_daily,
                impact_k=self.settings.costs.impact_k,
                spread_bps=self.settings.costs.spread_bps,
            )
            plain_kelly[symbol] = k_plain
            exec_kelly[symbol] = k_exec
            live_fraction[symbol] = live_ok and (k_exec <= k_plain)

        return {
            "vol_target_leverage": _to_native(leverage),
            "risk_parity_inverse_vol": _to_native(inverse_vol_dict),
            "risk_parity_erc_weights": _to_native(erc_weights),
            "risk_parity_erc_contrib": _to_native(erc_contrib),
            "plain_kelly": _to_native(plain_kelly),
            "execution_aware_kelly": _to_native(exec_kelly),
            "kelly_sanity": _to_native(live_fraction),
        }

    def _execution_block(self) -> Dict[str, Any]:
        if self.trades is None or self.trades.empty:
            return {"note": "no trades available"}
        trades = self.trades.copy()
        trades["abs_notional"] = trades["notional"].abs()
        trades["abs_quantity"] = trades["quantity"].abs()
        trades["date"] = pd.to_datetime(trades["date"])

        price_data = self.sanitized_daily.reset_index().set_index(["date", "symbol"])
        vwap = {}
        twap = {}
        slippage = {}
        impact_guard = {}

        for symbol in self.symbols:
            sym_trades = trades[trades["symbol"] == symbol]
            if sym_trades.empty:
                continue
            daily_data = price_data.xs(symbol, level="symbol")
            adv = daily_data["volume"].rolling(window=20, min_periods=5).mean().iloc[-1]
            vwap_vals = []
            twap_vals = []
            slippage_vals = []
            guard_vals = []
            for _, trade in sym_trades.iterrows():
                day = trade["date"]
                if day not in daily_data.index:
                    continue
                row = daily_data.loc[day]
                day_vwap = row["close"] if row["volume"] == 0 else row["close"]
                vwap_vals.append(day_vwap)
                day_twap = (row["high"] + row["low"] + row["close"] + row["open"]) / 4
                twap_vals.append(day_twap)
                slippage_vals.append(trade["price"] - day_vwap)
                if adv and adv > 0:
                    guard_vals.append(
                        self.settings.costs.impact_k
                        * math.sqrt(trade["abs_quantity"] / adv)
                    )
            if vwap_vals:
                trade_vwap = np.average(vwap_vals, weights=sym_trades["abs_quantity"])
                trade_twap = np.average(twap_vals, weights=sym_trades["abs_quantity"])
                vwap[symbol] = trade_vwap
                twap[symbol] = trade_twap
                slippage[symbol] = float(np.mean(slippage_vals))
                impact_guard[symbol] = float(
                    np.max(guard_vals) if guard_vals else np.nan
                )
        return {
            "average_vwap": vwap,
            "average_twap": twap,
            "average_slippage": slippage,
            "impact_guardrail": impact_guard,
        }

    def _risk_performance_block(self) -> Dict[str, Any]:
        mean_returns = self.returns.mean()
        excess_mean = mean_returns - self.risk_free_rate / TRADING_DAYS_PER_YEAR
        vol = self.returns.std()
        sharpe = excess_mean / vol.replace(0, np.nan)
        downside = self.returns.clip(upper=0).std()
        sortino = excess_mean / downside.replace(0, np.nan)
        t_stat = excess_mean / (self.returns.std(ddof=1) / math.sqrt(len(self.returns)))

        eq_curve = self.cumulative_equity.mean(axis=1)
        mdd = _max_drawdown(eq_curve)
        cagr = _cagr_from_equity(eq_curve)
        calmar = cagr / mdd if mdd not in (0, np.nan) else np.nan

        benchmark = (
            self.cumulative_equity.iloc[:, 0]
            if self.cumulative_equity.shape[1] > 0
            else None
        )
        info_ratio = {}
        if benchmark is not None:
            bench_returns = benchmark.pct_change().dropna()
            for symbol in self.symbols:
                asset_ret = self.returns[symbol].dropna()
                if asset_ret.empty or bench_returns.empty:
                    info_ratio[symbol] = np.nan
                    continue
                active = asset_ret.align(bench_returns, join="inner")[0] - bench_returns
                tracking_error = active.std()
                info_ratio[symbol] = (
                    active.mean() / tracking_error if tracking_error != 0 else np.nan
                )

        var95 = self.returns.quantile(0.05)
        var99 = self.returns.quantile(0.01)
        return {
            "sharpe": _to_native(sharpe.to_dict()),
            "sortino": _to_native(sortino.to_dict()),
            "t_stat": _to_native(t_stat.to_dict()),
            "mdd": mdd,
            "cagr": cagr,
            "calmar": calmar,
            "information_ratio": _to_native(info_ratio),
            "var_95": _to_native(var95.to_dict()),
            "var_99": _to_native(var99.to_dict()),
        }

    def _pairs_block(self) -> Dict[str, Any]:
        if len(self.symbols) < 2:
            return {"note": "need at least two symbols"}
        sym_a, sym_b = self.symbols[:2]
        prices_a = self.sanitized_daily["adj_close"].xs(sym_a, level="symbol")
        prices_b = self.sanitized_daily["adj_close"].xs(sym_b, level="symbol")
        hedge = _ols_hedge_ratio(prices_a, prices_b)
        residuals = prices_a - hedge * prices_b
        adf_stat, pvalue = _adf_test(residuals)
        z = (residuals - residuals.mean()) / residuals.std(ddof=1)
        rolling = z.rolling(window=20, min_periods=10).mean()
        return {
            "symbols": [sym_a, sym_b],
            "hedge_ratio": hedge,
            "adf_stat": adf_stat,
            "adf_pvalue": pvalue,
            "latest_zscore": z.iloc[-1] if not z.dropna().empty else np.nan,
            "rolling_mean_zscore": (
                rolling.iloc[-1] if not rolling.dropna().empty else np.nan
            ),
        }

    def _options_block(self) -> Dict[str, Any]:
        if not self.symbols:
            return {"note": "no symbols available"}
        symbol = self.symbols[0]
        spot = self.sanitized_daily["adj_close"].xs(symbol, level="symbol").iloc[-1]
        strike = spot * 1.05
        sigma = self.returns[symbol].std() * math.sqrt(TRADING_DAYS_PER_YEAR)
        maturity = 30 / 365
        call, put, parity_diff, greeks = _black_scholes_summary(
            spot,
            strike,
            sigma,
            maturity,
            risk_free=self.risk_free_rate,
        )
        return {
            "symbol": symbol,
            "spot": spot,
            "strike": strike,
            "volatility": sigma,
            "maturity_years": maturity,
            "call_price": call,
            "put_price": put,
            "parity_gap": parity_diff,
            "greeks": greeks,
        }

    def _redundancy_checklist(self) -> Dict[str, Any]:
        entries = {}
        # 1. Return identity
        log_sum = self.log_returns.sum()
        price_log = np.log((1 + self.returns).prod())
        entries["return_identity"] = _to_native((log_sum - price_log).abs().to_dict())
        # 2. Annualization consistency (EWMA vs rolling)
        ewma = self.returns.ewm(alpha=1 - 0.94).std().iloc[-1] * math.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        rolling = self.returns.rolling(window=60, min_periods=20).std().iloc[
            -1
        ] * math.sqrt(TRADING_DAYS_PER_YEAR)
        entries["annualization_consistency"] = _to_native((ewma / rolling).to_dict())
        # 3. Momentum parity sign agreement ratio
        ratio = {}
        closes = self.sanitized_daily["adj_close"].unstack("symbol").sort_index()
        for symbol in self.symbols:
            mom_primary = _momentum_12_2(closes[symbol])
            mom_alt = _ema_difference(closes[symbol], 10)
            joined = pd.concat([mom_primary, mom_alt], axis=1).dropna()
            if joined.empty:
                ratio[symbol] = np.nan
            else:
                signs = np.sign(joined.iloc[:, 0]) == np.sign(joined.iloc[:, 1])
                ratio[symbol] = float(signs.mean())
        entries["momentum_sign_match"] = ratio
        # 4. RSI smoothing RMSE (already computed but aggregate)
        rsi_rmse = {}
        for symbol in self.symbols:
            price_series = closes[symbol]
            wilder = _rsi_wilder(price_series, 14)
            sma = _rsi_sma(price_series, 14)
            joined = pd.concat([wilder, sma], axis=1).dropna()
            if joined.empty:
                rsi_rmse[symbol] = np.nan
            else:
                rsi_rmse[symbol] = float(
                    np.sqrt(np.mean((joined.iloc[:, 0] - joined.iloc[:, 1]) ** 2))
                )
        entries["rsi_rmse"] = rsi_rmse
        # 5. ATR variant difference
        atr_gap = {}
        highs = self.sanitized_daily["high"].unstack("symbol").sort_index()
        lows = self.sanitized_daily["low"].unstack("symbol").sort_index()
        closes_full = self.sanitized_daily["close"].unstack("symbol").sort_index()
        for symbol in self.symbols:
            atr_w = _atr(highs[symbol], lows[symbol], closes_full[symbol], 14, "wilder")
            atr_s = _atr(highs[symbol], lows[symbol], closes_full[symbol], 14, "sma")
            joined = pd.concat([atr_w, atr_s], axis=1).dropna()
            if joined.empty:
                atr_gap[symbol] = np.nan
            else:
                atr_gap[symbol] = float(abs(joined.iloc[-1, 0] - joined.iloc[-1, 1]))
        entries["atr_gap"] = atr_gap
        # 6. Risk parity contributions within tolerance
        sigma = self.returns.cov()
        _, contrib = _equal_risk_contribution(sigma)
        if contrib:
            avg = np.mean(list(contrib.values()))
            entries["risk_parity_deviation"] = {
                k: abs(v - avg) / avg for k, v in contrib.items() if avg
            }
        else:
            entries["risk_parity_deviation"] = {}
        # 7. Kelly sanity
        mean_returns = self.returns.mean()
        vol_returns = self.returns.std()
        kelly_exec = {}
        for symbol in self.symbols:
            _, ok = _execution_aware_kelly(
                mean_returns.get(symbol, np.nan),
                vol_returns.get(symbol, np.nan),
                symbol,
                self.trades,
                self.sanitized_daily,
                impact_k=self.settings.costs.impact_k,
                spread_bps=self.settings.costs.spread_bps,
            )
            kelly_exec[symbol] = bool(ok)
        entries["kelly_fraction_ok"] = kelly_exec
        # 8. Impact model vs slippage
        if self.trades is not None and not self.trades.empty:
            impact_ok = {}
            trades = self.trades.copy()
            trades["abs_notional"] = trades["notional"].abs()
            trades["abs_quantity"] = trades["quantity"].abs()
            trades["date"] = pd.to_datetime(trades["date"])
            price_data = self.sanitized_daily.reset_index().set_index(
                ["date", "symbol"]
            )
            for symbol in self.symbols:
                sym_trades = trades[trades["symbol"] == symbol]
                if sym_trades.empty:
                    continue
                daily = price_data.xs(symbol, level="symbol")
                adv = daily["volume"].rolling(window=20, min_periods=5).mean().iloc[-1]
                if not adv or np.isnan(adv) or adv == 0:
                    continue
                slippages = []
                impacts = []
                for _, trade in sym_trades.iterrows():
                    day = trade["date"]
                    if day not in daily.index:
                        continue
                    row = daily.loc[day]
                    ref_price = row["close"]
                    slippages.append(abs(trade["price"] - ref_price))
                    impacts.append(
                        self.settings.costs.impact_k
                        * math.sqrt(trade["abs_quantity"] / adv)
                    )
                if slippages:
                    impact_ok[symbol] = max(slippages) <= max(impacts) * 1.1
            entries["impact_vs_slippage"] = impact_ok
        else:
            entries["impact_vs_slippage"] = {}
        # 9. Sharpe vs t-stat
        sharpe = (
            self.returns.mean() - self.risk_free_rate / TRADING_DAYS_PER_YEAR
        ) / self.returns.std()
        t_stat = (self.returns.mean() - self.risk_free_rate / TRADING_DAYS_PER_YEAR) / (
            self.returns.std(ddof=1) / math.sqrt(len(self.returns))
        )
        entries["sharpe_vs_tstat"] = _to_native(
            (t_stat - sharpe * math.sqrt(len(self.returns))).abs().to_dict()
        )
        # 10. Put-call parity gap (already computed) -- reuse options block
        options = self._options_block()
        entries["put_call_parity_gap"] = options.get("parity_gap")
        return entries


def _winsorize_prices(
    df: pd.DataFrame,
    columns: Iterable[str],
    lower: float = 0.001,
    upper: float = 0.999,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    clipped = df.copy()
    stats: Dict[str, Dict[str, float]] = {}
    for symbol, group in df.groupby(level="symbol"):
        symbol_stats: Dict[str, float] = {}
        for column in columns:
            series = group[column]
            lower_q = series.quantile(lower)
            upper_q = series.quantile(upper)
            clipped.loc[(slice(None), symbol), column] = series.clip(
                lower_q, upper_q
            ).values
            symbol_stats[f"{column}_lower"] = float(lower_q)
            symbol_stats[f"{column}_upper"] = float(upper_q)
        stats[symbol] = symbol_stats
    return clipped, stats


def _mad_clamp_prices(
    df: pd.DataFrame,
    columns: Iterable[str],
    threshold: float = 3.5,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    clamped = df.copy()
    stats: Dict[str, Dict[str, float]] = {}
    for symbol, group in df.groupby(level="symbol"):
        symbol_stats: Dict[str, float] = {}
        for column in columns:
            series = group[column]
            median = series.median()
            mad = np.median(np.abs(series - median))
            scale = MAD_SCALE * mad
            if scale == 0:
                lower = median - threshold
                upper = median + threshold
            else:
                lower = median - threshold * scale
                upper = median + threshold * scale
            clamped.loc[(slice(None), symbol), column] = series.clip(
                lower, upper
            ).values
            symbol_stats[f"{column}_lower"] = float(lower)
            symbol_stats[f"{column}_upper"] = float(upper)
        stats[symbol] = symbol_stats
    return clamped, stats


def _cagr_from_returns(returns: pd.Series) -> float:
    if returns.empty:
        return np.nan
    cumulative = (1 + returns).prod()
    periods = len(returns)
    if cumulative <= 0 or periods == 0:
        return np.nan
    years = periods / TRADING_DAYS_PER_YEAR
    return cumulative ** (1 / years) - 1 if years > 0 else np.nan


def _cagr_from_log_returns(log_returns: pd.Series) -> float:
    if log_returns.empty:
        return np.nan
    cumulative_log = log_returns.sum()
    years = len(log_returns) / TRADING_DAYS_PER_YEAR
    return math.exp(cumulative_log / years) - 1 if years > 0 else np.nan


def _cagr_from_equity(equity: pd.Series) -> float:
    if equity.dropna().empty:
        return np.nan
    start = equity.dropna().iloc[0]
    end = equity.dropna().iloc[-1]
    periods = len(equity.dropna())
    if start <= 0 or periods == 0:
        return np.nan
    years = periods / TRADING_DAYS_PER_YEAR
    return (end / start) ** (1 / years) - 1 if years > 0 else np.nan


def _max_drawdown(series: pd.Series) -> float:
    if series.dropna().empty:
        return np.nan
    running_max = series.cummax()
    drawdown = (running_max - series) / running_max.replace(0, np.nan)
    return drawdown.max()


def _momentum_12_2(prices: pd.Series) -> pd.Series:
    if prices.dropna().empty:
        return pd.Series(dtype=float)
    price = prices.dropna()
    return ((price.shift(1) / price.shift(252)) - 1) - (
        (price.shift(1) / price.shift(21)) - 1
    )


def _momentum_log_approx(log_returns: pd.Series) -> pd.Series:
    if log_returns.dropna().empty:
        return pd.Series(dtype=float)
    return log_returns.rolling(window=252, min_periods=60).sum()


def _ema_difference(prices: pd.Series, window: int) -> pd.Series:
    if prices.dropna().empty:
        return pd.Series(dtype=float)
    fast = prices.ewm(span=window, adjust=False).mean()
    slow = prices.ewm(span=window * 2, adjust=False).mean()
    return fast - slow


def _zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window=window, min_periods=window // 2).mean()
    std = series.rolling(window=window, min_periods=window // 2).std()
    return (series - mean) / std


def _zscore_mad(series: pd.Series, window: int) -> pd.Series:
    rolling_median = series.rolling(window=window, min_periods=window // 2).median()
    rolling_mad = series.rolling(window=window, min_periods=window // 2).apply(
        lambda x: np.median(np.abs(x - np.median(x))), raw=False
    )
    scale = rolling_mad * MAD_SCALE
    return (series - rolling_median) / scale.replace(0, np.nan)


def _rsi_wilder(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _rsi_sma(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period // 2).mean()
    avg_loss = loss.rolling(window=period, min_periods=period // 2).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _bollinger(
    prices: pd.Series, window: int, method: str = "sma"
) -> Dict[str, pd.Series]:
    if method == "ema":
        mid = prices.ewm(span=window, adjust=False).mean()
        std = prices.ewm(span=window, adjust=False).std()
    else:
        mid = prices.rolling(window=window, min_periods=window // 2).mean()
        std = prices.rolling(window=window, min_periods=window // 2).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return {"mid": mid, "upper": upper, "lower": lower}


def _atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int,
    method: str = "wilder",
) -> pd.Series:
    high_low = high - low
    high_close = (high - close.shift(1)).abs()
    low_close = (low - close.shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    if method == "sma":
        return tr.rolling(window=period, min_periods=period // 2).mean()
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _equal_risk_contribution(
    covariance: pd.DataFrame,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    if covariance.empty:
        return {}, {}
    symbols = covariance.columns.tolist()
    cov = covariance.values
    n = len(symbols)
    if n == 0:
        return {}, {}
    weights = np.ones(n) / n
    for _ in range(100):
        contributions = weights * (cov @ weights)
        mean_contrib = contributions.mean()
        if mean_contrib == 0:
            break
        adjustment = mean_contrib / contributions
        weights *= adjustment
        weights /= weights.sum()
    contributions = weights * (cov @ weights)
    weight_dict = {
        symbol: float(weights[idx]) for idx, symbol in enumerate(symbols)
    }
    contrib_dict = {
        symbol: float(contributions[idx]) for idx, symbol in enumerate(symbols)
    }
    return weight_dict, contrib_dict


def _execution_aware_kelly(
    mu: float,
    sigma: float,
    symbol: str,
    trades: Optional[pd.DataFrame],
    daily: pd.DataFrame,
    impact_k: float,
    spread_bps: float,
) -> Tuple[float, bool]:
    if trades is None or trades.empty or np.isnan(mu) or np.isnan(sigma) or sigma == 0:
        return np.nan, False
    sym_trades = trades[trades["symbol"] == symbol]
    if sym_trades.empty:
        return np.nan, False
    abs_notional = sym_trades["notional"].abs().sum()
    gross = sym_trades["notional"].sum()
    turnover = abs_notional / max(abs(gross), 1e-6)
    price_data = daily.xs(symbol, level="symbol")
    adv = price_data["volume"].rolling(window=20, min_periods=5).mean().iloc[-1]
    avg_qty = sym_trades["quantity"].abs().mean()
    if not adv or adv == 0:
        return np.nan, False
    impact = impact_k * math.sqrt(avg_qty / adv)
    cost = (spread_bps / 10000) * turnover
    denom = sigma**2
    if denom == 0:
        return np.nan, False
    plain = mu / denom
    kelly_exec = (mu - impact - cost) / denom
    if np.isnan(kelly_exec) or np.isnan(plain):
        return np.nan, False
    if plain > 0:
        live_ok = 0 <= kelly_exec <= 0.5 * plain
    else:
        live_ok = 0 >= kelly_exec >= 0.5 * plain
    return kelly_exec, live_ok


def _ols_hedge_ratio(series_a: pd.Series, series_b: pd.Series) -> float:
    aligned = pd.concat([series_a, series_b], axis=1).dropna()
    if aligned.empty:
        return np.nan
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1]
    var = np.var(aligned.iloc[:, 1])
    return float(cov / var) if var != 0 else np.nan


def _adf_test(series: pd.Series) -> Tuple[float, float]:
    series = series.dropna()
    if len(series) < 20:
        return np.nan, np.nan
    result = adfuller(series, maxlag=1, autolag="AIC")
    return float(result[0]), float(result[1])


def _black_scholes_summary(
    spot: float,
    strike: float,
    sigma: float,
    maturity: float,
    risk_free: float,
) -> Tuple[float, float, float, Dict[str, float]]:
    if sigma <= 0 or maturity <= 0 or spot <= 0 or strike <= 0:
        return np.nan, np.nan, np.nan, {}
    d1 = (math.log(spot / strike) + (risk_free + 0.5 * sigma**2) * maturity) / (
        sigma * math.sqrt(maturity)
    )
    d2 = d1 - sigma * math.sqrt(maturity)
    call = spot * _norm_cdf(d1) - strike * math.exp(-risk_free * maturity) * _norm_cdf(
        d2
    )
    put = strike * math.exp(-risk_free * maturity) * _norm_cdf(-d2) - spot * _norm_cdf(
        -d1
    )
    parity_gap = (call - put) - (spot - strike * math.exp(-risk_free * maturity))
    greeks = {
        "delta_call": _norm_cdf(d1),
        "delta_put": _norm_cdf(d1) - 1,
        "gamma": _norm_pdf(d1) / (spot * sigma * math.sqrt(maturity)),
        "vega": spot * _norm_pdf(d1) * math.sqrt(maturity),
        "theta_call": -spot * _norm_pdf(d1) * sigma / (2 * math.sqrt(maturity))
        - risk_free * strike * math.exp(-risk_free * maturity) * _norm_cdf(d2),
        "theta_put": -spot * _norm_pdf(d1) * sigma / (2 * math.sqrt(maturity))
        + risk_free * strike * math.exp(-risk_free * maturity) * _norm_cdf(-d2),
        "rho_call": strike * maturity * math.exp(-risk_free * maturity) * _norm_cdf(d2),
        "rho_put": -strike
        * maturity
        * math.exp(-risk_free * maturity)
        * _norm_cdf(-d2),
    }
    greeks = {k: float(v) for k, v in greeks.items()}
    return float(call), float(put), float(parity_gap), greeks


def _norm_pdf(x: float) -> float:
    return 1 / math.sqrt(2 * math.pi) * math.exp(-0.5 * x**2)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def generate_master_report(
    config_path: str,
    output_path: Optional[str] = None,
    trades_path: Optional[str] = None,
    risk_free_rate: float = 0.0,
) -> Dict[str, Any]:
    ctx = build_context(config_path)
    settings = ctx.settings
    trades_df = None
    if trades_path:
        trades_file = Path(trades_path)
    else:
        trades_file = Path(settings.reports.trades_csv)
    if trades_file.exists():
        trades_df = pd.read_csv(trades_file)
    report = MasterFormulaReport(
        settings=settings,
        daily=ctx.daily,
        fundamentals=ctx.fundamentals,
        trades=trades_df,
        risk_free_rate=risk_free_rate,
    ).run()
    native_report = _to_native(report)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(native_report, fp, indent=2, allow_nan=False)
        logger.info("Master report saved to {}", output_path)
    return native_report


__all__ = ["generate_master_report", "MasterFormulaReport"]


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate master formula analytics report"
    )
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output", required=False, help="Optional output JSON path")
    parser.add_argument("--trades", required=False, help="Optional trades CSV override")
    parser.add_argument(
        "--risk-free",
        type=float,
        default=0.0,
        help="Annual risk-free rate in decimal form",
    )
    args = parser.parse_args()

    report = generate_master_report(
        config_path=args.config,
        output_path=args.output,
        trades_path=args.trades,
        risk_free_rate=args.risk_free,
    )
    if not args.output:
        print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    _main()
