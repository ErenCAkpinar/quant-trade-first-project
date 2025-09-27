from __future__ import annotations

from datetime import datetime

import pandas as pd


def trading_days(start: datetime, end: datetime, tz: str = "America/New_York") -> pd.DatetimeIndex:
    """Return NYSE trading days between start and end (inclusive)."""
    calendar = pd.date_range(start=start, end=end, freq="B", tz=tz)
    return calendar.tz_convert("UTC")


def align_to_session(date: pd.Timestamp) -> pd.Timestamp:
    if date.tzinfo is None:
        date = date.tz_localize("UTC")
    return date.normalize()
