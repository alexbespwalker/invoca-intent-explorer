"""Shared UI helpers for Streamlit pages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from invoca_intent_portal.lib.constants import MAIN_FILTER_PRESETS

_MAIN_FILTER_PRESETS = MAIN_FILTER_PRESETS


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
        .portal-filter-summary {
            margin: 0.2rem 0 1rem 0;
            color: #334155;
            font-size: 0.9rem;
        }
        .portal-section-caption {
            margin-top: -0.35rem;
            color: #64748b;
            font-size: 0.82rem;
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


def format_timestamp_utc(value: Any) -> str:
    if value is None:
        return "n/a"

    text = str(value).strip()
    if not text:
        return "n/a"

    parsed: datetime | None = None
    try:
        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return text

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%d %H:%M UTC")


def render_main_filter_inputs(page_key: str) -> tuple[str, str]:
    preset_key = f"{page_key}_main_filter_preset"
    previous_preset_key = f"{page_key}_main_filter_preset_prev"
    advertiser_key = f"{page_key}_advertiser_query"
    campaign_key = f"{page_key}_campaign_query"

    preset_names = list(_MAIN_FILTER_PRESETS.keys())
    if preset_key not in st.session_state:
        st.session_state[preset_key] = preset_names[0]
    if previous_preset_key not in st.session_state:
        st.session_state[previous_preset_key] = st.session_state[preset_key]
    if advertiser_key not in st.session_state:
        st.session_state[advertiser_key] = ""
    if campaign_key not in st.session_state:
        st.session_state[campaign_key] = ""

    selected_preset = st.selectbox("Main Filter Preset", options=preset_names, key=preset_key)
    if selected_preset != st.session_state[previous_preset_key]:
        preset_advertiser, preset_campaign = _MAIN_FILTER_PRESETS[selected_preset]
        st.session_state[advertiser_key] = preset_advertiser
        st.session_state[campaign_key] = preset_campaign
        st.session_state[previous_preset_key] = selected_preset

    advertiser_query = st.text_input(
        "Advertiser Contains",
        key=advertiser_key,
        placeholder="betterclaims or %claim%",
    )
    campaign_query = st.text_input(
        "Campaign Contains",
        key=campaign_key,
        placeholder="BC, MVA, 5BC%",
    )
    st.caption("Main filters support wildcards: `%` and `_`.")
    return advertiser_query, campaign_query


def render_pipeline_health_panel(
    pipeline_snapshot: dict[str, dict[str, Any] | None],
    freshness_snapshot: dict[str, Any],
) -> None:
    health_row = pipeline_snapshot.get("healthcheck") or {}
    discovery_row = pipeline_snapshot.get("discovery") or {}

    raw_status = str(health_row.get("status") or "").strip().lower()
    if raw_status in {"ok", "success"}:
        health_label = "Healthy"
    elif raw_status in {"warning", "warn"}:
        health_label = "Warning"
    elif raw_status in {"error", "failed", "failure"}:
        health_label = "Error"
    else:
        health_label = "Unknown"

    discovery_rows_raw = discovery_row.get("rows_processed")
    if discovery_rows_raw in (None, ""):
        discovery_rows_raw = discovery_row.get("rows_discovered")
    try:
        discovery_rows = int(discovery_rows_raw or 0)
    except (TypeError, ValueError):
        discovery_rows = 0

    health_ts = format_timestamp_utc(health_row.get("started_at") or health_row.get("finished_at"))
    discovery_ts = format_timestamp_utc(discovery_row.get("started_at") or discovery_row.get("finished_at"))
    latest_call_ts = format_timestamp_utc(freshness_snapshot.get("latest_call_updated_at"))
    latest_analysis_ts = format_timestamp_utc(freshness_snapshot.get("latest_analyzed_at"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Pipeline Health", health_label)
    col2.metric("Last Discovery Rows", f"{discovery_rows:,}")
    col3.metric("Latest Call Update", latest_call_ts)

    st.caption(
        f"Healthcheck: {health_ts} | Discovery run: {discovery_ts} | "
        f"Latest analysis: {latest_analysis_ts}"
    )
