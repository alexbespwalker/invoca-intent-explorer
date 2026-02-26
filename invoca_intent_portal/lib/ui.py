"""Shared UI helpers for Call Intent & Confusion Portal."""

from __future__ import annotations

import html as _html
from typing import Any

import plotly.graph_objects as go
import streamlit as st

# ── Color palette ─────────────────────────────────────────────────────────
COLORS = {
    "bg_primary": "#0f172a",
    "bg_surface": "#1e293b",
    "bg_elevated": "#273548",
    "border": "#334155",
    "border_subtle": "#1e293b",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent": "#22d3ee",
    "accent_dim": "#164e63",
    "amber": "#f59e0b",
    "amber_dim": "#78350f",
    "emerald": "#34d399",
    "rose": "#fb7185",
    "violet": "#a78bfa",
}

CHART_COLORS = [
    "#22d3ee", "#f59e0b", "#34d399", "#fb7185", "#a78bfa",
    "#38bdf8", "#fbbf24", "#6ee7b7", "#f472b6", "#818cf8",
]

# ── Intent / Outcome / Tone color maps (Walker Brain values) ─────────────

INTENT_COLORS: dict[str, tuple[str, str]] = {
    "seeking_representation":   ("#34d399", "rgba(52,211,153,0.15)"),
    "information_only":         ("#38bdf8", "rgba(56,189,248,0.15)"),
    "calling_for_someone_else": ("#a78bfa", "rgba(167,139,250,0.15)"),
    "follow_up":                ("#fbbf24", "rgba(251,191,36,0.15)"),
    "urgent_action":            ("#fb7185", "rgba(251,113,133,0.15)"),
    "trust_verification":       ("#f59e0b", "rgba(245,158,11,0.15)"),
    "cost_inquiry":             ("#22d3ee", "rgba(34,211,238,0.15)"),
    "referral":                 ("#6ee7b7", "rgba(110,231,183,0.15)"),
}

OUTCOME_COLORS: dict[str, tuple[str, str]] = {
    "referral-made":            ("#34d399", "rgba(52,211,153,0.15)"),
    "callback-requested":       ("#22d3ee", "rgba(34,211,238,0.15)"),
    "consultation-scheduled":   ("#a78bfa", "rgba(167,139,250,0.15)"),
    "not-qualified":            ("#f59e0b", "rgba(245,158,11,0.15)"),
    "information-only":         ("#94a3b8", "rgba(148,163,184,0.10)"),
    "other":                    ("#64748b", "rgba(100,116,139,0.10)"),
}

TONE_COLORS: dict[str, tuple[str, str]] = {
    "frustrated": ("#fb7185", "rgba(251,113,133,0.15)"),
    "neutral":    ("#94a3b8", "rgba(148,163,184,0.10)"),
    "confused":   ("#f59e0b", "rgba(245,158,11,0.15)"),
    "concerned":  ("#fbbf24", "rgba(251,191,36,0.15)"),
    "distressed": ("#ef4444", "rgba(239,68,68,0.15)"),
    "fearful":    ("#f472b6", "rgba(244,114,182,0.15)"),
    "anxious":    ("#818cf8", "rgba(129,140,248,0.15)"),
    "hopeful":    ("#34d399", "rgba(52,211,153,0.15)"),
    "angry":      ("#ef4444", "rgba(239,68,68,0.15)"),
    "relieved":   ("#6ee7b7", "rgba(110,231,183,0.15)"),
}


