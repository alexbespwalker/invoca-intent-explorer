"""Invoca Intent Explorer — home page."""

from __future__ import annotations

from datetime import datetime, timedelta
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
from invoca_intent_portal.lib.db import get_analyzed_calls, get_brands
from invoca_intent_portal.lib.ui import apply_base_styles, apply_chart_defaults

st.set_page_config(
    page_title="Invoca Intent Explorer",
    page_icon="\U0001F4DE",
    layout="wide",
)
apply_base_styles()
check_password()

st.title("Invoca Intent Explorer")
st.caption("BC call analysis: caller intent, brand confusion, agent quality.")

client = require_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

# ── Sidebar: 2 filters ──────────────────────────────────────────────────
with st.sidebar:
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
if analyzed_count > 0:
    intent_counts = calls_df.loc[analyzed_mask, "caller_intent"].value_counts()
    if not intent_counts.empty:
        top_intent = str(intent_counts.index[0])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Calls", f"{total_count:,}")
m2.metric("Brand Confusion Rate", f"{confusion_rate:.1f}%")
m3.metric("Avg Agent Quality", f"{avg_quality:.1f}" if avg_quality else "n/a")
m4.metric("Most Common Intent", top_intent)

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
        fig_pie = px.pie(pie_data, names="caller_intent", values="count", hole=0.45)
        apply_chart_defaults(fig_pie)
        fig_pie.update_layout(legend_title_text="Intent")
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
        fig_out = px.bar(out_data, x="call_outcome", y="count")
        apply_chart_defaults(fig_out)
        fig_out.update_layout(xaxis_title=None)
        st.plotly_chart(fig_out, use_container_width=True)
    else:
        st.info("No analyzed outcomes in current window.")

# ── Daily trend line ─────────────────────────────────────────────────────
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
    fig_trend = px.line(trend_df, x="call_date", y="calls", color="caller_intent")
    apply_chart_defaults(fig_trend)
    fig_trend.update_layout(yaxis_title="Calls")
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No analyzed data for trend chart.")

# ── Call table ───────────────────────────────────────────────────────────
st.subheader("Call Table")

show_cols = [
    "id", "invoca_call_id", "call_date_pt", "caller_intent",
    "intent_confidence", "call_outcome", "brand_confusion",
    "agent_quality_score", "caller_sentiment", "duration_seconds", "status",
]
existing_cols = [c for c in show_cols if c in calls_df.columns]
display_df = calls_df[existing_cols].copy()

st.dataframe(display_df, use_container_width=True, hide_index=True)

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Export CSV",
    data=csv_bytes,
    file_name=f"invoca_calls_{start_date}_{end_date}.csv",
    mime="text/csv",
)
