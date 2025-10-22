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
from ..data.news import NewsFetcher
from ..execution.broker_alpaca import AlpacaBroker, OrderTicket
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


def _positions_to_weights(
    positions: dict[str, float], prices: pd.Series, equity: float
) -> pd.Series:
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
    news_fetcher: NewsFetcher | None = None
    if getattr(settings.live, "news_enabled", False):
        try:
            news_fetcher = NewsFetcher(
                lookback_hours=settings.live.news_lookback_hours,
                company_headlines=settings.live.news_company_headlines,
                general_headlines=settings.live.news_general_headlines,
                refresh_minutes=settings.live.news_refresh_minutes,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Failed to initialise NewsFetcher: %s", exc)
            news_fetcher = None

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
        ctx = StrategyContext(
            settings=settings,
            provider=provider,
            meta=meta,
            daily=history,
            fundamentals=pd.DataFrame(),
        )
        sleeve_weights = compute_sleeve_weights(ctx)
        target = aggregate_target_weights(ctx, sleeve_weights)
        latest_target = target.iloc[-1].copy()
        prices = _current_prices(history)
        account_overview = broker.get_account_overview()
        cash_value = account_overview.get("cash")
        fallback_cash = getattr(settings.live, "paper_start_cash", 0.0)
        if cash_value is not None:
            cash = float(cash_value)
        else:
            cash = float(fallback_cash)
        position_status = broker.get_position_status()
        positions: dict[str, float] = {}
        for sym, info in position_status.items():
            qty_raw = info.get("qty", 0.0)
            qty_float = float(qty_raw) if qty_raw is not None else 0.0
            positions[sym] = qty_float
        equity = cash + sum(
            qty * prices.get(sym, 0.0) for sym, qty in positions.items()
        )
        current_weights = _positions_to_weights(
            positions, prices, max(equity, 1.0)
        ).copy()

        risk_orders: list[OrderTicket] = []
        risk_symbols: set[str] = set()
        stop_threshold = settings.live.stop_loss_plpc
        take_threshold = settings.live.take_profit_plpc
        for sym, info in position_status.items():
            qty = positions.get(sym, 0.0)
            plpc_raw = info.get("plpc")
            plpc = float(plpc_raw) if plpc_raw is not None else None
            if qty == 0 or plpc is None:
                continue
            trigger: str | None = None
            if stop_threshold is not None and plpc <= -abs(stop_threshold):
                trigger = "stop-loss"
            elif take_threshold is not None and plpc >= abs(take_threshold):
                trigger = "take-profit"
            if not trigger:
                continue
            side = "buy" if qty < 0 else "sell"
            risk_orders.append(
                OrderTicket(
                    symbol=sym,
                    qty=float(abs(qty)),
                    side=side,
                    type="market",
                )
            )
            risk_symbols.add(sym)
            if sym in latest_target.index:
                latest_target.loc[sym] = 0.0
            if sym in current_weights.index:
                current_weights.loc[sym] = 0.0
            logger.info(
                "%s triggered for %s (PL%% %.2f); queuing market exit",
                trigger,
                sym,
                plpc * 100.0,
            )

        if risk_orders:
            try:
                broker.cancel_open_orders()
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(
                    "Failed to cancel open orders prior to risk exits: %s", exc
                )

        slices = router.reconcile_positions(
            latest_target, current_weights, prices, equity
        )
        if risk_symbols:
            slices = [slc for slc in slices if slc.symbol not in risk_symbols]
        tickets = risk_orders + router.build_orders(slices, equity)
        if tickets:
            broker.submit_orders(tickets)
        else:
            logger.info("No orders to send this cycle")
        logger.info(
            "Account snapshot | cash: %.2f | buying power: %.2f | equity: %.2f",
            account_overview.get("cash", 0.0),
            account_overview.get("buying_power", 0.0),
            account_overview.get("equity", equity),
        )
        if news_fetcher:
            try:
                ranked = latest_target.abs().sort_values(ascending=False)
                top_symbols = [
                    symbol
                    for symbol, weight in ranked.items()
                    if weight > 0
                ][: settings.live.news_symbols]
                company_news = news_fetcher.get_company_headlines(top_symbols)
                for symbol, articles in company_news.items():
                    if not articles:
                        continue
                    headline = articles[0]
                    logger.info(
                        "News (%s): %s — %s",
                        symbol,
                        headline.headline,
                        headline.url,
                    )
                market_news = news_fetcher.get_market_headlines()
                if market_news:
                    headline = market_news[0]
                    logger.info(
                        "Market headline: %s — %s",
                        headline.headline,
                        headline.url,
                    )
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning("Failed to refresh news: %s", exc)
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
