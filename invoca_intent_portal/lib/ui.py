"""Shared UI helpers for Streamlit pages."""

from __future__ import annotations

import html as _html
from typing import Any

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

# ── Intent / Outcome color maps ───────────────────────────────────────────

INTENT_COLORS: dict[str, tuple[str, str]] = {
    # (text_color, bg_color)
    "injury_new_case":     ("#34d399", "rgba(52,211,153,0.15)"),
    "property_only":       ("#f59e0b", "rgba(245,158,11,0.15)"),
    "already_represented": ("#a78bfa", "rgba(167,139,250,0.15)"),
    "insurance_inquiry":   ("#fb7185", "rgba(251,113,133,0.15)"),
    "existing_case":       ("#38bdf8", "rgba(56,189,248,0.15)"),
    "wrong_number":        ("#94a3b8", "rgba(148,163,184,0.10)"),
    "general_question":    ("#fbbf24", "rgba(251,191,36,0.15)"),
    "spam":                ("#64748b", "rgba(100,116,139,0.10)"),
    "other":               ("#94a3b8", "rgba(148,163,184,0.10)"),
}

OUTCOME_COLORS: dict[str, tuple[str, str]] = {
    "connected":       ("#34d399", "rgba(52,211,153,0.15)"),
    "callback_set":    ("#22d3ee", "rgba(34,211,238,0.15)"),
    "caller_declined": ("#f59e0b", "rgba(245,158,11,0.15)"),
    "not_applicable":  ("#94a3b8", "rgba(148,163,184,0.10)"),
    "caller_dropped":  ("#fb7185", "rgba(251,113,133,0.15)"),
    "wrong_number":    ("#64748b", "rgba(100,116,139,0.10)"),
    "other":           ("#94a3b8", "rgba(148,163,184,0.10)"),
}

SENTIMENT_COLORS: dict[str, tuple[str, str]] = {
    "positive":   ("#34d399", "rgba(52,211,153,0.15)"),
    "neutral":    ("#94a3b8", "rgba(148,163,184,0.10)"),
    "confused":   ("#f59e0b", "rgba(245,158,11,0.15)"),
    "frustrated": ("#fb7185", "rgba(251,113,133,0.15)"),
    "angry":      ("#ef4444", "rgba(239,68,68,0.15)"),
}


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
    "brand_confusion": ("background:#7f1d1d;color:#fca5a5;", "Brand Confusion"),
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


def _fmt(s: str) -> str:
    """Format snake_case DB values into readable labels."""
    return s.replace("_", " ").title() if s else s


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


def badge_pill(label: str, text_color: str, bg_color: str) -> str:
    """Return HTML for a colored badge pill."""
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'padding:3px 10px;border-radius:6px;font-size:0.78em;font-weight:500;'
        f'background:{bg_color};color:{text_color};'
        f'border:1px solid {text_color}22;">'
        f'{_html.escape(label)}</span>'
    )


def intent_pill(intent: str) -> str:
    """Badge pill for a caller_intent value."""
    tc, bg = INTENT_COLORS.get(intent, ("#94a3b8", "rgba(148,163,184,0.10)"))
    return badge_pill(_fmt(intent), tc, bg)


def outcome_pill(outcome: str) -> str:
    """Badge pill for a call_outcome value."""
    tc, bg = OUTCOME_COLORS.get(outcome, ("#94a3b8", "rgba(148,163,184,0.10)"))
    return badge_pill(_fmt(outcome), tc, bg)


def sentiment_pill(sentiment: str) -> str:
    """Badge pill for a caller_sentiment value."""
    tc, bg = SENTIMENT_COLORS.get(sentiment, ("#94a3b8", "rgba(148,163,184,0.10)"))
    return badge_pill(_fmt(sentiment), tc, bg)


