from __future__ import annotations
import streamlit as st
import math
import pandas as pd

try:
    from constants import DEFAULT_MRP_SE, DEFAULT_RF_PLACEHOLDER, DEFAULT_TAX_RATE_SE
    from dcf import (
        compute_fcff, compute_wacc, enterprise_value_from_fcff,
        equity_value_from_ev, per_share_value, terminal_value_perpetuity
    )
    from formatting import format_currency
    from data import convert_to_sek
except ImportError:  # pragma: no cover
    from .constants import DEFAULT_MRP_SE, DEFAULT_RF_PLACEHOLDER, DEFAULT_TAX_RATE_SE
    from .dcf import (
        compute_fcff, compute_wacc, enterprise_value_from_fcff,
        equity_value_from_ev, per_share_value, terminal_value_perpetuity
    )
    from .formatting import format_currency
    from .data import convert_to_sek

# --- NEW: lightweight yfinance loader (inline to keep it simple) ---
try:
    import yfinance as yf
except Exception:
    yf = None

def safe_pct(numer, denom):
    try:
        return float(numer) / float(denom) if denom not in (0, None) else 0.0
    except Exception:
        return 0.0

st.set_page_config(page_title="Swedish DCF", layout="wide")
st.title("Swedish DCF")

st.sidebar.header("Inputs")
ticker = st.sidebar.text_input("Ticker", "VOLV-B.ST")
horizon = st.sidebar.slider("Forecast horizon (years)", 3, 10, 5, key="horizon")
g = st.sidebar.number_input("Terminal growth g", 0.0, 0.05, 0.02, step=0.005, key="g")
rf = st.sidebar.number_input("Risk-free rate", 0.0, 0.1, DEFAULT_RF_PLACEHOLDER, step=0.005, key="rf")
beta = st.sidebar.number_input("Beta", 0.0, 3.0, 1.0, step=0.1, key="beta")
mrp = st.sidebar.number_input("Market risk premium", 0.0, 0.2, DEFAULT_MRP_SE, step=0.005, key="mrp")
size_premium = st.sidebar.number_input("Size premium", 0.0, 0.05, 0.0, step=0.001, key="size_premium")
cod = st.sidebar.number_input("Cost of debt (pre-tax)", 0.0, 0.2, 0.03, step=0.005, key="cod")
tax = st.sidebar.number_input("Tax rate", 0.0, 1.0, DEFAULT_TAX_RATE_SE, step=0.01, key="tax")

# Model drivers
eb_margin = st.sidebar.number_input("EBIT margin", -0.5, 0.5, 0.10, step=0.01, key="eb_margin")
revenue = st.sidebar.number_input("Last revenue (SEK)", 0.0, 1e13, 100_000_000.0, step=1_000_000.0, key="revenue")
revgrowth = st.sidebar.number_input("Revenue growth", -0.2, 0.5, 0.05, step=0.01, key="revgrowth")
da_pct = st.sidebar.number_input("D&A % of revenue", 0.0, 0.5, 0.05, step=0.005, key="da_pct")
capex_pct = st.sidebar.number_input("Capex % of revenue", 0.0, 0.5, 0.05, step=0.005, key="capex_pct")
deltawnc_pct = st.sidebar.number_input("ΔNWC % of revenue", -0.5, 0.5, 0.01, step=0.005, key="deltawnc_pct")
net_debt = st.sidebar.number_input("Net debt (SEK)", -1e13, 1e13, 0.0, step=1_000_000.0, key="net_debt")
shares = st.sidebar.number_input("Diluted shares", 0.0, 1e12, 100_000_000.0, step=1000.0, key="shares")

