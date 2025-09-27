from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd
import plotly.graph_objects as go

from .metrics import calmar_ratio, max_drawdown, sharpe_ratio, sortino_ratio, value_at_risk


class ReportBuilder:
    def __init__(self, equity: pd.Series, trades: pd.DataFrame, positions: pd.DataFrame) -> None:
        self.equity = equity
        self.trades = trades
        self.positions = positions

    def build_summary(self) -> Dict[str, float]:
        returns = self.equity.pct_change().dropna()
        return {
            "CAGR": (self.equity.iloc[-1] / self.equity.iloc[0]) ** (252 / len(self.equity)) - 1,
            "Sharpe": sharpe_ratio(returns),
            "Sortino": sortino_ratio(returns),
            "MaxDD": max_drawdown(self.equity),
            "Calmar": calmar_ratio(self.equity),
            "VaR95": value_at_risk(returns, 0.95),
            "VaR99": value_at_risk(returns, 0.99),
            "Turnover": self.trades["notional"].abs().sum() / self.equity.iloc[-1],
        }

    def to_html(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.equity.index, y=self.equity.values, name="Equity"))
        summary = self.build_summary()
        metrics_table = go.Table(
            header=dict(values=list(summary.keys())),
            cells=dict(values=[list(summary.values())]),
        )
        fig2 = go.Figure(data=[metrics_table])
        html = f"<h1>Equity Curve</h1>{fig.to_html(full_html=False)}<h2>Summary</h2>{fig2.to_html(full_html=False)}"
        path.write_text(html, encoding="utf-8")

    def trades_to_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.trades.to_csv(path, index=False)
