from dcf_sweden.assumptions import revenue_cagr, propose_capex_pct, propose_da_pct


def test_revenue_cagr():
    revs = [100, 110, 121]
    assert abs(revenue_cagr(revs) - 0.10) < 1e-6


def test_capex_pct():
    revenues = [100, 100, 100]
    da = [5, 5, 5]
    capex = [4, 4, 4]
    da_pct = propose_da_pct(da, revenues)
    capex_pct = propose_capex_pct(capex, revenues, da_pct)
    assert capex_pct == da_pct
