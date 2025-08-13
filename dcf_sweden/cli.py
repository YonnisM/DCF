"""Command line interface for the Swedish DCF app."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import numpy as np

from .assumptions import Assumptions
from .constants import DEFAULT_MRP_SE, DEFAULT_RF_PLACEHOLDER, DEFAULT_TAX_RATE_SE
from .dcf import (
    compute_fcff,
    compute_wacc,
    enterprise_value_from_fcff,
    equity_value_from_ev,
    per_share_value,
    terminal_value_perpetuity,
    terminal_value_exit_multiple,
)
from .formatting import format_currency, table_to_csv


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="FCFF-based DCF for Swedish equities")
    p.add_argument("--ticker", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--method", choices=["perpetuity", "exit"], default="perpetuity")
    p.add_argument("--g", type=float, default=0.02)
    p.add_argument("--exit-multiple", type=float, default=10.0)
    p.add_argument("--rf", type=float, default=DEFAULT_RF_PLACEHOLDER)
    p.add_argument("--beta", type=float, default=1.0)
    p.add_argument("--mrp", type=float, default=DEFAULT_MRP_SE)
    p.add_argument("--size-premium-bps", dest="size_premium_bps", type=float, default=0.0)
    p.add_argument("--cod", type=float, default=0.03)
    p.add_argument("--tax", type=float, default=DEFAULT_TAX_RATE_SE)
    p.add_argument("--capex-pct", type=float, default=0.05)
    p.add_argument("--da-pct", type=float, default=0.05)
    p.add_argument("--deltawnc-pct", type=float, default=0.01)
    p.add_argument("--revenue", type=float, nargs="+", required=True, help="Historical revenue sequence for CAGR")
    p.add_argument("--ebit-margin", type=float, default=0.1)
    p.add_argument("--net-debt", type=float, default=0.0)
    p.add_argument("--shares", type=float, default=1.0)
    p.add_argument("--export-dir", default="./outputs")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    # Forecast revenues
    last_revenue = args.revenue[-1]
    revenues = [last_revenue * (1 + args.g) ** i for i in range(1, args.horizon + 1)]

    ebit = [r * args.ebit_margin for r in revenues]
    da = [r * args.da_pct for r in revenues]
    capex = [r * args.capex_pct for r in revenues]
    deltawnc = [r * args.deltawnc_pct for r in revenues]

    fcffs = [
        compute_fcff(e, args.tax, d, c, w) for e, d, c, w in zip(ebit, da, capex, deltawnc)
    ]

    wacc = compute_wacc(args.rf, args.beta, args.mrp, args.size_premium_bps / 10000, args.cod, args.tax, 1, 0)

    if args.method == "perpetuity":
        tv = terminal_value_perpetuity(fcffs[-1] * (1 + args.g), wacc, args.g)
    else:
        tv = terminal_value_exit_multiple(ebit[-1] + da[-1], args.exit_multiple)

    ev = enterprise_value_from_fcff(fcffs, wacc, tv)
    eq = equity_value_from_ev(ev, args.net_debt)
    ps = per_share_value(eq, args.shares)

    print(f"Intrinsic value per share: {format_currency(ps)}")

    export_path = Path(args.export_dir)
    export_path.mkdir(parents=True, exist_ok=True)
    csv = table_to_csv(
        ["Year", "Revenue", "EBIT", "FCFF"],
        zip(range(1, args.horizon + 1), revenues, ebit, fcffs),
    )
    (export_path / f"{args.ticker}_forecast.csv").write_text(csv)

    summary = {
        "ticker": args.ticker,
        "per_share_value": ps,
    }
    (export_path / f"{args.ticker}_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()

