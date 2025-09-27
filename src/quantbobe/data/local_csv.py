from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from .base import IDataProvider, SymbolMeta


class LocalCSVProvider(IDataProvider):
    """CSV/Parquet loader for pre-downloaded datasets."""

    def __init__(self, root: str | Path, universe_file: str | Path) -> None:
        self.root = Path(root)
        self.universe_file = Path(universe_file)
        if not self.root.exists():
            raise FileNotFoundError(f"Data root {self.root} not found")
        if not self.universe_file.exists():
            raise FileNotFoundError(f"Universe file {self.universe_file} not found")

    def _bars_path(self, symbol: str) -> Path:
        csv_path = self.root / f"{symbol}.csv"
        parquet_path = self.root / f"{symbol}.parquet"
        if csv_path.exists():
            return csv_path
        if parquet_path.exists():
            return parquet_path
        raise FileNotFoundError(f"Bars file missing for {symbol}")

    def get_daily_bars(self, symbols: Iterable[str], start: datetime, end: datetime) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for symbol in symbols:
            path = self._bars_path(symbol)
            if path.suffix == ".csv":
                df = pd.read_csv(path, parse_dates=["date"])
            else:
                df = pd.read_parquet(path)
                if "date" not in df.columns:
                    df = df.reset_index().rename(columns={"index": "date"})
            df = df[(df["date"] >= start) & (df["date"] <= end)].copy()
            df["symbol"] = symbol
            frames.append(df)
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True)
        combined.set_index(["date", "symbol"], inplace=True)
        return combined.sort_index()

    def get_fundamentals(self, symbols: Iterable[str]) -> pd.DataFrame:
        path = self.root / "fundamentals.csv"
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path, parse_dates=["date"])
        df = df[df["symbol"].isin(list(symbols))]
        df.set_index(["date", "symbol"], inplace=True)
        return df.sort_index()

    def get_intraday_bars(self, symbols: Iterable[str], start: datetime, end: datetime) -> pd.DataFrame:
        path = self.root / "intraday.parquet"
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_parquet(path)
        df = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)]
        df = df[df["symbol"].isin(list(symbols))]
        df.set_index(["timestamp", "symbol"], inplace=True)
        return df.sort_index()

    def get_symbol_meta(self) -> list[SymbolMeta]:
        df = pd.read_csv(self.universe_file)
        return [SymbolMeta(symbol=row.symbol, sector=row.get("sector")) for row in df.itertuples()]