def apply_base_styles() -> None:
    """Apply dark-theme visual baseline."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            font-size: 2rem !important;
            color: #f1f5f9 !important;
        }
        h2, h3 {
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
            color: #cbd5e1 !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #64748b !important;
            font-size: 0.9rem !important;
        }
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
        div[data-testid="stDataFrame"] {
            border: 1px solid #2d3b50;
            border-radius: 12px;
            overflow: hidden;
            background: linear-gradient(180deg, #1a2740 0%, #1e293b 100%);
            box-shadow: 0 1px 4px rgba(0,0,0,0.15);
        }
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
        button[kind="secondary"] {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            color: #94a3b8 !important;
            font-weight: 500 !important;
            transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease !important;
        }
        button[kind="secondary"]:hover {
            border-color: #475569 !important;
            color: #e2e8f0 !important;
            background: #273548 !important;
        }
        details {
            border: 1px solid #2d3b50 !important;
            border-radius: 0 0 12px 12px !important;
            margin-top: -0.5rem !important;
            background: linear-gradient(180deg, #1a2740 0%, #1e293b 100%) !important;
        }
        details summary {
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: #94a3b8 !important;
            padding: 0.5rem 1rem !important;
        }
        details[open] {
            border-color: #3d4f69 !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
        }
        details[open] summary {
            border-bottom: 1px solid #2d3b50 !important;
            margin-bottom: 0.4rem !important;
        }
        textarea {
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important;
            line-height: 1.65 !important;
        }
        hr { border-color: #1e293b !important; }
        a { color: #22d3ee !important; }
        div[data-testid="stPlotlyChart"] {
            border: 1px solid #2d3b50;
            border-radius: 12px;
            padding: 0.8rem 0.8rem 0.4rem;
            background: linear-gradient(145deg, #1a2740 0%, #1e293b 60%, #1a2740 100%);
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.02);
        }
        div[data-testid="stPlotlyChart"]:hover {
            border-color: #3d4f69;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.02);
        }
        .chart-title {
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #8b9db8;
            margin: 1.2rem 0 0.25rem 0;
            padding-left: 4px;
        }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
        }
        button[data-testid="stDownloadButton"] {
            border-radius: 10px !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
        }
        div[data-testid="stSelectbox"] label {
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            color: #94a3b8 !important;
        }
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
        div[data-testid="stTextInput"] input::placeholder { color: #475569 !important; }
        div[data-testid="stTextInput"] label {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            color: #8b9db8 !important;
            letter-spacing: 0.02em !important;
        }
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
        div[data-testid='stCode'] pre::-webkit-scrollbar { width: 6px; }
        div[data-testid='stCode'] pre::-webkit-scrollbar-track { background: #1e293b; }
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


# ── Generic helpers ──────────────────────────────────────────────────────


def val(obj: object) -> str:
    """Safe value display with 'n/a' fallback."""
    if obj is None:
        return "n/a"
    text = str(obj).strip()
    return text if text else "n/a"


def _fmt(s: str) -> str:
    """Format snake_case / kebab-case DB values into readable labels."""
    return s.replace("_", " ").replace("-", " ").title() if s else s


def chart_title(label: str) -> None:
    """Render a styled chart section title."""
    st.markdown(
        f'<div class="chart-title">{_html.escape(label)}</div>',
        unsafe_allow_html=True,
    )


def section_divider(label: str) -> None:
    """Render a styled section divider with label."""
    st.markdown(
        f'<div style="margin:1.2rem 0 0.6rem 0;padding-bottom:0.35rem;'
        f'border-bottom:1px solid {COLORS["border"]};'
        f'font-size:0.72rem;font-weight:600;letter-spacing:0.08em;'
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
    """Badge pill for a primary_intent value."""
    tc, bg = INTENT_COLORS.get(intent, ("#94a3b8", "rgba(148,163,184,0.10)"))
    return badge_pill(_fmt(intent), tc, bg)


def outcome_pill(outcome: str) -> str:
    """Badge pill for an outcome value."""
    tc, bg = OUTCOME_COLORS.get(outcome, ("#94a3b8", "rgba(148,163,184,0.10)"))
    return badge_pill(_fmt(outcome), tc, bg)


def tone_pill(tone: str) -> str:
    """Badge pill for an emotional_tone value."""
    tc, bg = TONE_COLORS.get(tone, ("#94a3b8", "rgba(148,163,184,0.10)"))
    return badge_pill(_fmt(tone), tc, bg)


# ── Call card + detail panel ─────────────────────────────────────────────


def call_card(row: dict[str, Any], idx: int) -> None:
    """Render a call summary card (situation-dominant)."""
    topic = str(row.get("primary_topic") or "")
    intent = str(row.get("primary_intent") or "other")
    outcome = str(row.get("outcome") or "other")
    date_val = str(row.get("call_date") or "")
    duration = row.get("call_duration_seconds") or ""
    confused = row.get("category_confusion", False)

    topic_short = topic[:200] + "..." if len(topic) > 200 else topic

    bc_badge = ""
    if confused:
        bc_badge = (
            ' <span style="display:inline-flex;align-items:center;padding:2px 8px;'
            'border-radius:5px;font-size:0.72em;font-weight:500;'
            'background:rgba(251,113,133,0.15);color:#fb7185;'
            'border:1px solid #fb718533;">Confused</span>'
        )

    card_html = (
        f'<div style="background:linear-gradient(145deg,#1a2740 0%,#1e293b 60%,#222f43 100%);'
        f'border:1px solid #2d3b50;border-radius:12px;padding:0.85rem 1.1rem;'
        f'margin-bottom:0.5rem;">'
        f'<div style="font-size:0.92rem;color:{COLORS["text_primary"]};line-height:1.45;'
        f'margin-bottom:0.4rem;">'
        f'{_html.escape(topic_short)}</div>'
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
        f'{intent_pill(intent)}{bc_badge}'
        f'<span style="flex:1;"></span>'
        f'<span style="font-size:0.76rem;color:{COLORS["text_secondary"]};font-variant-numeric:tabular-nums;">'
        f'{_html.escape(str(date_val))}  \u00b7  {_html.escape(str(duration))}s</span>'
        f'{outcome_pill(outcome)}'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def call_detail_panel(row: dict[str, Any], idx: int = 0) -> None:
    """Render detail content inside an st.expander for a call."""
    summary = str(row.get("summary") or "")
    intent = str(row.get("primary_intent") or "other")
    outcome = str(row.get("outcome") or "other")
    tone = str(row.get("emotional_tone") or "")
    case_type = str(row.get("case_type") or "")
    quality = row.get("quality_score")
    confidence = row.get("confidence_score")
    confused = row.get("category_confusion", False)
    key_quote = row.get("key_quote")
    confusion_points = row.get("process_confusion_points")
    brands_mentioned = row.get("other_brands_mentioned")
    channel = row.get("channel_referenced")
    empathy = row.get("agent_empathy_score")
    education = row.get("agent_education_quality")
    closing = row.get("agent_closing_effectiveness")
    needs_review = row.get("needs_review", False)
    review_reason = row.get("review_reason")

    # 1. Summary
    if summary:
        st.markdown(
            f'<div style="font-size:0.92rem;color:{COLORS["text_primary"]};line-height:1.5;'
            f'margin-bottom:0.8rem;">{_html.escape(summary)}</div>',
            unsafe_allow_html=True,
        )

    # 2. Key quote
    if key_quote:
        section_divider("Key Quote")
        st.markdown(
            f'<div style="padding:0.6rem 1rem;margin:0.4rem 0;'
            f'border-left:3px solid {COLORS["accent"]};'
            f'background:linear-gradient(135deg,{COLORS["bg_elevated"]} 0%,#1e293b 100%);'
            f'border:1px solid #2d3b50;border-left:3px solid {COLORS["accent"]};'
            f'border-radius:0 10px 10px 0;'
            f'font-style:italic;color:{COLORS["text_primary"]};font-size:0.86rem;'
            f'line-height:1.6;">&ldquo;{_html.escape(str(key_quote))}&rdquo;</div>',
            unsafe_allow_html=True,
        )

    # 3. Analysis chips
    section_divider("Analysis")
    chips = [intent_pill(intent), outcome_pill(outcome)]
    if tone:
        chips.append(tone_pill(tone))
    if case_type:
        chips.append(badge_pill(_fmt(case_type), "#38bdf8", "rgba(56,189,248,0.15)"))
    if quality is not None:
        q_color = "#34d399" if quality >= 70 else ("#f59e0b" if quality >= 50 else "#fb7185")
        chips.append(badge_pill(f"Quality: {quality}/100", q_color, f"{q_color}22"))
    if confidence is not None:
        c_val = float(confidence)
        if c_val <= 1:
            c_color = "#34d399" if c_val >= 0.8 else ("#f59e0b" if c_val >= 0.6 else "#fb7185")
            chips.append(badge_pill(f"Conf: {c_val:.0%}", c_color, f"{c_color}22"))
        else:
            c_color = "#34d399" if c_val >= 80 else ("#f59e0b" if c_val >= 60 else "#fb7185")
            chips.append(badge_pill(f"Conf: {c_val:.0f}%", c_color, f"{c_color}22"))
    if confused:
        chips.append(badge_pill("Confused", "#fca5a5", "rgba(127,29,29,0.5)"))

    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:0.3rem 0 0.8rem 0;">'
        f'{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )

    # 4. Confusion section
    if confused:
        section_divider("Category Confusion")
        if brands_mentioned and isinstance(brands_mentioned, list) and len(brands_mentioned) > 0:
            brand_pills = " ".join(
                badge_pill(str(b), "#f59e0b", "rgba(245,158,11,0.15)")
                for b in brands_mentioned if b
            )
            st.markdown(
                f'<div style="margin:0.4rem 0;"><span style="font-size:0.74rem;font-weight:600;'
                f'letter-spacing:0.06em;text-transform:uppercase;color:{COLORS["text_muted"]};'
                f'margin-right:8px;">Brands Mentioned</span>{brand_pills}</div>',
                unsafe_allow_html=True,
            )
        if confusion_points and isinstance(confusion_points, list) and len(confusion_points) > 0:
            for point in (p for p in confusion_points if p):
                st.markdown(
                    f'<div style="padding:0.4rem 0.8rem;margin:0.3rem 0;'
                    f'border-left:3px solid {COLORS["rose"]};'
                    f'background:rgba(251,113,133,0.06);'
                    f'border-radius:0 8px 8px 0;'
                    f'color:{COLORS["text_secondary"]};font-size:0.84rem;'
                    f'line-height:1.5;">'
                    f'{_html.escape(str(point))}</div>',
                    unsafe_allow_html=True,
                )
        if channel:
            st.markdown(
                f'<div style="margin:0.4rem 0;"><span style="font-size:0.74rem;font-weight:600;'
                f'letter-spacing:0.06em;text-transform:uppercase;color:{COLORS["text_muted"]};'
                f'margin-right:8px;">Channel</span>'
                f'{badge_pill(_fmt(str(channel)), "#22d3ee", "rgba(34,211,238,0.15)")}</div>',
                unsafe_allow_html=True,
            )

    # 5. Agent performance
    if any(v is not None for v in (empathy, education, closing)):
        section_divider("Agent Performance")
        agent_chips = []
        for label, score in [("Empathy", empathy), ("Education", education), ("Closing", closing)]:
            if score is not None:
                s_color = "#34d399" if score >= 7 else ("#f59e0b" if score >= 5 else "#fb7185")
                agent_chips.append(badge_pill(f"{label}: {score}/10", s_color, f"{s_color}22"))
        st.markdown(
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:0.3rem 0 0.6rem 0;">'
            f'{"".join(agent_chips)}</div>',
            unsafe_allow_html=True,
        )

    # 6. Needs review
    if needs_review:
        review_html = (
            f'<div style="margin:0.5rem 0;padding:0.5rem 0.8rem;'
            f'border:1px solid {COLORS["amber"]};border-radius:8px;'
            f'background:rgba(245,158,11,0.08);">'
            f'<span style="font-size:0.74rem;font-weight:600;color:{COLORS["amber"]};">'
            f'NEEDS REVIEW</span>'
        )
        if review_reason:
            review_html += (
                f'<br><span style="font-size:0.82rem;color:{COLORS["text_secondary"]};">'
                f'{_html.escape(str(review_reason))}</span>'
            )
        review_html += '</div>'
        st.markdown(review_html, unsafe_allow_html=True)
