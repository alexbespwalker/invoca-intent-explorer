"""Trend views for quality, confusion, and repositioning."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import plotly.express as px
import streamlit as st

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[2] if _THIS_FILE.parent.name == "pages" else _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    # Keep package imports stable when Streamlit executes files by path.
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.data_access import (
    get_confusion_patterns_df,
    get_data_freshness_snapshot,
    get_pipeline_snapshot,
    get_quality_trends_df,
    get_repositioning_df,
)
from invoca_intent_portal.lib.filter_state import CallFilters
from invoca_intent_portal.lib.sidebar_filters import build_active_filter_summary, render_call_filter_sidebar
from invoca_intent_portal.lib.supabase_client import get_supabase_client
from invoca_intent_portal.lib.ui import (
    apply_base_styles,
    render_pipeline_health_panel,
)

st.set_page_config(page_title="Trends Dashboard", page_icon="📈", layout="wide")
apply_base_styles()
st.title("Trends Dashboard")

client = get_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

with st.sidebar:
    sidebar_selection = render_call_filter_sidebar(
        client=client,
        page_key="trends",
        pt_today=pt_today,
        date_presets=[
            ("Last 7 Days (PT)", "last_7"),
            ("Last 14 Days (PT)", "last_14"),
            ("Last 28 Days (PT)", "last_28"),
            ("Custom", "custom"),
        ],
        default_preset_index=1,
        custom_days_default=28,
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

quality_df = get_quality_trends_df(
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
confusion_df = get_confusion_patterns_df(
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
reposition_df = get_repositioning_df(
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

if quality_df.empty and confusion_df.empty and reposition_df.empty:
    st.warning("No trend data available for this date range.")
    st.stop()

st.markdown(f"<div class='portal-filter-summary'>{_active_filter_summary()}</div>", unsafe_allow_html=True)

st.subheader("Weekly Quality + Confusion")
if not quality_df.empty:
    fig_quality = px.line(
        quality_df,
        x="week_start",
        y=["avg_agent_quality", "confusion_rate_pct"],
        markers=True,
    )
    fig_quality.update_layout(margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Value")
    st.plotly_chart(fig_quality, use_container_width=True)
else:
    st.info("No quality trend rows yet.")

trend_col_1, trend_col_2 = st.columns(2)

with trend_col_1:
    st.subheader("Top Confusion Signals")
    if not confusion_df.empty:
        top_conf = (
            confusion_df.groupby("confusion_signal", as_index=False)["signal_count"]
            .sum()
            .sort_values("signal_count", ascending=False)
            .head(12)
        )
        fig_conf = px.bar(top_conf, x="confusion_signal", y="signal_count")
        fig_conf.update_layout(margin=dict(t=20, b=20, l=20, r=20), xaxis_title=None, yaxis_title="Mentions")
        st.plotly_chart(fig_conf, use_container_width=True)
    else:
        st.info("No confusion signals in this period.")

with trend_col_2:
    st.subheader("Repositioning Success Rate")
    if not reposition_df.empty:
        fig_rep = px.line(reposition_df, x="week_start", y="success_rate_pct", markers=True)
        fig_rep.update_layout(margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Success %")
        st.plotly_chart(fig_rep, use_container_width=True)
    else:
        st.info("No repositioning rows in this period.")

with st.expander("Raw Trend Tables", expanded=False):
    st.markdown("**Quality Trends**")
    st.dataframe(quality_df, use_container_width=True, hide_index=True)
    st.markdown("**Confusion Patterns**")
    st.dataframe(confusion_df, use_container_width=True, hide_index=True)
    st.markdown("**Repositioning Effectiveness**")
    st.dataframe(reposition_df, use_container_width=True, hide_index=True)
