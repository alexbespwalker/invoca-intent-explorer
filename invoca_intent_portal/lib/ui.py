"""Shared UI helpers for Streamlit pages."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def apply_base_styles() -> None:
    """Apply a compact visual baseline across portal pages."""
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2.2rem;
            max-width: 1340px;
        }
        div[data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.6rem 0.8rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_defaults(fig: go.Figure) -> go.Figure:
    """Apply consistent chart defaults, preventing Plotly 'undefined' title bug."""
    fig.update_layout(
        title=dict(text=""),
        margin=dict(t=20, b=20, l=20, r=20),
    )
    return fig
