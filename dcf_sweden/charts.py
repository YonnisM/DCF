"""Plot helpers for Streamlit or CLI usage."""
from __future__ import annotations

import numpy as np
import plotly.express as px

from .formatting import as_percent


def heatmap_wacc_g(wacc_values, g_values, data: np.ndarray):
    fig = px.imshow(
        data,
        x=[as_percent(w) for w in wacc_values],
        y=[as_percent(g) for g in g_values],
        origin="lower",
        labels=dict(x="WACC", y="g", color="Terminal Value"),
    )
    fig.update_layout(height=400)
    return fig


def heatmap_wacc_exit(wacc_values, exit_values, data: np.ndarray):
    fig = px.imshow(
        data,
        x=[as_percent(w) for w in wacc_values],
        y=[f"{m}x" for m in exit_values],
        origin="lower",
        labels=dict(x="WACC", y="Exit EV/EBITDA", color="PV of TV"),
    )
    fig.update_layout(height=400)
    return fig

