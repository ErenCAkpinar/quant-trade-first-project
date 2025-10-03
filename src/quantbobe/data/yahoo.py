from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Iterable

import pandas as pd
import yfinance as yf

from .base import IDataProvider, SymbolMeta


@lru_cache(maxsize=32)
def _download_daily_cached(symbol: str, start: str, end: str) -> pd.DataFrame:
    return yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)


class YahooProvider(IDataProvider):
    """Thin wrapper around yfinance with point-in-time safeguards."""

    def __init__(self, universe_path: str) -> None:
        self.universe_path = universe_path
        self._meta = self._load_meta()

    def _download_daily(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        return _download_daily_cached(symbol, start, end)

    def _load_meta(self) -> list[SymbolMeta]:
        df = pd.read_csv(self.universe_path)
        return [
            SymbolMeta(
                symbol=row.symbol, sector=row.sector if hasattr(row, "sector") else None
            )
            for row in df.itertuples()
        ]

    def get_daily_bars(
        self, symbols: Iterable[str], start: datetime, end: datetime
    ) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for symbol in symbols:
            # Use simple date strings instead of ISO format
            start_str = start.strftime("%Y-%m-%d")
            end_str = end.strftime("%Y-%m-%d")
            df = self._download_daily(symbol, start_str, end_str)
            if df.empty:
                continue
            # Flatten multi-level columns
            df.columns = df.columns.get_level_values(0).str.lower()
            df["symbol"] = symbol
            df = df.reset_index()
            # The index column is named 'Date' after reset_index, rename it to 'date'
            if "Date" in df.columns:
                df = df.rename(columns={"Date": "date"})
            elif "index" in df.columns:
                df = df.rename(columns={"index": "date"})
            # Ensure date column is datetime
            df["date"] = pd.to_datetime(df["date"])
            if "adj close" in df.columns:
                df = df.rename(columns={"adj close": "adj_close"})
            frames.append(df)
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True)
        # Convert timezone-aware datetimes to naive for comparison
        if combined["date"].dt.tz is not None:
            combined["date"] = combined["date"].dt.tz_localize(None)
        # Ensure start and end are also timezone-naive
        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        end_naive = end.replace(tzinfo=None) if end.tzinfo else end
        combined = combined[
            (combined["date"] >= start_naive) & (combined["date"] <= end_naive)
        ]
        combined.set_index(["date", "symbol"], inplace=True)
        return combined.sort_index()

    def get_fundamentals(self, symbols: Iterable[str]) -> pd.DataFrame:
        records: list[pd.DataFrame] = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            try:
                fundamentals = ticker.financials.T
                if fundamentals.empty:
                    continue
                fundamentals.index = pd.to_datetime(fundamentals.index)
                fundamentals["symbol"] = symbol
                fundamentals = fundamentals.reset_index().rename(
                    columns={"index": "date"}
                )
                fundamentals = fundamentals.sort_values("date")
                fundamentals["date"] = fundamentals["date"] + pd.Timedelta(days=5)
                records.append(fundamentals)
            except Exception:  # pragma: no cover - API variability
                continue
        if not records:
            return pd.DataFrame()
        df = pd.concat(records, ignore_index=True)
        df.set_index(["date", "symbol"], inplace=True)
        return df.sort_index()

    def get_intraday_bars(
        self, symbols: Iterable[str], start: datetime, end: datetime
    ) -> pd.DataFrame:
        # Yahoo intraday is rate limited; return empty placeholder.
        return pd.DataFrame()

    def get_symbol_meta(self) -> list[SymbolMeta]:
        return self._meta
