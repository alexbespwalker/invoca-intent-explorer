"""Intent Explorer home page."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[2] if _THIS_FILE.parent.name == "pages" else _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    # Keep package imports stable when Streamlit executes files by path.
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.data_access import (
    get_calls_df,
    get_data_freshness_snapshot,
    get_intent_summary_df,
    get_pipeline_snapshot,
)
from invoca_intent_portal.lib.filter_state import CallFilters
from invoca_intent_portal.lib.sidebar_filters import build_active_filter_summary, render_call_filter_sidebar
from invoca_intent_portal.lib.supabase_client import get_supabase_client
from invoca_intent_portal.lib.ui import (
    apply_base_styles,
    render_pipeline_health_panel,
)

st.set_page_config(
    page_title="Invoca Intent Explorer",
    page_icon="📞",
    layout="wide",
)
apply_base_styles()

st.title("Invoca Intent Explorer")
st.caption("North star: insight quality for intent, confusion, repositioning, and outcomes.")

client = get_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

with st.sidebar:
    sidebar_selection = render_call_filter_sidebar(
        client=client,
        page_key="home",
        pt_today=pt_today,
        date_presets=[
            ("Yesterday (PT)", "yesterday"),
            ("Last 7 Days (PT)", "last_7"),
            ("Last 14 Days (PT)", "last_14"),
            ("Custom", "custom"),
        ],
        default_preset_index=0,
        custom_days_default=14,
    )

start_date = sidebar_selection.start_date
end_date = sidebar_selection.end_date
selected_filters: CallFilters = sidebar_selection.filters
selected_brand = selected_filters.brand_code
selected_media_source = selected_filters.media_source
selected_campaign = selected_filters.campaign_name
selected_campaign_query = selected_filters.campaign_query
selected_publisher = selected_filters.publisher
selected_channel = selected_filters.channel
selected_advertiser = selected_filters.advertiser_name
selected_advertiser_query = selected_filters.advertiser_query
selected_utm_source = selected_filters.utm_source
selected_utm_campaign = selected_filters.utm_campaign
selected_device = selected_filters.device_type
selected_region = selected_filters.geo_region
selected_city = selected_filters.geo_city
selected_status = selected_filters.call_status


def _active_filter_summary() -> str:
    return build_active_filter_summary(selected_filters)


pipeline_snapshot = get_pipeline_snapshot(client)
freshness_snapshot = get_data_freshness_snapshot(client)
render_pipeline_health_panel(pipeline_snapshot, freshness_snapshot)

with st.spinner("Loading data..."):
    summary_df = get_intent_summary_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        brand_code=selected_brand,
        media_source=selected_media_source,
        campaign_name=selected_campaign,
        campaign_query=selected_campaign_query,
        publisher=selected_publisher,
        channel=selected_channel,
        advertiser_name=selected_advertiser,
        advertiser_query=selected_advertiser_query,
        utm_source=selected_utm_source,
        utm_campaign=selected_utm_campaign,
        device_type=selected_device,
        geo_region=selected_region,
        geo_city=selected_city,
        call_status=selected_status,
        filters=selected_filters,
    )
    calls_df = get_calls_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        brand_code=selected_brand,
        limit=5000,
        media_source=selected_media_source,
        campaign_name=selected_campaign,
        campaign_query=selected_campaign_query,
        publisher=selected_publisher,
        channel=selected_channel,
        advertiser_name=selected_advertiser,
        advertiser_query=selected_advertiser_query,
        utm_source=selected_utm_source,
        utm_campaign=selected_utm_campaign,
        device_type=selected_device,
        geo_region=selected_region,
        geo_city=selected_city,
        call_status=selected_status,
        filters=selected_filters,
    )

if calls_df.empty:
    st.warning("No calls found for this filter window.")
    st.stop()

st.markdown(f"<div class='portal-filter-summary'>{_active_filter_summary()}</div>", unsafe_allow_html=True)

calls_count = len(calls_df)
confusion_rate = float(calls_df["brand_confusion"].fillna(False).mean() * 100)
avg_quality = float(calls_df["agent_quality_score"].dropna().mean()) if "agent_quality_score" in calls_df else 0.0
avg_confidence = float(calls_df["intent_confidence"].dropna().mean()) if "intent_confidence" in calls_df else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Calls", f"{calls_count:,}")
m2.metric("Brand Confusion Rate", f"{confusion_rate:.1f}%")
m3.metric("Avg Agent Quality", f"{avg_quality:.2f}")
m4.metric("Avg Intent Confidence", f"{avg_confidence:.1f}")

chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    st.subheader("Intent Distribution")
    st.markdown("<div class='portal-section-caption'>Distribution of analyzed caller intents.</div>", unsafe_allow_html=True)
    if "caller_intent" in calls_df and calls_df["caller_intent"].notna().any():
        pie_data = (
            calls_df["caller_intent"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("caller_intent")
            .reset_index(name="count")
        )
        fig_pie = px.pie(pie_data, names="caller_intent", values="count", hole=0.45)
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend_title_text="Intent")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No analyzed intent rows in current window yet.")

with chart_col_2:
    st.subheader("Outcome Breakdown")
    st.markdown("<div class='portal-section-caption'>Outcome labels for analyzed calls.</div>", unsafe_allow_html=True)
    if "call_outcome" in calls_df and calls_df["call_outcome"].notna().any():
        out_data = (
            calls_df["call_outcome"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("call_outcome")
            .reset_index(name="count")
        )
        fig_out = px.bar(out_data, x="call_outcome", y="count")
        fig_out.update_layout(margin=dict(t=20, b=20, l=20, r=20), xaxis_title=None)
        st.plotly_chart(fig_out, use_container_width=True)
    else:
        st.info("No analyzed outcomes in current window yet.")

st.subheader("Daily Intent Trend")
if not summary_df.empty:
    trend_df = summary_df.groupby(["call_date", "caller_intent"], as_index=False)["total_calls"].sum()
    fig_trend = px.line(trend_df, x="call_date", y="total_calls", color="caller_intent")
    fig_trend.update_layout(margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Calls")
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No summary rows available yet for this date window.")

st.subheader("Top Elements")
top_col_1, top_col_2, top_col_3, top_col_4 = st.columns(4)

def _top_counts(df: pd.DataFrame, col: str, n: int = 8) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame(columns=[col, "count"])
    out = (
        df[col]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .replace("", "unknown")
        .value_counts()
        .head(n)
        .rename_axis(col)
        .reset_index(name="count")
    )
    return out


with top_col_1:
    st.markdown("**Media Source**")
    top_media = _top_counts(calls_df, "media_source")
    st.dataframe(top_media, use_container_width=True, hide_index=True)

with top_col_2:
    st.markdown("**Campaign**")
    top_campaign = _top_counts(calls_df, "campaign_name")
    st.dataframe(top_campaign, use_container_width=True, hide_index=True)

with top_col_3:
    st.markdown("**Publisher**")
    top_publisher = _top_counts(calls_df, "publisher")
    st.dataframe(top_publisher, use_container_width=True, hide_index=True)

with top_col_4:
    st.markdown("**Channel**")
    top_channel = _top_counts(calls_df, "channel")
    st.dataframe(top_channel, use_container_width=True, hide_index=True)

st.subheader("Call Table")
show_cols = [
    "id",
    "invoca_call_id",
    "call_date_pt",
    "call_start_time",
    "brand_code",
    "advertiser_name",
    "campaign_name",
    "media_source",
    "publisher",
    "channel",
    "duration_seconds",
    "status",
    "caller_intent",
    "intent_confidence",
    "call_outcome",
    "brand_confusion",
    "agent_quality_score",
]
existing_cols = [c for c in show_cols if c in calls_df.columns]

display_df = calls_df[existing_cols].copy()
if "call_start_time" in display_df.columns:
    display_df["call_start_time"] = pd.to_datetime(display_df["call_start_time"], utc=True, errors="coerce")

st.dataframe(display_df, use_container_width=True, hide_index=True)

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Export Filtered CSV",
    data=csv_bytes,
    file_name=f"invoca_calls_{start_date}_{end_date}.csv",
    mime="text/csv",
)

st.caption("Use left navigation for Call Detail, Trends, and Review Queue.")
