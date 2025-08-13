"""Formatting helpers for currency and numbers."""
from __future__ import annotations

import math
from typing import Iterable


def format_currency(value: float, currency: str = "SEK", decimals: int = 0) -> str:
    """Return a human readable currency string."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value:,.{decimals}f} {currency}"


def as_percent(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def table_to_csv(headers: Iterable[str], rows: Iterable[Iterable]) -> str:
    """Convert a table to CSV string."""
    import csv
    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(list(headers))
    for row in rows:
        writer.writerow(list(row))
    return buf.getvalue()

