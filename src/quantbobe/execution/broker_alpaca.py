from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING, Dict, Iterable, Optional

from dotenv import load_dotenv
from loguru import logger

try:  # pragma: no cover - optional dependency import
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

    _ALPACA_PY_AVAILABLE = True
except Exception:  # pragma: no cover - import fallback if package missing
    TradingClient = None
    OrderSide = None
    TimeInForce = None
    LimitOrderRequest = None
    MarketOrderRequest = None
    _ALPACA_PY_AVAILABLE = False

try:  # pragma: no cover - legacy dependency fallback
    import alpaca_trade_api as tradeapi
except Exception:  # pragma: no cover - optional dependency import
    tradeapi = None

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ..config.schema import AlpacaConfig


@dataclass
class OrderTicket:
    symbol: str
    qty: float
    side: str
    type: str = "limit"
    limit_price: Optional[float] = None


class AlpacaBroker:
    """Alpaca trading client wrapper using alpaca-py."""

    def __init__(self, config: Optional["AlpacaConfig"] = None) -> None:
        load_dotenv()
        self._config = config
        self._key_env = config.key_env if config else "ALPACA_API_KEY_ID"
        self._secret_env = config.secret_env if config else "ALPACA_API_SECRET_KEY"
        self._base_url = (
            config.trading_base_url
            if config
            else os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")
        )
        self._client, self._mode = self._init_client()

    def _init_client(self):
        api_key = os.getenv(self._key_env)
        api_secret = os.getenv(self._secret_env)
        if not api_key or not api_secret:
            logger.warning(
                "Alpaca credentials missing in environment (expected %s/%s); "
                "broker will run in dry mode.",
                self._key_env,
                self._secret_env,
            )
            return None, "none"
        if _ALPACA_PY_AVAILABLE and TradingClient is not None:
            try:
                import inspect

                paper_mode = "paper" in self._base_url.lower()
                params = inspect.signature(TradingClient.__init__).parameters
                call_args: list[str] = []
                call_kwargs: Dict[str, object] = {}
                if "api_key" in params:
                    call_kwargs["api_key"] = api_key
                    if "secret_key" in params:
                        call_kwargs["secret_key"] = api_secret
                    else:
                        call_args.append(api_secret)
                else:
                    call_args.extend([api_key, api_secret])
                if "paper" in params:
                    call_kwargs["paper"] = paper_mode
                if "url_override" in params:
                    call_kwargs["url_override"] = self._base_url
                elif "base_url" in params:
                    call_kwargs["base_url"] = self._base_url
                client = TradingClient(*call_args, **call_kwargs)
                return client, "alpaca_py"
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.exception("Failed to initialise Alpaca TradingClient: %s", exc)
        if tradeapi is not None:
            try:
                client = tradeapi.REST(api_key, api_secret, base_url=self._base_url)
                return client, "trade_api"
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.exception(
                    "Failed to initialise alpaca-trade-api REST client: %s", exc
                )
        logger.warning("No Alpaca client available; running in dry mode.")
        return None, "none"

    def get_cash(self) -> float:
        if self._client is None:
            return 0.0
        account = self._client.get_account()
        return float(account.cash)

    def get_positions(self) -> Dict[str, float]:
        if self._client is None:
            return {}
        positions = {}
        if self._mode == "alpaca_py":
            to_iter = self._client.get_all_positions()
        else:
            to_iter = self._client.list_positions()
        for position in to_iter:
            qty = float(getattr(position, "qty", 0))
            positions[position.symbol] = qty
        return positions

    def cancel_open_orders(self) -> None:
        if self._client is None:
            return
        if self._mode == "alpaca_py":
            self._client.cancel_orders()
        else:
            self._client.cancel_all_orders()

    def submit_orders(self, tickets: Iterable[OrderTicket]) -> None:
        orders = list(tickets)
        if self._client is None:
            logger.info("Dry-run orders: {}", orders)
            return
        for order in orders:
            qty = abs(float(order.qty))
            if qty < 1e-4:
                continue
            side = order.side.lower()
            participation = min(qty / 1_000_000.0, 1.0)
            if participation > 0.05:
                logger.warning(
                    "Participation %.4f too high for %s; skipping",
                    participation,
                    order.symbol,
                )
                continue
            try:
                self._submit_order(order, qty, side)
                logger.info(
                    "Submitted %s %s shares of %s", order.side, qty, order.symbol
                )
            except Exception as exc:  # pragma: no cover - network/API errors
                logger.exception("Failed to submit order for %s: %s", order.symbol, exc)

    def _submit_order(self, order: OrderTicket, qty: float, side: str) -> None:
        order_type = order.type.lower()
        if self._mode == "alpaca_py":
            tif = TimeInForce.DAY
            if order_type == "market":
                request = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=qty,
                    side=OrderSide(side),
                    time_in_force=tif,
                )
            elif order_type == "limit":
                if order.limit_price is None:
                    raise ValueError("Limit price required for limit orders")
                price = (
                    Decimal(str(order.limit_price))
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    .normalize()
                )
                request = LimitOrderRequest(
                    symbol=order.symbol,
                    qty=qty,
                    side=OrderSide(side),
                    limit_price=float(price),
                    time_in_force=tif,
                )
            else:
                raise ValueError(f"Unsupported order type '{order.type}'")
            self._client.submit_order(request)
        elif self._mode == "trade_api":
            params = {
                "symbol": order.symbol,
                "qty": qty,
                "side": side,
                "time_in_force": "day",
                "type": order_type,
            }
            if order_type == "limit":
                if order.limit_price is None:
                    raise ValueError("Limit price required for limit orders")
                params["limit_price"] = float(
                    Decimal(str(order.limit_price)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                )
            self._client.submit_order(**params)
        else:
            raise RuntimeError("No Alpaca client configured")

    def market_clock(self):
        if self._client is None:
            return None
        return self._client.get_clock()
