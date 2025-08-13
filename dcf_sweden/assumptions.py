"""Heuristics to derive default assumptions from historical data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .constants import DEFAULT_MRP_SE, DEFAULT_TAX_RATE_SE


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def revenue_cagr(revenues: Iterable[float]) -> float:
    """Compute geometric CAGR for a sequence of revenues."""
    rev = [r for r in revenues if r > 0]
    if len(rev) < 2:
        return 0.0
    start, end = rev[0], rev[-1]
    years = len(rev) - 1
    return (end / start) ** (1 / years) - 1


def avg_margin(series: Iterable[float], revenues: Iterable[float]) -> float:
    """Return average margin of series / revenues."""
    rev = np.array(revenues, dtype=float)
    ser = np.array(series, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        margins = np.where(rev != 0, ser / rev, np.nan)
    margins = margins[~np.isnan(margins)]
    if len(margins) == 0:
        return 0.0
    return float(np.mean(margins))


def propose_da_pct(da: Iterable[float], revenues: Iterable[float]) -> float:
    return clamp(avg_margin(da, revenues), 0.0, 0.2)


def propose_capex_pct(capex: Iterable[float], revenues: Iterable[float], da_pct: float) -> float:
    capex_pct = clamp(avg_margin(capex, revenues), 0.0, 0.2)
    return max(capex_pct, da_pct)


def propose_delta_nwc_pct(deltawnc: Iterable[float], revenues: Iterable[float]) -> float:
    pct = avg_margin(deltawnc, revenues)
    return clamp(pct, -0.05, 0.15)


def propose_tax_rate() -> float:
    return DEFAULT_TAX_RATE_SE


def propose_mrp() -> float:
    return DEFAULT_MRP_SE


@dataclass
class Assumptions:
    revenue_growth: float
    ebit_margin: float
    da_pct: float
    capex_pct: float
    deltawnc_pct: float
    tax_rate: float
    mrp: float


