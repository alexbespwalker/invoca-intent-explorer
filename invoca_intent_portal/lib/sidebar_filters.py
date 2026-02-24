"""Shared sidebar rendering for call dashboards."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any

import streamlit as st

from invoca_intent_portal.lib.calls_repo import get_brands_df, get_dimension_options
from invoca_intent_portal.lib.filter_state import CallFilters
from invoca_intent_portal.lib.ui import render_main_filter_inputs


@dataclass(frozen=True)
class SidebarSelection:
    start_date: date
    end_date: date
    filters: CallFilters


_ADVANCED_DIMENSIONS: list[tuple[str, str, str]] = [
    ("Advertiser (Exact)", "advertiser_name", "advertiser_name"),
    ("Campaign (Exact)", "campaign_name", "campaign_name"),
    ("Media Source", "media_source", "media_source"),
    ("Publisher", "publisher", "publisher"),
    ("Channel", "channel", "channel"),
    ("UTM Source", "utm_source", "utm_source"),
    ("UTM Campaign", "utm_campaign", "utm_campaign"),
    ("Device Type", "device_type", "device_type"),
    ("Geo Region", "geo_region", "geo_region"),
    ("Geo City", "geo_city", "geo_city"),
    ("Call Status", "status", "call_status"),
]


def _build_pt_date_range(
    pt_today: date,
    preset_value: str,
    custom_days_default: int,
) -> tuple[date, date]:
    if preset_value == "yesterday":
        start_date = pt_today - timedelta(days=1)
        return start_date, start_date

    if preset_value.startswith("last_"):
        days = int(preset_value.replace("last_", ""))
        end_date = pt_today
        start_date = end_date - timedelta(days=days - 1)
        return start_date, end_date

    # custom
    date_range = st.date_input(
        "Date Range (PT)",
        value=(pt_today - timedelta(days=custom_days_default - 1), pt_today),
        max_value=pt_today,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        return date_range[0], date_range[1]
    return pt_today - timedelta(days=custom_days_default - 1), pt_today


def render_call_filter_sidebar(
    client: Any,
    page_key: str,
    pt_today: date,
    date_presets: list[tuple[str, str]],
    default_preset_index: int,
    custom_days_default: int,
) -> SidebarSelection:
    st.header("Filters")

    preset_labels = [label for label, _ in date_presets]
    preset_map = {label: value for label, value in date_presets}
    selected_preset_label = st.selectbox(
        "Date Preset",
        options=preset_labels,
        index=default_preset_index,
    )
    start_date, end_date = _build_pt_date_range(
        pt_today=pt_today,
        preset_value=preset_map[selected_preset_label],
        custom_days_default=custom_days_default,
    )

    brands_df = get_brands_df(client)
    brand_options = ["ALL"]
    brand_label_map = {"ALL": "All Brands"}
    if not brands_df.empty:
        for _, row in brands_df.iterrows():
            code = row["brand_code"]
            brand_options.append(code)
            brand_label_map[code] = f"{code} - {row['brand_name']}"

    selected_brand = st.selectbox(
        "Brand",
        options=brand_options,
        index=0,
        format_func=lambda x: brand_label_map.get(x, x),
    )

    st.markdown("#### Main Filters")
    selected_advertiser_query, selected_campaign_query = render_main_filter_inputs(page_key)

    running_filters = CallFilters(
        brand_code=selected_brand,
        advertiser_query=selected_advertiser_query,
        campaign_query=selected_campaign_query,
    )

    with st.expander("Advanced Filters", expanded=False):
        for label, column_name, attr_name in _ADVANCED_DIMENSIONS:
            options = ["ALL"] + get_dimension_options(
                client=client,
                column_name=column_name,
                start_date=start_date,
                end_date=end_date,
                filters=running_filters,
            )
            selected_value = st.selectbox(label, options=options, index=0, key=f"{page_key}_{column_name}_exact")
            normalized_value = None if str(selected_value).upper() == "ALL" else selected_value
            running_filters = replace(running_filters, **{attr_name: normalized_value})

    return SidebarSelection(
        start_date=start_date,
        end_date=end_date,
        filters=running_filters,
    )


def build_active_filter_summary(filters: CallFilters) -> str:
    pairs = [
        ("Brand", filters.brand_code),
        ("Advertiser Contains", filters.advertiser_query),
        ("Campaign Contains", filters.campaign_query),
        ("Advertiser", filters.advertiser_name),
        ("Media Source", filters.media_source),
        ("Campaign", filters.campaign_name),
        ("Publisher", filters.publisher),
        ("Channel", filters.channel),
        ("UTM Source", filters.utm_source),
        ("UTM Campaign", filters.utm_campaign),
        ("Device", filters.device_type),
        ("Region", filters.geo_region),
        ("City", filters.geo_city),
        ("Status", filters.call_status),
    ]
    active = [f"{key}: {value}" for key, value in pairs if value and str(value).upper() != "ALL"]
    return "Active Filters: " + (" | ".join(active) if active else "All")
