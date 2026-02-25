"""Shared UI helpers for Streamlit pages."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# ── Color palette ─────────────────────────────────────────────────────────
# Dark navy base with teal accent, warm amber secondary
COLORS = {
    "bg_primary": "#0f172a",
    "bg_surface": "#1e293b",
    "bg_elevated": "#273548",
    "border": "#334155",
    "border_subtle": "#1e293b",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent": "#22d3ee",       # cyan/teal
    "accent_dim": "#164e63",
    "amber": "#f59e0b",
    "amber_dim": "#78350f",
    "emerald": "#34d399",
    "rose": "#fb7185",
    "violet": "#a78bfa",
}

# Chart color sequence: distinctive, readable on dark backgrounds
CHART_COLORS = [
    "#22d3ee",  # cyan
    "#f59e0b",  # amber
    "#34d399",  # emerald
    "#fb7185",  # rose
    "#a78bfa",  # violet
    "#38bdf8",  # sky
    "#fbbf24",  # yellow
    "#6ee7b7",  # mint
    "#f472b6",  # pink
    "#818cf8",  # indigo
]


def apply_base_styles() -> None:
    """Apply dark-theme visual baseline across portal pages."""
    st.markdown(
        """
        <style>
        /* ── Import fonts ─────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ── Global typography ────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* ── Main container ───────────────────────────── */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        /* ── Page title ───────────────────────────────── */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            font-size: 2rem !important;
            color: #f1f5f9 !important;
        }

        /* ── Subheadings ──────────────────────────────── */
        h2, h3 {
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
            color: #cbd5e1 !important;
        }

        /* ── Caption text ─────────────────────────────── */
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #64748b !important;
            font-size: 0.9rem !important;
        }

        /* ── KPI metric cards ─────────────────────────── */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1e293b 0%, #273548 100%);
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            border-color: #22d3ee;
            box-shadow: 0 0 20px rgba(34, 211, 238, 0.08);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] div {
            color: #94a3b8 !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.04em !important;
            text-transform: uppercase !important;
            opacity: 1 !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #f1f5f9 !important;
            font-weight: 700 !important;
            font-size: 1.4rem !important;
            font-family: 'DM Sans', sans-serif !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* ── Data table ───────────────────────────────── */
        div[data-testid="stDataFrame"] {
            border: 1px solid #334155;
            border-radius: 12px;
            overflow: hidden;
        }

        /* ── Sidebar styling ──────────────────────────── */
        section[data-testid="stSidebar"] {
            border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] h2 {
            font-size: 0.78rem !important;
            text-transform: uppercase;
            letter-spacing: 0.08em !important;
            color: #22d3ee !important;
            margin-bottom: 0.5rem !important;
            font-weight: 600 !important;
        }
        /* Sidebar navigation page links */
        section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a[aria-current="page"] {
            color: #22d3ee !important;
            font-weight: 600 !important;
        }

        /* ── Buttons ──────────────────────────────────── */
        button[kind="primary"] {
            border-radius: 10px !important;
        }

        /* ── Expanders ────────────────────────────────── */
        details {
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
        }

        /* ── Text areas ───────────────────────────────── */
        textarea {
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important;
            line-height: 1.65 !important;
        }

        /* ── Horizontal dividers ──────────────────────── */
        hr {
            border-color: #1e293b !important;
        }

        /* ── Links ────────────────────────────────────── */
        a {
            color: #22d3ee !important;
        }

        /* ── Plotly chart containers ──────────────────── */
        div[data-testid="stPlotlyChart"] {
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 0.5rem;
            background: #1e293b;
            transition: border-color 0.2s ease;
        }
        div[data-testid="stPlotlyChart"]:hover {
            border-color: #475569;
        }

        /* ── Metric delta (green arrow + pct) ─────────── */
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
        }

        /* ── Download button refinement ───────────────── */
        button[data-testid="stDownloadButton"] {
            border-radius: 10px !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
        }

        /* ── Selectbox refinement ─────────────────────── */
        div[data-testid="stSelectbox"] label {
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: #94a3b8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Plotly chart theme ────────────────────────────────────────────────────

PLOTLY_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family="DM Sans, -apple-system, sans-serif",
        color="#94a3b8",
        size=12,
    ),
    xaxis=dict(
        gridcolor="#1e293b",
        linecolor="#334155",
        zerolinecolor="#334155",
        tickfont=dict(color="#64748b", size=11),
    ),
    yaxis=dict(
        gridcolor="#1e293b",
        linecolor="#334155",
        zerolinecolor="#334155",
        tickfont=dict(color="#64748b", size=11),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
    ),
    colorway=CHART_COLORS,
)


def apply_chart_defaults(fig: go.Figure) -> go.Figure:
    """Apply dark-theme chart defaults, preventing Plotly 'undefined' title bug."""
    fig.update_layout(
        title=dict(text=""),
        margin=dict(t=20, b=40, l=40, r=20),
        **PLOTLY_TEMPLATE,
    )
    return fig
