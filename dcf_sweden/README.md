# Swedish DCF Valuation App

This project provides a minimal yet functional discounted cash-flow (DCF) valuation tool focused on Swedish equities.
It offers both a Streamlit web interface and a command line interface.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Streamlit

```bash
streamlit run app.py
```

### CLI

```bash
python cli.py --ticker VOLV-B.ST --revenue 400000000000 430000000000 450000000000 --method perpetuity --g 0.02
```

Outputs are written to `./outputs` by default.

## Data Sources

The app relies on [yfinance](https://github.com/ranaroussi/yfinance) for market and financial data. All values are converted to SEK
using Yahoo Finance FX tickers when necessary.

## Disclaimer

This tool is for educational purposes only and should not be considered investment advice.
