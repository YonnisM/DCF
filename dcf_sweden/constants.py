"""Project-wide constants for Swedish DCF valuation."""

from __future__ import annotations

# Corporate tax rate in Sweden (2023)
DEFAULT_TAX_RATE_SE: float = 0.206

# Market risk premium assumption for Sweden
DEFAULT_MRP_SE: float = 0.055

# Placeholder for the risk-free rate (user should update in UI/CLI)
DEFAULT_RF_PLACEHOLDER: float = 0.02

# Common FX tickers for conversion to SEK when using yfinance
DEFAULT_FX_TICKERS = {
    "USD": "USDSEK=X",
    "EUR": "EURSEK=X",
}

# Sensitivity grid defaults
WACC_SENSITIVITY = [x / 100 for x in range(600, 1201, 50)]  # 6% -> 12% step 0.5%
G_SENSITIVITY = [x / 10000 for x in range(0, 251, 25)]  # 0% -> 2.5% step 0.25%
EXIT_MULTIPLE_SENSITIVITY = list(range(6, 15))  # 6x -> 14x