def call_card(row: dict[str, Any], idx: int) -> None:
    """Render a compact call summary card with expander for details."""
    intent = str(row.get("caller_intent") or "other")
    situation = str(row.get("caller_situation") or "")
    outcome = str(row.get("call_outcome") or "other")
    confidence = row.get("intent_confidence")
    date_val = str(row.get("call_date_pt") or "")
    duration = row.get("duration_seconds") or ""
    sentiment = str(row.get("caller_sentiment") or "")
    brand_confused = row.get("brand_confusion", False)
    quality = row.get("agent_quality_score")

    # First key quote preview
    quotes = row.get("key_quotes")
    quote_preview = ""
    if quotes and isinstance(quotes, list) and quotes:
        q = quotes[0]
        if isinstance(q, dict):
            quote_preview = q.get("quote", "")
        else:
            quote_preview = str(q)
    if len(quote_preview) > 120:
        quote_preview = quote_preview[:117] + "..."

    # Truncate situation for card
    situation_short = situation[:140] + "..." if len(situation) > 140 else situation

    # Confidence color
    conf_str = str(confidence) if confidence is not None else "—"
    conf_color = "#34d399" if confidence and confidence >= 80 else (
        "#f59e0b" if confidence and confidence >= 60 else "#fb7185"
    )

    # Brand confusion indicator
    bc_dot = (
        f' <span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
        f'background:#fb7185;margin-left:4px;" title="Brand confusion"></span>'
        if brand_confused else ""
    )

    card_html = (
        f'<div style="background:linear-gradient(145deg,#1a2740 0%,#1e293b 60%,#222f43 100%);'
        f'border:1px solid #2d3b50;border-radius:12px;padding:0.8rem 1.1rem;'
        f'margin-bottom:0.15rem;">'
        # Row 1: intent pill + situation + date/duration
        f'<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:0.35rem;">'
        f'<div style="flex-shrink:0;">{intent_pill(intent)}{bc_dot}</div>'
        f'<div style="flex:1;font-size:0.85rem;color:{COLORS["text_primary"]};line-height:1.4;">'
        f'{_html.escape(situation_short)}</div>'
        f'<div style="flex-shrink:0;text-align:right;font-size:0.75rem;color:{COLORS["text_muted"]};">'
        f'{_html.escape(str(date_val))}<br>{_html.escape(str(duration))}s</div>'
        f'</div>'
    )

    # Row 2: quote preview + outcome + confidence
    if quote_preview:
        card_html += (
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="flex:1;font-size:0.8rem;color:{COLORS["text_secondary"]};'
            f'font-style:italic;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
            f'&ldquo;{_html.escape(quote_preview)}&rdquo;</div>'
            f'<div style="flex-shrink:0;display:flex;align-items:center;gap:8px;">'
            f'{outcome_pill(outcome)}'
            f'<span style="font-size:0.75rem;color:{conf_color};font-family:\'JetBrains Mono\',monospace;">'
            f'{conf_str}</span>'
            f'</div></div>'
        )
    else:
        card_html += (
            f'<div style="display:flex;justify-content:flex-end;gap:8px;align-items:center;">'
            f'{outcome_pill(outcome)}'
            f'<span style="font-size:0.75rem;color:{conf_color};font-family:\'JetBrains Mono\',monospace;">'
            f'{conf_str}</span>'
            f'</div>'
        )

    card_html += '</div>'
    st.markdown(card_html, unsafe_allow_html=True)


