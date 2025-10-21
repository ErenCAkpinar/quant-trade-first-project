from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .metrics import sharpe_ratio, sortino_ratio, value_at_risk


class ReportBuilder:
    def __init__(
        self, equity: pd.Series, trades: pd.DataFrame, positions: pd.DataFrame
    ) -> None:
        self.equity = equity
        self.trades = trades
        self.positions = positions

    def build_summary(self) -> Dict[str, float]:
        equity = self.equity
        returns = equity.pct_change(fill_method=None).dropna()
        ann_factor = 252.0

        if equity.empty or len(equity) < 2:
            cagr = float("nan")
            max_dd = float("nan")
            calmar = float("nan")
        else:
            initial = float(equity.iloc[0])
            terminal = float(equity.iloc[-1])
            if initial <= 0 or terminal <= 0:
                cagr = float("nan")
            else:
                if pd.api.types.is_datetime64_any_dtype(equity.index):
                    day_span = max((equity.index[-1] - equity.index[0]).days, 1)
                    years = day_span / 365.25
                else:
                    years = max((len(equity) - 1) / ann_factor, 1e-9)
                cagr = (terminal / initial) ** (1 / years) - 1
            running_max = equity.cummax()
            drawdown = equity / running_max.replace(0, np.nan) - 1
            max_dd = float(drawdown.min()) if not drawdown.empty else float("nan")
            calmar = cagr / abs(max_dd) if max_dd < 0 else float("nan")

        sharpe = sharpe_ratio(returns) if not returns.empty else float("nan")
        sortino = sortino_ratio(returns) if not returns.empty else float("nan")
        var_95 = value_at_risk(returns, 0.95) if not returns.empty else float("nan")
        var_99 = value_at_risk(returns, 0.99) if not returns.empty else float("nan")

        if self.trades.empty or equity.empty:
            turnover = 0.0
        else:
            daily_notional = (
                self.trades.assign(notional=self.trades["notional"].abs())
                .groupby("date")["notional"]
                .sum()
            )
            equity_for_turnover = equity.reindex(daily_notional.index).ffill()
            turnover_series = daily_notional / equity_for_turnover.replace(0, np.nan)
            turnover = float(turnover_series.mean(skipna=True)) if not turnover_series.empty else 0.0

        return {
            "CAGR": cagr,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "MaxDD": max_dd,
            "Calmar": calmar,
            "VaR95": var_95,
            "VaR99": var_99,
            "Turnover": turnover,
        }

    def to_html(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=self.equity.index, y=self.equity.values, name="Equity")
        )
        summary = self.build_summary()
        metrics_table = go.Table(
            header=dict(values=list(summary.keys())),
            cells=dict(values=[list(summary.values())]),
        )
        fig2 = go.Figure(data=[metrics_table])
        equity_html = fig.to_html(full_html=False)
        summary_html = fig2.to_html(full_html=False)
        html = (
            "<h1>Equity Curve</h1>"
            f"{equity_html}"
            "<h2>Summary</h2>"
            f"{summary_html}"
        )
        path.write_text(html, encoding="utf-8")

    def trades_to_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.trades.to_csv(path, index=False)
