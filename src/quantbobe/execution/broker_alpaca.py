from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from dotenv import load_dotenv
from loguru import logger

try:
    import alpaca_trade_api as tradeapi
except Exception:  # pragma: no cover - optional dependency import
    tradeapi = None


@dataclass
class OrderTicket:
    symbol: str
    qty: float
    side: str
    type: str = "market"
    limit_price: Optional[float] = None


class AlpacaBroker:
    """Lightweight Alpaca paper broker wrapper."""

    def __init__(self) -> None:
        load_dotenv()
        self._api_key = os.getenv("ALPACA_API_KEY_ID")
        self._api_secret = os.getenv("ALPACA_API_SECRET_KEY")
        self._base_url = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")
        if not all([self._api_key, self._api_secret]):
            logger.warning("Alpaca credentials missing; broker will run in dry mode.")
        self._client = None

    def _ensure_client(self) -> Optional[tradeapi.REST]:
        if tradeapi is None:
            return None
        if self._client is None and self._api_key and self._api_secret:
            self._client = tradeapi.REST(self._api_key, self._api_secret, base_url=self._base_url)
        return self._client

    def get_cash(self) -> float:
        client = self._ensure_client()
        if client is None:
            return 0.0
        account = client.get_account()
        return float(account.cash)

    def get_positions(self) -> Dict[str, float]:
        client = self._ensure_client()
        if client is None:
            return {}
        positions = {}
        for position in client.list_positions():
            positions[position.symbol] = float(position.qty)
        return positions

    def cancel_open_orders(self) -> None:
        client = self._ensure_client()
        if client is None:
            return
        client.cancel_all_orders()

    def submit_orders(self, tickets: Iterable[OrderTicket]) -> None:
        client = self._ensure_client()
        if client is None:
            logger.info("Dry-run orders: {}", list(tickets))
            return
        for order in tickets:
            qty = abs(order.qty)
            if qty < 1e-4:
                continue
            participation = min(abs(order.qty) / 1_000_000, 1.0)
            if participation > 0.05:
                logger.warning("Participation {} too high for {}", participation, order.symbol)
                continue
            client.submit_order(
                symbol=order.symbol,
                qty=qty,
                side=order.side,
                type=order.type,
                time_in_force="day",
                limit_price=order.limit_price,
            )
            logger.info("Submitted {} {} shares of {}", order.side, qty, order.symbol)

    def market_clock(self):
        client = self._ensure_client()
        if client is None:
            return None
        return client.get_clock()
