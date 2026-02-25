"""Shared UI helpers for Streamlit pages."""

from __future__ import annotations

import html as _html

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
            background: linear-gradient(145deg, #1a2740 0%, #1e293b 60%, #222f43 100%);
            border: 1px solid #334155;
            border-left: 3px solid #334155;
            border-radius: 14px;
            padding: 1.1rem 1.2rem 1rem;
            transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.15s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03);
        }
        div[data-testid="stMetric"]:hover {
            border-color: #475569;
            border-left-color: #22d3ee;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 0 24px rgba(34,211,238,0.06);
            transform: translateY(-1px);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] div {
            color: #8b9db8 !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
            opacity: 1 !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #f1f5f9 !important;
            font-weight: 700 !important;
            font-size: 1.6rem !important;
            font-family: 'DM Sans', sans-serif !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.3 !important;
        }

        /* ── Data table ───────────────────────────────── */
        div[data-testid="stDataFrame"] {
            border: 1px solid #2d3b50;
            border-radius: 12px;
            overflow: hidden;
            background: linear-gradient(180deg, #1a2740 0%, #1e293b 100%);
            box-shadow: 0 1px 4px rgba(0,0,0,0.15);
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
            border: 1px solid #2d3b50;
            border-radius: 12px;
            padding: 0.6rem 0.6rem 0.3rem;
            background: linear-gradient(180deg, #1a2740 0%, #1e293b 100%);
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
            box-shadow: 0 1px 4px rgba(0,0,0,0.15);
        }
        div[data-testid="stPlotlyChart"]:hover {
            border-color: #3d4f69;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        }

        /* ── Chart section titles ────────────────────── */
        .chart-title {
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #8b9db8;
            margin: 1rem 0 0.4rem 0;
            padding-left: 2px;
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

        /* ── Login card ──────────────────────────────── */
        .login-card {
            background: linear-gradient(145deg, #1a2740 0%, #1e293b 60%, #1a2740 100%);
            border: 1px solid #2d3b50;
            border-radius: 16px;
            padding: 2rem 2rem 1.5rem;
            margin-top: 1rem;
            box-shadow: 0 4px 24px rgba(0,0,0,0.3), 0 0 40px rgba(34,211,238,0.03);
        }
        .login-card-header {
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #64748b;
            margin-bottom: 1.2rem;
            text-align: center;
        }

        /* ── Text input refinement (login + filters) ── */
        div[data-testid="stTextInput"] input {
            background: #0f172a !important;
            border: 1px solid #2d3b50 !important;
            border-radius: 10px !important;
            color: #e2e8f0 !important;
            font-size: 0.9rem !important;
            padding: 0.6rem 0.8rem !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #22d3ee !important;
            box-shadow: 0 0 0 2px rgba(34,211,238,0.12) !important;
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: #475569 !important;
        }
        div[data-testid="stTextInput"] label {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            color: #8b9db8 !important;
            letter-spacing: 0.02em !important;
        }

        /* ── Primary button refinement ───────────────── */
        button[kind="primary"] {
            background: linear-gradient(135deg, #0891b2 0%, #22d3ee 100%) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #0f172a !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            transition: box-shadow 0.2s ease, transform 0.1s ease !important;
        }
        button[kind="primary"]:hover {
            box-shadow: 0 4px 16px rgba(34,211,238,0.25) !important;
            transform: translateY(-1px) !important;
        }
        button[kind="primary"]:active {
            transform: translateY(0) !important;
        }

        /* ── Transcript code block ─────────────────────── */
        div[data-testid='stCode'] {
            border: 1px solid #334155;
            border-radius: 10px;
            overflow: hidden;
        }
        div[data-testid='stCode'] pre {
            max-height: 420px;
            overflow-y: auto;
            background: #0f172a !important;
            color: #cbd5e1 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important;
            line-height: 1.7 !important;
            padding: 1rem 1.2rem !important;
        }
        div[data-testid='stCode'] pre::-webkit-scrollbar {
            width: 6px;
        }
        div[data-testid='stCode'] pre::-webkit-scrollbar-track {
            background: #1e293b;
        }
        div[data-testid='stCode'] pre::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 3px;
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


# ── Shared detail-panel helpers ──────────────────────────────────────────

FLAG_STYLES: dict[str, tuple[str, str]] = {
    "compliance_concern": ("background:#7f1d1d;color:#fca5a5;", "Compliance Concern"),
    "training_opportunity": ("background:#78350f;color:#fbbf24;", "Training Opportunity"),
    "exceptional_handling": ("background:#064e3b;color:#6ee7b7;", "Exceptional Handling"),
}


def val(obj: object) -> str:
    """Safe value display with 'n/a' fallback."""
    if obj is None:
        return "n/a"
    text = str(obj).strip()
    return text if text else "n/a"


def chart_title(label: str) -> None:
    """Render a styled chart section title."""
    st.markdown(
        f'<div class="chart-title">{_html.escape(label)}</div>',
        unsafe_allow_html=True,
    )


def section_divider(label: str) -> None:
    """Render a styled section divider with label."""
    st.markdown(
        f'<div style="margin:1.5rem 0 0.8rem 0;padding-bottom:0.4rem;'
        f'border-bottom:1px solid {COLORS["border"]};'
        f'font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:{COLORS["text_muted"]};">'
        f'{_html.escape(label)}</div>',
        unsafe_allow_html=True,
    )
