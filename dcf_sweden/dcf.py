"""Core DCF valuation engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass
class DCFResult:
    enterprise_value: float
    equity_value: float
    per_share_value: float


# --- FCFF ---------------------------------------------------------------

def compute_fcff(ebit: float, tax_rate: float, da: float, capex: float, delta_nwc: float) -> float:
    """Free cash flow to firm."""
    return ebit * (1 - tax_rate) + da - capex - delta_nwc


# --- WACC ---------------------------------------------------------------

def cost_of_equity(rf: float, beta: float, mrp: float, size_premium: float = 0.0) -> float:
    return rf + beta * (mrp + size_premium)


def cost_of_debt_after_tax(cod: float, tax_rate: float) -> float:
    return cod * (1 - tax_rate)


def compute_wacc(rf: float, beta: float, mrp: float, size_premium: float, cod: float, tax_rate: float, equity: float, debt: float) -> float:
    coe = cost_of_equity(rf, beta, mrp, size_premium)
    cod_at = cost_of_debt_after_tax(cod, tax_rate)
    total = equity + debt
    if total == 0:
        return coe
    return (equity / total) * coe + (debt / total) * cod_at


# --- Terminal Value ----------------------------------------------------

def terminal_value_perpetuity(fcff_next: float, wacc: float, g: float) -> float:
    if g >= wacc:
        raise ValueError("Terminal growth must be less than WACC")
    return fcff_next / (wacc - g)


def terminal_value_exit_multiple(ebitda: float, exit_multiple: float) -> float:
    return ebitda * exit_multiple


# --- PV calculations ---------------------------------------------------

def discount_cash_flows(fcffs: Iterable[float], wacc: float) -> List[float]:
    pvs = []
    for t, fcff in enumerate(fcffs, start=1):
        pvs.append(fcff / ((1 + wacc) ** t))
    return pvs


def enterprise_value_from_fcff(fcffs: Iterable[float], wacc: float, terminal_value: float) -> float:
    pvs = discount_cash_flows(fcffs, wacc)
    n = len(pvs)
    ev = sum(pvs) + terminal_value / ((1 + wacc) ** n)
    return ev


def equity_value_from_ev(ev: float, net_debt: float, minority_interest: float = 0.0, investments: float = 0.0) -> float:
    return ev - net_debt - minority_interest + investments


def per_share_value(equity_value: float, shares_outstanding: float) -> float:
    if shares_outstanding <= 0:
        return float("nan")
    return equity_value / shares_outstanding


# --- Sensitivities -----------------------------------------------------

def sensitivity_wacc_g(fcff_last: float, wacc_values: Iterable[float], g_values: Iterable[float]) -> np.ndarray:
    grid = np.zeros((len(g_values), len(wacc_values)))
    for i, g in enumerate(g_values):
        for j, wacc in enumerate(wacc_values):
            try:
                grid[i, j] = terminal_value_perpetuity(fcff_last * (1 + g), wacc, g)
            except ValueError:
                grid[i, j] = np.nan
    return grid


def sensitivity_wacc_exit(ebitda: float, wacc_values: Iterable[float], exit_multiples: Iterable[float]) -> np.ndarray:
    grid = np.zeros((len(exit_multiples), len(wacc_values)))
    for i, multiple in enumerate(exit_multiples):
        tv = terminal_value_exit_multiple(ebitda, multiple)
        for j, wacc in enumerate(wacc_values):
            grid[i, j] = tv / (1 + wacc) ** len(wacc_values)
    return grid


