from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd


@dataclass
class SymbolMeta:
    symbol: str
    sector: str | None = None
    beta: float | None = None


class IDataProvider(ABC):
    """Interface for point-in-time market data providers."""

    @abstractmethod
    def get_daily_bars(self, symbols: Iterable[str], start: datetime, end: datetime) -> pd.DataFrame:
        """Return multi-index DataFrame (date, symbol) with OHLCV and adjustments."""

    @abstractmethod
    def get_fundamentals(self, symbols: Iterable[str]) -> pd.DataFrame:
        """Return point-in-time fundamentals indexed by date and symbol."""

    @abstractmethod
    def get_intraday_bars(self, symbols: Iterable[str], start: datetime, end: datetime) -> pd.DataFrame:
        """Return intraday OHLCV data. Optional for providers that do not support it."""

    @abstractmethod
    def get_symbol_meta(self) -> list[SymbolMeta]:
        """Return metadata for configured symbols (sector mapping, etc.)."""
