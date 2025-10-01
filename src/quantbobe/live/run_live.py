from __future__ import annotations

import signal
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from loguru import logger

from ..config.loader import load_settings
from ..data import build_provider
from ..data.base import SymbolMeta
from ..execution.broker_alpaca import AlpacaBroker
from ..execution.router import ExecutionRouter
from ..execution.slippage import SlippageModel
from ..strategy import StrategyContext, aggregate_target_weights, compute_sleeve_weights


def _latest_history(provider, symbols, days: int = 252):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days * 2)
    return provider.get_daily_bars(symbols, start, end)


def _current_prices(history: pd.DataFrame) -> pd.Series:
    closes = history["close"].unstack("symbol")
    return closes.iloc[-1]


def _positions_to_weights(positions: dict[str, float], prices: pd.Series, equity: float) -> pd.Series:
    weights = {}
    for symbol, qty in positions.items():
        price = prices.get(symbol)
        if price is None:
            continue
        weights[symbol] = qty * price / max(equity, 1e-6)
    return pd.Series(weights)


def run_live(config_path: str) -> None:
    settings = load_settings(config_path)
    provider = build_provider(settings)
    meta: list[SymbolMeta] = provider.get_symbol_meta()
    symbols = [m.symbol for m in meta]

    broker = AlpacaBroker(settings.alpaca)
    slippage = SlippageModel(settings.costs.spread_bps, settings.costs.impact_k)
    router = ExecutionRouter(slippage)

    running = True

    def handle_sigint(sig, frame):  # type: ignore[unused-ignore]
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_sigint)

    reports_path = Path(settings.reports.html).parent
    reports_path.mkdir(parents=True, exist_ok=True)
    pnl_file = reports_path / "live_pnl.csv"

    logger.info("Starting live paper trading loop...")
    while running:
        history = _latest_history(provider, symbols)
        if history.empty:
            logger.warning("No history fetched; retrying")
            time.sleep(settings.live.poll_interval_sec)
            continue
        ctx = StrategyContext(settings=settings, provider=provider, meta=meta, daily=history, fundamentals=pd.DataFrame())
        sleeve_weights = compute_sleeve_weights(ctx)
        target = aggregate_target_weights(ctx, sleeve_weights)
        latest_target = target.iloc[-1]
        prices = _current_prices(history)
        cash = broker.get_cash() or settings.live.paper_start_cash
        positions = broker.get_positions()
        equity = cash + sum(qty * prices.get(sym, 0.0) for sym, qty in positions.items())
        current_weights = _positions_to_weights(positions, prices, max(equity, 1.0))
        slices = router.reconcile_positions(latest_target, current_weights, prices, equity)
        tickets = router.build_orders(slices, equity)
        if tickets:
            broker.submit_orders(tickets)
        else:
            logger.info("No orders to send this cycle")
        pnl_row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "equity": equity,
            "cash": cash,
        }
        if pnl_file.exists():
            existing = pd.read_csv(pnl_file)
            existing = pd.concat([existing, pd.DataFrame([pnl_row])], ignore_index=True)
            existing.to_csv(pnl_file, index=False)
        else:
            pd.DataFrame([pnl_row]).to_csv(pnl_file, index=False)
        time.sleep(settings.live.poll_interval_sec)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run live Alpaca paper trading loop")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    args = parser.parse_args()
    run_live(args.config)
