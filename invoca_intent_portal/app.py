"""Invoca Intent Explorer — home page."""

from __future__ import annotations

from datetime import datetime, timedelta
import html as _html
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.auth import check_password
from invoca_intent_portal.lib.supabase_client import require_supabase_client
from invoca_intent_portal.lib.db import get_analyzed_calls, get_brands, get_call_detail
from invoca_intent_portal.lib.ui import apply_base_styles, apply_chart_defaults, CHART_COLORS


def _fmt(val: str) -> str:
    """Format snake_case DB values into readable labels."""
    return val.replace("_", " ").title() if val else val

st.set_page_config(
    page_title="Invoca Intent Explorer",
    page_icon="\U0001F4DE",
    layout="wide",
)
apply_base_styles()
check_password()

st.markdown(
    '<div style="height:3px;background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
    'border-radius:2px;margin-bottom:1rem;"></div>',
    unsafe_allow_html=True,
)
st.title("Invoca Intent Explorer")
st.caption("BC call analysis  \u2022  caller intent  \u2022  brand confusion  \u2022  agent quality")

client = require_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

# ── Sidebar: 2 filters ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:600;letter-spacing:0.1em;'
        'text-transform:uppercase;color:#64748b;margin-bottom:1.5rem;">'
        'Walker Advertising</div>',
        unsafe_allow_html=True,
    )
    st.header("Filters")

    date_preset = st.selectbox(
        "Date Range",
        options=["Yesterday", "Last 7 Days", "Last 14 Days", "Custom"],
        index=1,
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

    brands = get_brands(client)
    brand_options = ["ALL"] + [b["brand_code"] for b in brands]
    brand_labels = {"ALL": "All Brands"}
    for b in brands:
        brand_labels[b["brand_code"]] = f"{b['brand_code']} - {b['brand_name']}"

    selected_brand = st.selectbox(
        "Brand",
        options=brand_options,
        index=0,
        format_func=lambda x: brand_labels.get(x, x),
    )

    brand_filter = None if selected_brand == "ALL" else selected_brand

# ── Load data ────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading data..."):
        calls_df = get_analyzed_calls(
            client,
            start_date=start_date,
            end_date=end_date,
            brand_code=brand_filter,
            limit=5000,
        )
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if calls_df.empty:
    st.warning("No calls found for this filter window.")
    st.stop()

# ── KPI row (4 metrics) ─────────────────────────────────────────────────
analyzed_mask = calls_df["caller_intent"].notna()
analyzed_count = int(analyzed_mask.sum())
total_count = len(calls_df)

confusion_rate = 0.0
if analyzed_count > 0:
    confusion_rate = float(
        calls_df.loc[analyzed_mask, "brand_confusion"].fillna(False).mean() * 100
    )

avg_quality = 0.0
if "agent_quality_score" in calls_df.columns:
    quality_vals = calls_df["agent_quality_score"].dropna()
    if len(quality_vals) > 0:
        avg_quality = float(quality_vals.mean())

top_intent = "n/a"
top_intent_pct = ""
if analyzed_count > 0:
    intent_counts = calls_df.loc[analyzed_mask, "caller_intent"].value_counts()
    if not intent_counts.empty:
        raw_intent = str(intent_counts.index[0])
        top_intent = raw_intent.replace("_", " ").title()
        # Abbreviate long intents for the KPI card
        _abbrev = {"New Case Inquiry": "New Case", "Existing Case Status": "Existing"}
        top_intent = _abbrev.get(top_intent, top_intent)
        top_intent_pct = f"{intent_counts.iloc[0] / analyzed_count * 100:.0f}%"

repo_success_rate = "n/a"
if "agent_repositioning_attempted" in calls_df.columns:
    attempted = calls_df["agent_repositioning_attempted"].fillna(False)
    successful = calls_df.get("agent_repositioning_successful", pd.Series(dtype=bool)).fillna(False)
    attempted_count = int(attempted.sum())
    if attempted_count > 0:
        repo_success_rate = f"{successful.sum() / attempted_count * 100:.0f}%"

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Calls", f"{total_count:,}")
m2.metric("Confusion Rate", f"{confusion_rate:.1f}%")
m3.metric("Avg Quality", f"{avg_quality:.1f}" if avg_quality else "n/a")
m4.metric("Top Intent", top_intent, delta=top_intent_pct if top_intent_pct else None)
m5.metric("Repo Success", repo_success_rate)

# ── Charts (2 columns) ──────────────────────────────────────────────────
chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    st.subheader("Intent Distribution")
    if analyzed_count > 0:
        pie_data = (
            calls_df.loc[analyzed_mask, "caller_intent"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("caller_intent")
            .reset_index(name="count")
        )
        pie_data["label"] = pie_data["caller_intent"].apply(_fmt)
        # Build explicit color mapping so pie slices get our palette
        label_names = pie_data["label"].tolist()
        label_color_map = {n: CHART_COLORS[i % len(CHART_COLORS)] for i, n in enumerate(label_names)}
        fig_pie = px.pie(
            pie_data, names="label", values="count", hole=0.45,
            color="label", color_discrete_map=label_color_map,
        )
        apply_chart_defaults(fig_pie)
        fig_pie.update_traces(textfont_color="#e2e8f0", textfont_size=12)
        fig_pie.update_layout(legend_title_text="")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No analyzed calls in current window.")

with chart_col_2:
    st.subheader("Outcome Breakdown")
    if "call_outcome" in calls_df.columns and calls_df["call_outcome"].notna().any():
        out_data = (
            calls_df["call_outcome"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("call_outcome")
            .reset_index(name="count")
        )
        out_data["label"] = out_data["call_outcome"].apply(_fmt)
        fig_out = px.bar(
            out_data, y="label", x="count", orientation="h",
            color_discrete_sequence=[CHART_COLORS[0]],
        )
        apply_chart_defaults(fig_out)
        fig_out.update_layout(yaxis_title=None, xaxis_title=None, margin=dict(l=180, t=20, b=40, r=20))
        fig_out.update_traces(marker_cornerradius=4)
        st.plotly_chart(fig_out, use_container_width=True)
    else:
        st.info("No analyzed outcomes in current window.")

# ── Case Type + Daily Trend (2 columns) ──────────────────────────────────
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Case Type Distribution")
    if "case_type" in calls_df.columns and calls_df["case_type"].notna().any():
        case_data = (
            calls_df["case_type"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("case_type")
            .reset_index(name="count")
        )
        case_data["label"] = case_data["case_type"].apply(_fmt)
        fig_case = px.bar(
            case_data, y="label", x="count", orientation="h",
            color_discrete_sequence=[CHART_COLORS[1]],
        )
        apply_chart_defaults(fig_case)
        fig_case.update_layout(yaxis_title=None, xaxis_title=None, margin=dict(l=180, t=20, b=40, r=20))
        fig_case.update_traces(marker_cornerradius=4)
        st.plotly_chart(fig_case, use_container_width=True)
    else:
        st.info("No case type data in current window.")

with row2_col2:
    st.subheader("Daily Intent Trend")
    if analyzed_count > 0:
        trend_base = calls_df.loc[analyzed_mask].copy()
        trend_base["call_date"] = pd.to_datetime(
            trend_base["call_date_pt"], errors="coerce"
        )
        trend_df = (
            trend_base.groupby(["call_date", "caller_intent"], as_index=False)
            .size()
            .rename(columns={"size": "calls"})
        )
        trend_df["intent_label"] = trend_df["caller_intent"].apply(_fmt)
        fig_trend = px.line(
            trend_df, x="call_date", y="calls", color="intent_label",
            color_discrete_sequence=CHART_COLORS, markers=True,
        )
        apply_chart_defaults(fig_trend)
        fig_trend.update_layout(yaxis_title="Calls", xaxis_title="", legend_title_text="")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No analyzed data for trend chart.")

# ── Call table ───────────────────────────────────────────────────────────
st.subheader("Call Table")
st.caption("Select a row to preview its transcript below.")

# Extract first key quote as intent quote
if "key_quotes" in calls_df.columns:
    calls_df["intent_quote"] = calls_df["key_quotes"].apply(
        lambda q: q[0]["quote"] if isinstance(q, list) and q and isinstance(q[0], dict) and "quote" in q[0] else ""
    )
else:
    calls_df["intent_quote"] = ""

show_cols = [
    "invoca_call_id", "call_date_pt", "caller_intent",
    "intent_quote", "intent_confidence", "brand_confusion",
    "agent_quality_score", "call_outcome", "case_type",
    "agent_repositioning_successful", "caller_sentiment",
    "duration_seconds",
]
existing_cols = [c for c in show_cols if c in calls_df.columns]
display_df = calls_df[existing_cols].copy()

# Format snake_case values in key columns
for col in ["caller_intent", "call_outcome", "case_type", "caller_sentiment"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda v: _fmt(str(v)) if pd.notna(v) else "")

# Rename columns to human-readable headers
display_df = display_df.rename(columns={
    "invoca_call_id": "Call ID",
    "call_date_pt": "Date",
    "caller_intent": "Intent",
    "intent_quote": "Intent Quote",
    "intent_confidence": "Confidence",
    "brand_confusion": "Brand Confused",
    "agent_quality_score": "Quality",
    "call_outcome": "Outcome",
    "case_type": "Case Type",
    "agent_repositioning_successful": "Repo OK",
    "caller_sentiment": "Sentiment",
    "duration_seconds": "Duration (s)",
})

# Map display rows back to DB IDs for on-click lookup
row_id_map = calls_df.loc[display_df.index, "id"].tolist()

selection = st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

# ── Inline transcript panel ──────────────────────────────────────────
if selection.selection.rows:
    selected_idx = selection.selection.rows[0]
    selected_call_id = str(row_id_map[selected_idx])
    selected_row = display_df.iloc[selected_idx]

    call_detail, _ = get_call_detail(client, selected_call_id)

    if call_detail and call_detail.get("transcript_text"):
        st.markdown(
            '<div style="height:2px;margin:1.5rem 0 1rem 0;'
            'background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
            'border-radius:1px;opacity:0.5;"></div>',
            unsafe_allow_html=True,
        )

        # Section label
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;'
            'text-transform:uppercase;color:#64748b;margin-bottom:0.5rem;">'
            'Transcript Preview</div>',
            unsafe_allow_html=True,
        )

        # Metadata header bar — single styled card header
        call_label = _html.escape(str(selected_row.get("Call ID", selected_call_id)))
        call_date = _html.escape(str(selected_row.get("Date", "")))
        call_intent = _html.escape(str(selected_row.get("Intent", "")))
        call_dur = _html.escape(str(selected_row.get("Duration (s)", "")))

        st.markdown(
            f'<div style="display:flex;gap:2rem;align-items:center;'
            f'background:linear-gradient(135deg,#1e293b 0%,#273548 100%);'
            f'border:1px solid #334155;border-radius:12px;'
            f'padding:0.8rem 1.2rem;margin-bottom:0.8rem;">'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Call ID</span><br>'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.88rem;'
            f'color:#22d3ee;">{call_label}</span></div>'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Date</span><br>'
            f'<span style="font-size:0.88rem;color:#e2e8f0;">{call_date}</span></div>'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Intent</span><br>'
            f'<span style="display:inline-block;margin-top:2px;padding:1px 8px;'
            f'background:#164e6380;border-radius:5px;font-size:0.84rem;'
            f'color:#22d3ee;">{call_intent}</span></div>'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Duration</span><br>'
            f'<span style="font-size:0.88rem;color:#e2e8f0;">{call_dur}s</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Word count indicator
        _transcript_text = call_detail["transcript_text"]
        _word_count = len(_transcript_text.split())
        st.markdown(
            f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:0.4rem;'
            f'font-family:\'JetBrains Mono\',monospace;">'
            f'{_word_count:,} words</div>',
            unsafe_allow_html=True,
        )

        # Style the transcript code block to match dark navy theme
        st.markdown(
            "<style>"
            "div[data-testid='stCode'] {"
            "  border: 1px solid #334155;"
            "  border-radius: 10px;"
            "  overflow: hidden;"
            "}"
            "div[data-testid='stCode'] pre {"
            "  max-height: 420px;"
            "  overflow-y: auto;"
            "  background: #0f172a !important;"
            "  color: #cbd5e1 !important;"
            "  font-family: 'JetBrains Mono', monospace !important;"
            "  font-size: 0.82rem !important;"
            "  line-height: 1.7 !important;"
            "  padding: 1rem 1.2rem !important;"
            "}"
            "div[data-testid='stCode'] pre::-webkit-scrollbar {"
            "  width: 6px;"
            "}"
            "div[data-testid='stCode'] pre::-webkit-scrollbar-track {"
            "  background: #1e293b;"
            "}"
            "div[data-testid='stCode'] pre::-webkit-scrollbar-thumb {"
            "  background: #475569;"
            "  border-radius: 3px;"
            "}"
            "</style>",
            unsafe_allow_html=True,
        )

        # Transcript with native copy button
        st.code(call_detail["transcript_text"], language=None, wrap_lines=True)

        # Link to full detail page — styled as pill link
        st.markdown(
            f'<a href="/Call_Detail?call_id={selected_call_id}" target="_self" '
            f'style="display:inline-block;margin-top:0.6rem;padding:0.45rem 1.2rem;'
            f'background:#164e63;color:#22d3ee !important;border:1px solid #22d3ee33;'
            f'border-radius:8px;font-size:0.82rem;font-weight:600;'
            f'letter-spacing:0.02em;text-decoration:none !important;'
            f'transition:all 0.2s ease;"'
            f' onmouseover="this.style.background=\'#1e6a7a\';this.style.borderColor=\'#22d3ee66\'"'
            f' onmouseout="this.style.background=\'#164e63\';this.style.borderColor=\'#22d3ee33\'"'
            f'>Open full analysis &#8594;</a>',
            unsafe_allow_html=True,
        )
    elif call_detail:
        st.markdown(
            '<div style="height:2px;margin:1.5rem 0 1rem 0;'
            'background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
            'border-radius:1px;opacity:0.5;"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;'
            'text-transform:uppercase;color:#64748b;margin-bottom:0.5rem;">'
            'Transcript Preview</div>',
            unsafe_allow_html=True,
        )
        st.warning("This call has no transcript text yet.")
    else:
        st.markdown(
            '<div style="height:2px;margin:1.5rem 0 1rem 0;'
            'background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
            'border-radius:1px;opacity:0.5;"></div>',
            unsafe_allow_html=True,
        )
        st.error(f"Could not load call {selected_call_id}.")

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "\U0001F4E5 Export CSV",
    data=csv_bytes,
    file_name=f"invoca_calls_{start_date}_{end_date}.csv",
    mime="text/csv",
)
