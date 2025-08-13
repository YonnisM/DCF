"""Streamlit application entry point."""
from __future__ import annotations

import streamlit as st

from .constants import DEFAULT_MRP_SE, DEFAULT_RF_PLACEHOLDER, DEFAULT_TAX_RATE_SE
from .dcf import (
    compute_fcff,
    compute_wacc,
    enterprise_value_from_fcff,
    equity_value_from_ev,
    per_share_value,
    terminal_value_perpetuity,
)
from .formatting import format_currency


st.set_page_config(page_title="Swedish DCF", layout="wide")

st.sidebar.header("Inputs")
ticker = st.sidebar.text_input("Ticker", "VOLV-B.ST")
horizon = st.sidebar.slider("Forecast horizon", 3, 10, 5)
g = st.sidebar.number_input("Terminal growth g", 0.0, 0.05, 0.02, step=0.005)
rf = st.sidebar.number_input("Risk-free rate", 0.0, 0.1, DEFAULT_RF_PLACEHOLDER, step=0.005)
beta = st.sidebar.number_input("Beta", 0.0, 3.0, 1.0, step=0.1)
mrp = st.sidebar.number_input("Market risk premium", 0.0, 0.2, DEFAULT_MRP_SE, step=0.005)
size_premium = st.sidebar.number_input("Size premium", 0.0, 0.05, 0.0, step=0.001)
cod = st.sidebar.number_input("Cost of debt (pre-tax)", 0.0, 0.2, 0.03, step=0.005)
tax = st.sidebar.number_input("Tax rate", 0.0, 1.0, DEFAULT_TAX_RATE_SE, step=0.01)
eb_margin = st.sidebar.number_input("EBIT margin", -0.5, 0.5, 0.1, step=0.01)
revenue = st.sidebar.number_input("Last revenue", 0.0, 1e9, 100_000_000.0, step=1_000_000.0)
revgrowth = st.sidebar.number_input("Revenue growth", -0.2, 0.5, 0.05, step=0.01)
da_pct = st.sidebar.number_input("D&A %", 0.0, 0.2, 0.05, step=0.005)
capex_pct = st.sidebar.number_input("Capex %", 0.0, 0.2, 0.05, step=0.005)
deltawnc_pct = st.sidebar.number_input("ΔNWC %", -0.1, 0.2, 0.01, step=0.005)
net_debt = st.sidebar.number_input("Net debt", -1e9, 1e9, 0.0, step=1_000_000.0)
shares = st.sidebar.number_input("Diluted shares", 0.0, 1e12, 100_000_000.0, step=1000.0)

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
    st.metric("Enterprise Value", format_currency(ev))
    st.metric("Equity Value", format_currency(eq))
    st.metric("Intrinsic Value / share", format_currency(ps))

