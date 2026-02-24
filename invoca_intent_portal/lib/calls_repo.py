"""Calls and dimension repository helpers."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from invoca_intent_portal.lib.filter_state import CallFilters


def _table(client: Any, table_name: str) -> Any:
    return client.schema("invoca").table(table_name)


def _as_df(data: list[dict[str, Any]]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def _norm_filter(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value or value.upper() == "ALL":
        return None
    return value


def _norm_contains(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    return value


def _escape_ilike(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_ilike_pattern(value: str) -> str:
    # Allow explicit wildcard use like 5BC% while keeping default behavior as contains.
    if "%" in value or "_" in value:
        return value
    return f"%{_escape_ilike(value)}%"


def _filters_without_dimension(filters: CallFilters, column_name: str) -> CallFilters:
    if column_name == "advertiser_name":
        return replace(filters, advertiser_name=None, advertiser_query=None)
    if column_name == "campaign_name":
        return replace(filters, campaign_name=None, campaign_query=None)
    if column_name == "status":
        return replace(filters, call_status=None)
    if hasattr(filters, column_name):
        return replace(filters, **{column_name: None})
    return filters


def _apply_call_filters(query: Any, filters: CallFilters | None) -> Any:
    scoped = filters or CallFilters()

    norm_brand = _norm_filter(scoped.brand_code)
    norm_media_source = _norm_filter(scoped.media_source)
    norm_campaign_name = _norm_filter(scoped.campaign_name)
    norm_campaign_query = _norm_contains(scoped.campaign_query)
    norm_publisher = _norm_filter(scoped.publisher)
    norm_channel = _norm_filter(scoped.channel)
    norm_advertiser_name = _norm_filter(scoped.advertiser_name)
    norm_advertiser_query = _norm_contains(scoped.advertiser_query)
    norm_utm_source = _norm_filter(scoped.utm_source)
    norm_utm_campaign = _norm_filter(scoped.utm_campaign)
    norm_device_type = _norm_filter(scoped.device_type)
    norm_geo_region = _norm_filter(scoped.geo_region)
    norm_geo_city = _norm_filter(scoped.geo_city)
    norm_call_status = _norm_filter(scoped.call_status)

    if norm_brand:
        query = query.eq("brand_code", norm_brand)
    if norm_media_source:
        query = query.eq("media_source", norm_media_source)
    if norm_campaign_name:
        query = query.eq("campaign_name", norm_campaign_name)
    if norm_campaign_query:
        query = query.ilike("campaign_name", _build_ilike_pattern(norm_campaign_query))
    if norm_publisher:
        query = query.eq("publisher", norm_publisher)
    if norm_channel:
        query = query.eq("channel", norm_channel)
    if norm_advertiser_name:
        query = query.eq("advertiser_name", norm_advertiser_name)
    if norm_advertiser_query:
        query = query.ilike("advertiser_name", _build_ilike_pattern(norm_advertiser_query))
    if norm_utm_source:
        query = query.eq("utm_source", norm_utm_source)
    if norm_utm_campaign:
        query = query.eq("utm_campaign", norm_utm_campaign)
    if norm_device_type:
        query = query.eq("device_type", norm_device_type)
    if norm_geo_region:
        query = query.eq("geo_region", norm_geo_region)
    if norm_geo_city:
        query = query.eq("geo_city", norm_geo_city)
    if norm_call_status:
        query = query.eq("status", norm_call_status)
    return query


@st.cache_data(ttl=3600, show_spinner=False)
def get_brands_df(_client: Any) -> pd.DataFrame:
    rows = (
        _table(_client, "brands")
        .select("brand_code,brand_name,active,priority")
        .eq("active", True)
        .order("priority", desc=False)
        .execute()
        .data
        or []
    )
    return _as_df(rows)


@st.cache_data(ttl=3600, show_spinner=False)
def get_dimension_options(
    _client: Any,
    column_name: str,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
    limit: int = 1000,
) -> list[str]:
    query = (
        _table(_client, "calls")
        .select(column_name)
        .gte("call_date_pt", start_date.isoformat())
        .lte("call_date_pt", end_date.isoformat())
        .not_.is_(column_name, "null")
        .limit(limit)
    )

    scoped_filters = _filters_without_dimension(filters or CallFilters(), column_name)
    query = _apply_call_filters(query=query, filters=scoped_filters)
    rows = query.execute().data or []

    values = []
    for row in rows:
        value = row.get(column_name)
        if value is None:
            continue
        val_str = str(value).strip()
        if val_str:
            values.append(val_str)
    return sorted(set(values))


@st.cache_data(ttl=300, show_spinner=False)
def get_calls_df(
    _client: Any,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
    limit: int = 500,
) -> pd.DataFrame:
    query = (
        _table(_client, "calls")
        .select(
            "id,invoca_call_id,call_record_id,brand_code,advertiser_name,campaign_name,"
            "call_date_pt,call_start_time,duration_seconds,status,transcript_word_count,"
            "caller_phone,destination_number,media_source,media_medium,publisher,channel,"
            "landing_page,utm_source,utm_medium,utm_campaign,utm_term,utm_content,"
            "gclid,fbclid,msclkid,ad_group,creative_id,placement,device_type,geo_region,geo_city"
        )
        .gte("call_date_pt", start_date.isoformat())
        .lte("call_date_pt", end_date.isoformat())
        .order("call_start_time", desc=True)
        .limit(limit)
    )
    query = _apply_call_filters(query=query, filters=filters)

    calls_rows = query.execute().data or []
    calls_df = _as_df(calls_rows)
    if calls_df.empty:
        return calls_df

    call_ids = calls_df["id"].tolist()
    analysis_rows = (
        _table(_client, "analysis")
        .select(
            "call_id,analyzed_at,caller_intent,intent_confidence,brand_confusion,"
            "call_outcome,agent_quality_score,caller_sentiment,total_cost,validation_passed,"
            "confusion_signals,agent_repositioning_attempted,agent_repositioning_successful,"
            "repositioning_technique,flags"
        )
        .in_("call_id", call_ids)
        .order("analyzed_at", desc=True)
        .execute()
        .data
        or []
    )
    analysis_df = _as_df(analysis_rows)

    if not analysis_df.empty:
        analysis_df["analyzed_at"] = pd.to_datetime(analysis_df["analyzed_at"], utc=True, errors="coerce")
        analysis_df = analysis_df.sort_values("analyzed_at", ascending=False).drop_duplicates(
            subset=["call_id"], keep="first"
        )

    calls_df = calls_df.merge(
        analysis_df,
        how="left",
        left_on="id",
        right_on="call_id",
    )
    calls_df["call_start_time"] = pd.to_datetime(calls_df.get("call_start_time"), utc=True, errors="coerce")
    if "call_date_pt" in calls_df.columns:
        calls_df["call_date_pt"] = pd.to_datetime(calls_df["call_date_pt"], errors="coerce").dt.date
    return calls_df


def get_call_detail_by_numeric_id(client: Any, call_id: int) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    call_rows = _table(client, "calls").select("*").eq("id", call_id).limit(1).execute().data or []
    if not call_rows:
        return None, []

    analysis_rows = (
        _table(client, "analysis")
        .select("*")
        .eq("call_id", call_id)
        .order("analyzed_at", desc=True)
        .execute()
        .data
        or []
    )
    return call_rows[0], analysis_rows


def get_call_detail_by_invoca_id(
    client: Any,
    invoca_call_id: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    call_rows = (
        _table(client, "calls")
        .select("*")
        .eq("invoca_call_id", invoca_call_id)
        .order("call_start_time", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not call_rows:
        return None, []

    call = call_rows[0]
    analysis_rows = (
        _table(client, "analysis")
        .select("*")
        .eq("call_id", call["id"])
        .order("analyzed_at", desc=True)
        .execute()
        .data
        or []
    )
    return call, analysis_rows
