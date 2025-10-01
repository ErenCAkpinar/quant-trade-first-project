from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..config.schema import Settings
from .base import IDataProvider, SymbolMeta

_ALPACA_PY_AVAILABLE = False
_ALPACA_PY_IMPORT_ERROR: str | None = None
_TRADE_API_AVAILABLE = False
_TRADE_API_IMPORT_ERROR: str | None = None

try:  # pragma: no cover - optional dependency
    import alpaca_trade_api as tradeapi
    _TRADE_API_AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional dependency
    tradeapi = None
    _TRADE_API_IMPORT_ERROR = str(exc)


_TIMEFRAME_MAP = {
    "1Min": lambda TF, TFU: TF.Minute,
    "5Min": lambda TF, TFU: TF(5, TFU.Minute),
    "15Min": lambda TF, TFU: TF(15, TFU.Minute),
    "30Min": lambda TF, TFU: TF(30, TFU.Minute),
    "1Hour": lambda TF, TFU: TF.Hour,
    "1Day": lambda TF, TFU: TF.Day,
}


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AlpacaProvider(IDataProvider):
    """Market data provider backed by Alpaca Market Data API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.data_config = settings.data
        self.alpaca_config = settings.alpaca
        key = os.getenv(self.alpaca_config.key_env)
        secret = os.getenv(self.alpaca_config.secret_env)
        if not key or not secret:
            raise EnvironmentError(
                "Alpaca credentials not found in environment. "
                f"Ensure {self.alpaca_config.key_env} and {self.alpaca_config.secret_env} are set."
            )
        self._alpaca_py_modules = None
        self._mode = "none"
        self.client = self._try_init_alpaca_py(key, secret)
        if self.client is None:
            self.client = self._try_init_trade_api(key, secret)
        if self.client is None:
            raise ImportError(
                "Alpaca provider requires alpaca-py or alpaca-trade-api. "
                f"alpaca-py import error: {_ALPACA_PY_IMPORT_ERROR}; "
                f"alpaca-trade-api import error: {_TRADE_API_IMPORT_ERROR}"
            )
        self._meta = self._load_symbol_meta()

    def _try_init_alpaca_py(self, key: str, secret: str):
        global _ALPACA_PY_AVAILABLE, _ALPACA_PY_IMPORT_ERROR
        _ensure_urllib3_six_moves()
        try:  # pragma: no cover - optional dependency
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
        except Exception as exc:  # pragma: no cover - align with optional install
            _ALPACA_PY_IMPORT_ERROR = str(exc)
            return None
        try:
            client = StockHistoricalDataClient(
                api_key=key,
                secret_key=secret,
                url_override=self.alpaca_config.data_base_url,
            )
            self._alpaca_py_modules = {
                "StockBarsRequest": StockBarsRequest,
                "TimeFrame": TimeFrame,
                "TimeFrameUnit": TimeFrameUnit,
            }
            self._mode = "alpaca_py"
            _ALPACA_PY_AVAILABLE = True
            _ALPACA_PY_IMPORT_ERROR = None
            return client
        except Exception as exc:  # pragma: no cover - defensive guard
            _ALPACA_PY_IMPORT_ERROR = str(exc)
            return None

    def _try_init_trade_api(self, key: str, secret: str):
        global _TRADE_API_AVAILABLE, _TRADE_API_IMPORT_ERROR
        if tradeapi is None:
            return None
        _ensure_urllib3_six_moves()
        try:
            client = tradeapi.REST(
                key,
                secret,
                base_url=self.alpaca_config.trading_base_url,
                data_base_url=self.alpaca_config.data_base_url,
            )
            self._mode = "trade_api"
            _TRADE_API_AVAILABLE = True
            _TRADE_API_IMPORT_ERROR = None
            return client
        except Exception as exc:  # pragma: no cover - defensive guard
            _TRADE_API_IMPORT_ERROR = str(exc)
            return None

    def _load_symbol_meta(self) -> list[SymbolMeta]:
        symbols: list[str]
        path = Path(self.data_config.path)
        universe_path = path / self.data_config.equities_universe
        if self.data_config.symbols:
            symbols = list(self.data_config.symbols)
            sectors = {}
        elif universe_path.exists():
            df = pd.read_csv(universe_path)
            if "symbol" not in df.columns:
                raise ValueError(f"Universe file {universe_path} missing 'symbol' column")
            symbols = df["symbol"].astype(str).tolist()
            sectors = df.set_index("symbol").to_dict().get("sector", {})
        else:
            raise FileNotFoundError(
                "Equities universe file not found and no explicit symbols provided for Alpaca provider"
            )
        meta = []
        for symbol in symbols:
            meta.append(SymbolMeta(symbol=symbol, sector=sectors.get(symbol)))
        return meta

    @cached_property
    def symbols(self) -> list[str]:
        return [m.symbol for m in self._meta]

    def _resolve_timeframe(self) -> TimeFrame:
        tf = self.data_config.timeframe or "1Day"
        if self._mode == "trade_api":
            return self.data_config.timeframe or "1Day"
        modules = self._alpaca_py_modules
        if not modules:
            raise ImportError("alpaca-py is required to resolve Alpaca timeframes")
        if tf not in _TIMEFRAME_MAP:
            raise ValueError(f"Unsupported Alpaca timeframe '{tf}'")
        TimeFrame = modules["TimeFrame"]
        TimeFrameUnit = modules["TimeFrameUnit"]
        return _TIMEFRAME_MAP[tf](TimeFrame, TimeFrameUnit)

    def get_daily_bars(self, symbols: Iterable[str], start: datetime, end: datetime) -> pd.DataFrame:
        symbols = list(symbols) or self.symbols
        if not symbols:
            return pd.DataFrame()
        start_utc = _ensure_utc(start)
        end_utc = _ensure_utc(end)
        if self._mode == "alpaca_py":
            timeframe = self._resolve_timeframe()
            modules = self._alpaca_py_modules or {}
            StockBarsRequest = modules.get("StockBarsRequest")
            if StockBarsRequest is None:
                raise ImportError("alpaca-py components unavailable to request bars")
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe,
                start=start_utc,
                end=end_utc,
                feed=self.alpaca_config.data_feed,
                adjustment="raw",
                limit=None,
            )
            response = self.client.get_stock_bars(request)
            df = response.df
            if df.empty:
                return pd.DataFrame()
            frame = df.reset_index().rename(columns={"timestamp": "date"})
            frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_convert(None)
        else:
            timeframe = self._resolve_timeframe()
            bars = self.client.get_bars(
                symbols,
                timeframe,
                start=start_utc.isoformat(),
                end=end_utc.isoformat(),
                adjustment="raw",
                feed=self.alpaca_config.data_feed,
            )
            df = bars.df
            if df.empty:
                return pd.DataFrame()
            frame = df.reset_index().rename(columns={"timestamp": "date"})
            frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_convert(None)
        frame.rename(
            columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "trade_count": "trade_count",
                "vwap": "vwap",
            },
            inplace=True,
        )
        if "adj_close" not in frame.columns:
            frame["adj_close"] = frame["close"]
        cols = ["date", "symbol", "open", "high", "low", "close", "adj_close", "volume"]
        frame = frame.reindex(columns=cols)
        start_naive = start_utc.replace(tzinfo=None)
        end_naive = end_utc.replace(tzinfo=None)
        frame = frame[(frame["date"] >= start_naive) & (frame["date"] <= end_naive)]
        frame.set_index(["date", "symbol"], inplace=True)
        return frame.sort_index()

    def get_fundamentals(self, symbols: Iterable[str]) -> pd.DataFrame:
        # Alpaca fundamentals require separate subscriptions; stubbed as empty for now.
        return pd.DataFrame()

    def get_intraday_bars(self, symbols: Iterable[str], start: datetime, end: datetime) -> pd.DataFrame:
        # TODO: Implement intraday fetch via Alpaca if needed.
        return pd.DataFrame()

    def get_symbol_meta(self) -> list[SymbolMeta]:
        return self._meta
def _ensure_urllib3_six_moves() -> None:
    """Ensure urllib3's vendored six module exposes moves for Python 3.12."""
    import sys
    import types

    if "urllib3.packages.six.moves" in sys.modules:
        return
    try:
        import six
    except Exception:
        return
    # Register base module alias if needed
    sys.modules.setdefault("urllib3.packages.six", six)
    moves = six.moves
    module = types.ModuleType("urllib3.packages.six.moves")

    def _getattr(name: str):
        return getattr(moves, name)

    def _dir():
        return [attr for attr in dir(moves) if not attr.startswith("__")]

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    module.__dir__ = _dir  # type: ignore[attr-defined]

    for attr in _dir():
        try:
            value = getattr(moves, attr)
        except Exception:
            continue
        setattr(module, attr, value)
        if isinstance(value, types.ModuleType):
            sys.modules.setdefault(f"urllib3.packages.six.moves.{attr}", value)

    sys.modules.setdefault("urllib3.packages.six.moves", module)

    # Explicitly register common modules required by urllib3.
    try:
        import http.client as http_client
        sys.modules.setdefault("urllib3.packages.six.moves.http_client", http_client)
    except Exception:
        pass
    try:
        import urllib.parse as urllib_parse
        sys.modules.setdefault("urllib3.packages.six.moves.urllib", module.urllib)  # type: ignore[attr-defined]
        sys.modules.setdefault("urllib3.packages.six.moves.urllib.parse", urllib_parse)
    except Exception:
        pass
    try:
        import queue as queue_mod
        sys.modules.setdefault("urllib3.packages.six.moves.queue", queue_mod)
    except Exception:
        pass
