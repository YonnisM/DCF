"""Data access layer using yfinance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

try:  # pragma: no cover - optional dependency
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

try:  # allow running as package or script
    from constants import DEFAULT_FX_TICKERS
except ImportError:  # pragma: no cover
    from .constants import DEFAULT_FX_TICKERS


@dataclass
class MarketData:
    price: float
    currency: str
    shares_outstanding: float
    market_cap: float


@dataclass
class FinancialStatements:
    income_statement: pd.DataFrame
    balance_sheet: pd.DataFrame
    cash_flow: pd.DataFrame


def fetch_market_data(ticker: str) -> MarketData:
    """Fetch latest market data for a ticker."""
    if yf is None:
        raise RuntimeError("yfinance is required for market data fetching")
    info = yf.Ticker(ticker).info
    return MarketData(
        price=info.get("regularMarketPrice"),
        currency=info.get("currency", "SEK"),
        shares_outstanding=info.get("sharesOutstanding", 0.0),
        market_cap=info.get("marketCap", 0.0),
    )


def fetch_financials(ticker: str) -> FinancialStatements:
    """Return financial statements for a ticker.

    The function mirrors the structure from Yahoo Finance. It returns empty
    DataFrames if the download fails to keep callers robust.
    """
    if yf is None:
        raise RuntimeError("yfinance is required for financials fetching")
    yft = yf.Ticker(ticker)
    try:
        income = yft.financials.T
        balance = yft.balance_sheet.T
        cash = yft.cashflow.T
    except Exception:
        income = pd.DataFrame()
        balance = pd.DataFrame()
        cash = pd.DataFrame()
    return FinancialStatements(income, balance, cash)


def fetch_fx_rate(from_currency: str, to_currency: str = "SEK") -> Optional[float]:
    """Fetch latest FX rate using yfinance."""
    if from_currency == to_currency:
        return 1.0
    if yf is None:
        return None
    ticker = DEFAULT_FX_TICKERS.get(from_currency.upper())
    if ticker is None:
        return None
    data = yf.Ticker(ticker).history(period="1d")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])


def convert_to_sek(amount: float, currency: str) -> Optional[float]:
    rate = fetch_fx_rate(currency, "SEK")
    if rate is None:
        return None
    return amount * rate

