import numpy as np

from dcf_sweden.dcf import (
    compute_fcff,
    compute_wacc,
    terminal_value_perpetuity,
    enterprise_value_from_fcff,
    equity_value_from_ev,
    per_share_value,
    sensitivity_wacc_g,
)


def test_fcff():
    fcff = compute_fcff(100, 0.2, 10, 20, 5)
    assert fcff == 100 * 0.8 + 10 - 20 - 5


def test_wacc():
    wacc = compute_wacc(0.02, 1.0, 0.05, 0.0, 0.03, 0.2, 60, 40)
    coe = 0.02 + 1.0 * 0.05
    cod_at = 0.03 * (1 - 0.2)
    expected = 0.6 * coe + 0.4 * cod_at
    assert abs(wacc - expected) < 1e-9


def test_terminal_value_error():
    try:
        terminal_value_perpetuity(100, 0.05, 0.05)
    except ValueError:
        assert True
    else:  # pragma: no cover - ensures error raised
        assert False


def test_valuation_flow():
    fcffs = [100, 110, 120]
    wacc = 0.1
    tv = terminal_value_perpetuity(120 * 1.02, wacc, 0.02)
    ev = enterprise_value_from_fcff(fcffs, wacc, tv)
    eq = equity_value_from_ev(ev, net_debt=50)
    ps = per_share_value(eq, 10)
    assert ps > 0


def test_sensitivity_shape():
    grid = sensitivity_wacc_g(100, [0.07, 0.08], [0.01, 0.02, 0.025])
    assert grid.shape == (3, 2)
    assert grid[-1, 0] > 0