def call_detail_panel(row: dict[str, Any], call_detail: dict[str, Any] | None, idx: int = 0) -> None:
    """Render detail content inside an st.expander for a call."""
    intent = str(row.get("caller_intent") or "other")
    situation = str(row.get("caller_situation") or "No situation summary available.")
    outcome = str(row.get("call_outcome") or "other")
    sentiment = str(row.get("caller_sentiment") or "")
    case_type = str(row.get("case_type") or "")
    quality = row.get("agent_quality_score")
    brand_confused = row.get("brand_confusion", False)
    confidence = row.get("intent_confidence")
    flags = row.get("flags")
    quotes = row.get("key_quotes")
    signals = row.get("confusion_signals")

    # 1. Situation summary
    st.markdown(
        f'<div style="font-size:0.92rem;color:{COLORS["text_primary"]};line-height:1.5;'
        f'margin-bottom:0.8rem;">{_html.escape(situation)}</div>',
        unsafe_allow_html=True,
    )

    # 2. Key quotes (prominently)
    if quotes and isinstance(quotes, list) and len(quotes) > 0:
        section_divider("Key Quotes")
        _quote_style = (
            f'padding:0.6rem 1rem;margin:0.4rem 0;'
            f'border-left:3px solid {COLORS["accent"]};'
            f'background:linear-gradient(135deg,{COLORS["bg_elevated"]} 0%,#1e293b 100%);'
            f'border:1px solid #2d3b50;border-left:3px solid {COLORS["accent"]};'
            f'border-radius:0 10px 10px 0;'
            f'font-style:italic;color:{COLORS["text_primary"]};font-size:0.86rem;'
            f'line-height:1.6;'
        )
        for q in quotes:
            text = q.get("quote", "") if isinstance(q, dict) else str(q)
            ctx = q.get("context") if isinstance(q, dict) else None
            st.markdown(
                f'<div style="{_quote_style}">&ldquo;{_html.escape(text)}&rdquo;</div>',
                unsafe_allow_html=True,
            )
            if ctx:
                st.markdown(
                    f'<div style="font-size:0.74rem;color:{COLORS["text_muted"]};'
                    f'margin:-0.1rem 0 0.3rem 1.1rem;font-style:normal;">'
                    f'{_html.escape(str(ctx))}</div>',
                    unsafe_allow_html=True,
                )

    # 3. Analysis chips row
    section_divider("Analysis")
    chips = [
        intent_pill(intent),
        outcome_pill(outcome),
    ]
    if sentiment:
        chips.append(sentiment_pill(sentiment))
    if case_type and case_type != "not_applicable":
        chips.append(badge_pill(_fmt(case_type), "#38bdf8", "rgba(56,189,248,0.15)"))
    if quality is not None:
        q_color = "#34d399" if quality >= 7 else ("#f59e0b" if quality >= 5 else "#fb7185")
        chips.append(badge_pill(f"Quality: {quality}/10", q_color, f"{q_color}22"))
    if confidence is not None:
        c_color = "#34d399" if confidence >= 80 else ("#f59e0b" if confidence >= 60 else "#fb7185")
        chips.append(badge_pill(f"Conf: {confidence}%", c_color, f"{c_color}22"))
    if brand_confused:
        chips.append(badge_pill("Brand Confused", "#fca5a5", "rgba(127,29,29,0.5)"))

    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:0.3rem 0 0.8rem 0;">'
        f'{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )

    # 4. Flags
    if flags and isinstance(flags, list) and len(flags) > 0:
        _default_style = f"background:{COLORS['bg_elevated']};color:{COLORS['text_secondary']};"
        flag_html = " ".join(
            f'<span style="{FLAG_STYLES.get(f, (_default_style,))[0]}'
            f'padding:3px 10px;border-radius:6px;font-size:0.78em;font-weight:500;">'
            f'{_html.escape(FLAG_STYLES.get(f, (None, _fmt(f)))[1])}</span>'
            for f in flags
        )
        st.markdown(
            f'<div style="margin:0 0 0.6rem 0;"><span style="font-size:0.72rem;font-weight:600;'
            f'letter-spacing:0.06em;text-transform:uppercase;color:{COLORS["text_muted"]};'
            f'margin-right:8px;">FLAGS</span>{flag_html}</div>',
            unsafe_allow_html=True,
        )

    # 5. Confusion signals
    if signals and isinstance(signals, list) and len(signals) > 0:
        section_divider("Confusion Signals")
        for sig in signals:
            st.markdown(
                f'<div style="padding:0.4rem 0.8rem;margin:0.3rem 0;'
                f'border-left:3px solid {COLORS["rose"]};'
                f'background:rgba(251,113,133,0.06);'
                f'border-radius:0 8px 8px 0;'
                f'color:{COLORS["text_secondary"]};font-size:0.84rem;'
                f'line-height:1.5;">'
                f'{_html.escape(str(sig))}</div>',
                unsafe_allow_html=True,
            )

    # 6. Raw analysis JSON
    raw = row.get("raw_analysis")
    if raw:
        with st.expander("Raw Analysis JSON", expanded=False):
            import json
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    pass
            st.json(raw)
