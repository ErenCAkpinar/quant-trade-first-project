from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..config.schema import Settings
from .base import IDataProvider, SymbolMeta
from .local_csv import LocalCSVProvider
from .yahoo import YahooProvider


def build_provider(settings: Settings) -> IDataProvider:
    data_root = Path(settings.data.path)
    universe_path = data_root / settings.data.equities_universe
    if settings.data.provider == "local_csv":
        return LocalCSVProvider(data_root, universe_path)
    if settings.data.provider == "yahoo":
        return YahooProvider(str(universe_path))
    raise ValueError(f"Unsupported data provider {settings.data.provider}")


def load_universe(settings: Settings) -> list[SymbolMeta]:
    provider = build_provider(settings)
    return provider.get_symbol_meta()


def load_daily_history(
    provider: IDataProvider,
    symbols: Iterable[str],
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    data = provider.get_daily_bars(symbols, start, end)
    if data.empty:
        raise ValueError("No historical data returned for requested symbols")
    return data


def load_fundamentals(provider: IDataProvider, symbols: Iterable[str]) -> pd.DataFrame:
    return provider.get_fundamentals(symbols)
