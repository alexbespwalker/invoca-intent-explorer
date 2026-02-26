"""Call Intent & Confusion Portal — powered by Walker Brain analysis."""

from __future__ import annotations

from datetime import datetime, timedelta
import html as _html
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as _components

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.auth import check_password, logout
from invoca_intent_portal.lib.supabase_client import require_supabase_client
from invoca_intent_portal.lib.db import get_calls, get_transcript
from invoca_intent_portal.lib.ui import (
    apply_base_styles, apply_chart_defaults, chart_title, COLORS,
    section_divider, call_card, call_detail_panel, _fmt, badge_pill,
    INTENT_COLORS, OUTCOME_COLORS, TONE_COLORS,
)


st.set_page_config(
    page_title="Call Intent & Confusion Portal",
    page_icon="\U0001F4DE",
    layout="wide",
)
apply_base_styles()
check_password()

# ── Header ───────────────────────────────────────────────────────────────
st.markdown(
    '<div style="height:3px;background:linear-gradient(90deg,#22d3ee 0%,#0ea5e9 40%,#a78bfa 70%,#f59e0b 100%);'
    'border-radius:2px;margin-bottom:0.8rem;opacity:0.9;"></div>',
    unsafe_allow_html=True,
)
st.title("Call Intent & Confusion Portal")
st.caption("Caller intent  \u2022  category confusion  \u2022  agent quality")

client = require_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