# --- NEW: Prefill from Yahoo ---
if st.sidebar.button("Load from Yahoo"):
    if yf is None:
        st.sidebar.error("yfinance not installed. Run: pip install yfinance")
    else:
        try:
            t = yf.Ticker(ticker)
            info = getattr(t, "fast_info", None) or getattr(t, "info", {}) or {}
            cur = info.get("currency", "SEK")
            mcap = info.get("marketCap")
            if mcap is not None:
                mcap_sek = convert_to_sek(mcap, cur)
                if mcap_sek is not None:
                    mcap = mcap_sek
                    cur = "SEK"
            st.session_state["snapshot"] = {
                "Name": info.get("shortName") or info.get("longName") or ticker,
                "Currency": cur,
                "Market Cap": mcap,
                "Shares Out": info.get("sharesOutstanding"),
            }

            # statements come as columns = line items, rows = dates
            income = t.financials.T if hasattr(t, "financials") else pd.DataFrame()
            cash = t.cashflow.T if hasattr(t, "cashflow") else pd.DataFrame()
            balance = t.balance_sheet.T if hasattr(t, "balance_sheet") else pd.DataFrame()

            # revenue & EBIT margin defaults
            if not income.empty:
                rev_series = income.get("Total Revenue") or income.get("TotalRevenue")
                ebit_series = income.get("Ebit") or income.get("EBIT") or income.get("Operating Income")
                if rev_series is not None and len(rev_series) > 0:
                    val = float(rev_series.iloc[0])
                    conv = convert_to_sek(val, info.get("currency", "SEK"))
                    if conv is not None:
                        val = conv
                    st.session_state["revenue"] = val
                    st.sidebar.success(f"Last revenue set to {format_currency(val)}")
                if rev_series is not None and ebit_series is not None:
                    eb_val = float(safe_pct(ebit_series.mean(), rev_series.mean()))
                    st.session_state["eb_margin"] = eb_val
                    st.sidebar.success(f"EBIT margin set to {eb_val:.2%}")

            # D&A, Capex, ΔNWC %
            if not cash.empty and not income.empty:
                da = cash.get("Depreciation Amortization") or cash.get("Depreciation")
                capex = cash.get("Capital Expenditures")
                if da is not None and len(da) > 0 and st.session_state.get("revenue", 0) > 0:
                    da_val = max(0.0, min(0.5, float(da.mean() / income["Total Revenue"].mean())))
                    st.session_state["da_pct"] = da_val
                    st.sidebar.success(f"D&A % set to {da_val:.2%}")
                if capex is not None and len(capex) > 0 and st.session_state.get("revenue", 0) > 0:
                    capex_val = max(
                        st.session_state.get("da_pct", 0.0),
                        max(0.0, min(0.5, float(capex.mean() / income['Total Revenue'].mean()))),
                    )
                    st.session_state["capex_pct"] = capex_val
                    st.sidebar.success(f"Capex % set to {capex_val:.2%}")

            if not balance.empty and not income.empty:
                # ΔNWC approx using (CA-CL) yoy / revenue
                for col in ("Total Current Assets", "TotalCurrentAssets"):
                    if col in balance: ca = balance[col]; break
                else: ca = None
                for col in ("Total Current Liabilities", "TotalCurrentLiabilities"):
                    if col in balance: cl = balance[col]; break
                else: cl = None
                if ca is not None and cl is not None and "Total Revenue" in income:
                    wc = (ca - cl).sort_index()
                    d_wc = wc.diff().dropna()
                    rev_aligned = income["Total Revenue"].sort_index().reindex(d_wc.index)
                    if rev_aligned.notna().any():
                        deltawnc_val = float((d_wc / rev_aligned).mean())
                        st.session_state["deltawnc_pct"] = deltawnc_val
                        st.sidebar.success(f"ΔNWC % set to {deltawnc_val:.2%}")

            # shares & net debt (best-effort)
            if st.session_state["snapshot"].get("Shares Out"):
                st.session_state["shares"] = float(st.session_state["snapshot"]["Shares Out"])
            cash_bal = balance.get("Cash And Cash Equivalents") if not balance.empty else None
            debt = balance.get("Total Debt") if not balance.empty else None
            if cash_bal is not None and debt is not None:
                nd = float((debt.iloc[0] if len(debt) else 0) - (cash_bal.iloc[0] if len(cash_bal) else 0))
                conv = convert_to_sek(nd, info.get("currency", "SEK"))
                st.session_state["net_debt"] = conv if conv is not None else nd

        except Exception as e:
            st.error(f"Failed to load from Yahoo: {e}")

# Company snapshot (if any)
snap = st.session_state.get("snapshot")
if snap:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Name", snap["Name"])
    c2.metric("Currency", snap["Currency"])
    c3.metric("Market Cap", format_currency(snap["Market Cap"], snap["Currency"]) if snap["Market Cap"] else "-")
    c4.metric("Shares Out", f"{int(snap['Shares Out']):,}" if snap.get("Shares Out") else "-")

# --- Run DCF ---
if st.sidebar.button("Run DCF"):
    revenues = [revenue * (1 + revgrowth) ** i for i in range(1, horizon + 1)]
    ebit = [r * eb_margin for r in revenues]
    da = [r * da_pct for r in revenues]
    capex = [r * capex_pct for r in revenues]
    deltawnc = [r * deltawnc_pct for r in revenues]

    fcffs = [compute_fcff(e, tax, d, c, w) for e, d, c, w in zip(ebit, da, capex, deltawnc)]
    wacc = compute_wacc(rf, beta, mrp, size_premium, cod, tax, 1, 0)
    tv = terminal_value_perpetuity(fcffs[-1] * (1 + g), wacc, g)
    ev = enterprise_value_from_fcff(fcffs, wacc, tv)
    eq = equity_value_from_ev(ev, net_debt)
    ps = per_share_value(eq, shares)

    st.subheader("Results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Enterprise Value", format_currency(ev))
    c2.metric("Equity Value", format_currency(eq))
    c3.metric("Intrinsic Value / share", format_currency(ps))