# ── Sidebar: filters ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:600;letter-spacing:0.1em;'
        'text-transform:uppercase;color:#64748b;margin-bottom:0.8rem;">'
        'Walker Advertising</div>',
        unsafe_allow_html=True,
    )

    _user_display = st.session_state.get("user_display_name") or st.session_state.get("user_email")
    if _user_display:
        st.markdown(
            f'<div style="font-size:0.78rem;color:{COLORS["text_secondary"]};'
            f'margin-bottom:0.3rem;">'
            f'{_html.escape(str(_user_display))}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="logout_btn"):
            logout()
        st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)

    st.header("Filters")

    date_preset = st.selectbox(
        "Date Range",
        options=["Yesterday", "Last 7 Days", "Last 14 Days", "Last 30 Days", "Custom"],
        index=2,
    )

    if date_preset == "Yesterday":
        start_date = pt_today - timedelta(days=1)
        end_date = start_date
    elif date_preset == "Last 7 Days":
        start_date = pt_today - timedelta(days=6)
        end_date = pt_today
    elif date_preset == "Last 14 Days":
        start_date = pt_today - timedelta(days=13)
        end_date = pt_today
    elif date_preset == "Last 30 Days":
        start_date = pt_today - timedelta(days=29)
        end_date = pt_today
    else:
        date_range = st.date_input(
            "Date Range (PT)",
            value=(pt_today - timedelta(days=13), pt_today),
            max_value=pt_today,
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range[0], date_range[1]
        else:
            start_date = pt_today - timedelta(days=13)
            end_date = pt_today

    confusion_filter = st.radio(
        "Category Confusion",
        options=["All", "Confused Only", "Not Confused"],
        index=0,
        horizontal=True,
    )

    intent_filter = st.multiselect(
        "Intent",
        options=list(INTENT_COLORS.keys()),
        format_func=_fmt,
        default=[],
    )

    outcome_filter = st.multiselect(
        "Outcome",
        options=list(OUTCOME_COLORS.keys()),
        format_func=_fmt,
        default=[],
    )

    quality_range = st.slider("Quality Score", min_value=0, max_value=100, value=(0, 100))

    language_filter = st.selectbox(
        "Language",
        options=["All", "English", "Spanish", "Bilingual"],
        index=0,
    )

    st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading data..."):
        df = get_calls(client, start_date=start_date, end_date=end_date)
except Exception:
    st.error("Error loading data. Please try again or check your filters.")
    st.stop()

if df.empty:
    st.warning("No calls found for this date range.")
    st.stop()

# ── Apply filters ────────────────────────────────────────────────────────
if confusion_filter == "Confused Only":
    df = df[df["category_confusion"].fillna(False) == True]  # noqa: E712
elif confusion_filter == "Not Confused":
    df = df[df["category_confusion"].fillna(False) == False]  # noqa: E712

if intent_filter:
    df = df[df["primary_intent"].isin(intent_filter)]

if outcome_filter:
    df = df[df["outcome"].isin(outcome_filter)]

if quality_range != (0, 100):
    df = df[df["quality_score"].fillna(0).between(quality_range[0], quality_range[1])]

if language_filter != "All":
    _lang_map = {
        "English": ["en", "english"],
        "Spanish": ["es", "spanish"],
        "Bilingual": ["bilingual", "both"],
    }
    _valid_langs = _lang_map.get(language_filter, [language_filter.lower()])
    df = df[df["original_language"].fillna("").str.lower().isin(_valid_langs)]

if df.empty:
    st.warning("No calls match the current filters.")
    st.stop()

# ── Metrics ──────────────────────────────────────────────────────────────
total = len(df)
confused_count = int(df["category_confusion"].fillna(False).sum())
confusion_rate = confused_count / total * 100 if total else 0
referral_count = int((df["outcome"] == "referral-made").sum())
referral_rate = referral_count / total * 100 if total else 0
avg_quality = df["quality_score"].dropna().mean()

# ── KPI Strip ────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Calls", f"{total:,}")
m2.metric("Confusion Rate", f"{confusion_rate:.1f}%")
m3.metric("Referral Rate", f"{referral_rate:.1f}%")
m4.metric("Avg Quality", f"{avg_quality:.0f}/100" if pd.notna(avg_quality) else "n/a")

_components.html("""
<script>
(function colorKPI() {
    const colors = ['#22d3ee','#fb7185','#34d399','#f59e0b'];
    const metrics = window.parent.document.querySelectorAll('[data-testid="stMetric"]');
    metrics.forEach((m, i) => {
        if (i < colors.length) m.style.borderLeftColor = colors[i];
    });
    if (metrics.length < 4) setTimeout(colorKPI, 500);
})();
</script>
""", height=0)

# ── Charts Row 1: Intent Breakdown + Outcome Distribution ───────────────
c1, c2 = st.columns(2)

with c1:
    chart_title("Intent Breakdown")
    intent_data = (
        df["primary_intent"]
        .fillna("other")
        .value_counts()
        .rename_axis("intent")
        .reset_index(name="count")
    )
    intent_data["label"] = intent_data["intent"].apply(_fmt)
    bar_colors = [
        INTENT_COLORS.get(v, ("#94a3b8", ""))[0] for v in intent_data["intent"]
    ]
    fig_intent = px.bar(intent_data, y="label", x="count", orientation="h")
    fig_intent.update_traces(
        marker_color=bar_colors,
        marker_cornerradius=4,
        text=intent_data["count"],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    )
    apply_chart_defaults(fig_intent)
    fig_intent.update_layout(
        yaxis_title=None, xaxis_title=None,
        yaxis=dict(automargin=True, tickfont=dict(color="#94a3b8", size=11)),
        margin=dict(l=10, t=10, b=40, r=50),
        showlegend=False,
        height=320,
    )
    st.plotly_chart(fig_intent, use_container_width=True)

with c2:
    chart_title("Outcome Distribution")
    outcome_data = (
        df["outcome"]
        .fillna("other")
        .value_counts()
        .rename_axis("outcome")
        .reset_index(name="count")
    )
    outcome_data["label"] = outcome_data["outcome"].apply(_fmt)
    bar_colors = [
        OUTCOME_COLORS.get(v, ("#94a3b8", ""))[0] for v in outcome_data["outcome"]
    ]
    fig_outcome = px.bar(outcome_data, y="label", x="count", orientation="h")
    fig_outcome.update_traces(
        marker_color=bar_colors,
        marker_cornerradius=4,
        text=outcome_data["count"],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    )
    apply_chart_defaults(fig_outcome)
    fig_outcome.update_layout(
        yaxis_title=None, xaxis_title=None,
        yaxis=dict(automargin=True, tickfont=dict(color="#94a3b8", size=11)),
        margin=dict(l=10, t=10, b=40, r=50),
        showlegend=False,
        height=320,
    )
    st.plotly_chart(fig_outcome, use_container_width=True)

# ── Charts Row 2: Confusion x Intent + Emotional Tone ───────────────────
c3, c4 = st.columns(2)

with c3:
    chart_title("Confusion Rate by Intent")
    intent_confusion = (
        df.groupby("primary_intent")
        .agg(
            total=("id", "count"),
            confused=("category_confusion", lambda x: x.fillna(False).sum()),
        )
        .reset_index()
    )
    intent_confusion["rate"] = (
        intent_confusion["confused"] / intent_confusion["total"] * 100
    ).round(1)
    intent_confusion["label"] = intent_confusion["primary_intent"].apply(_fmt)
    intent_confusion = intent_confusion.sort_values("rate", ascending=True)

    fig_conf = px.bar(intent_confusion, y="label", x="rate", orientation="h")
    fig_conf.update_traces(
        marker_color="#fb7185",
        marker_cornerradius=4,
        text=intent_confusion["rate"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    )
    apply_chart_defaults(fig_conf)
    fig_conf.update_layout(
        yaxis_title=None, xaxis_title="Confusion %",
        yaxis=dict(automargin=True, tickfont=dict(color="#94a3b8", size=11)),
        margin=dict(l=10, t=10, b=40, r=60),
        showlegend=False,
        height=320,
    )
    st.plotly_chart(fig_conf, use_container_width=True)

with c4:
    chart_title("Emotional Tone")
    tone_data = (
        df["emotional_tone"]
        .fillna("unknown")
        .value_counts()
        .rename_axis("tone")
        .reset_index(name="count")
    )
    tone_data["label"] = tone_data["tone"].apply(_fmt)
    bar_colors = [
        TONE_COLORS.get(v, ("#94a3b8", ""))[0] for v in tone_data["tone"]
    ]
    fig_tone = px.bar(tone_data, y="label", x="count", orientation="h")
    fig_tone.update_traces(
        marker_color=bar_colors,
        marker_cornerradius=4,
        text=tone_data["count"],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    )
    apply_chart_defaults(fig_tone)
    fig_tone.update_layout(
        yaxis_title=None, xaxis_title=None,
        yaxis=dict(automargin=True, tickfont=dict(color="#94a3b8", size=11)),
        margin=dict(l=10, t=10, b=40, r=50),
        showlegend=False,
        height=320,
    )
    st.plotly_chart(fig_tone, use_container_width=True)

# ── Call List ────────────────────────────────────────────────────────────
st.markdown(
    '<div style="height:1px;margin:1.2rem 0 0.8rem;background:#334155;"></div>',
    unsafe_allow_html=True,
)

active_filters = []
if confusion_filter != "All":
    active_filters.append(confusion_filter)
if intent_filter:
    active_filters.append(f"Intent: {', '.join(_fmt(i) for i in intent_filter)}")
if outcome_filter:
    active_filters.append(f"Outcome: {', '.join(_fmt(o) for o in outcome_filter)}")
if quality_range != (0, 100):
    active_filters.append(f"Quality: {quality_range[0]}\u2013{quality_range[1]}")
if language_filter != "All":
    active_filters.append(f"Language: {language_filter}")
if active_filters:
    st.markdown(
        f'<div style="font-size:0.78rem;color:{COLORS["accent"]};margin-bottom:0.3rem;">'
        f'Active filters: {_html.escape(" + ".join(active_filters))}</div>',
        unsafe_allow_html=True,
    )

section_divider(f"Calls ({total})")

df = df.sort_values("call_start_date", ascending=False)

# Pagination
PAGE_SIZE = 25
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

_filter_key = (
    f"{start_date}|{end_date}|{confusion_filter}|"
    f"{','.join(sorted(intent_filter))}|{','.join(sorted(outcome_filter))}|"
    f"{quality_range}|{language_filter}"
)
if st.session_state.get("_filter_key") != _filter_key:
    st.session_state["_filter_key"] = _filter_key
    st.session_state["page"] = 0
if "page" not in st.session_state:
    st.session_state["page"] = 0
if st.session_state["page"] >= total_pages:
    st.session_state["page"] = 0

col_prev, col_info, col_next = st.columns([1, 3, 1])
with col_prev:
    if st.button("\u2190 Prev", disabled=st.session_state["page"] <= 0):
        st.session_state["page"] -= 1
        st.rerun()
with col_info:
    st.markdown(
        f'<div style="text-align:center;font-size:0.8rem;color:{COLORS["text_muted"]};'
        f'padding-top:0.4rem;">Page {st.session_state["page"] + 1} of {total_pages}</div>',
        unsafe_allow_html=True,
    )
with col_next:
    if st.button("Next \u2192", disabled=st.session_state["page"] >= total_pages - 1):
        st.session_state["page"] += 1
        st.rerun()

page_start = st.session_state["page"] * PAGE_SIZE
page_end = min(page_start + PAGE_SIZE, total)
page_df = df.iloc[page_start:page_end]

for idx, (_, row) in enumerate(page_df.iterrows()):
    row_dict = row.to_dict()
    call_card(row_dict, page_start + idx)

    with st.expander("Details", expanded=False):
        call_detail_panel(row_dict, page_start + idx)

        call_id = row_dict.get("id")
        if call_id is not None:
            tx_key = f"show_tx_{page_start + idx}_{call_id}"
            if st.button("Load transcript", key=f"txbtn_{page_start + idx}_{call_id}"):
                st.session_state[tx_key] = True
            if st.session_state.get(tx_key):
                transcript = get_transcript(client, int(call_id))
                if transcript:
                    wc = len(transcript.split())
                    st.markdown(
                        f'<div style="font-size:0.73rem;color:#64748b;margin-bottom:0.3rem;'
                        f"font-family:'JetBrains Mono',monospace;\">"
                        f'{wc:,} words</div>',
                        unsafe_allow_html=True,
                    )
                    st.code(transcript, language=None, wrap_lines=True)
                else:
                    st.warning("No transcript available.")

# ── CSV Export ───────────────────────────────────────────────────────────
with st.sidebar:
    export_cols = [
        "source_transcript_id", "call_date", "primary_intent", "primary_topic",
        "outcome", "emotional_tone", "quality_score", "category_confusion",
        "case_type", "call_duration_seconds", "original_language",
    ]
    existing = [c for c in export_cols if c in df.columns]
    export_df = df[existing].copy()
    for col in ["primary_intent", "outcome", "emotional_tone", "case_type"]:
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda v: _fmt(str(v)) if pd.notna(v) else ""
            )
    export_df.columns = [_fmt(c) for c in export_df.columns]

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "\U0001F4E5 Export CSV",
        data=csv_bytes,
        file_name=f"calls_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
