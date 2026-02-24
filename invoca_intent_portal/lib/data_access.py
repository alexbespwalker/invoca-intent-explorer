"""Backward-compatible data access facade.

This module preserves the original function signatures while delegating
implementation to focused repository modules.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

import pandas as pd

from invoca_intent_portal.lib.analysis_repo import (
    get_confusion_patterns_df as _get_confusion_patterns_df,
    get_intent_summary_df as _get_intent_summary_df,
    get_quality_trends_df as _get_quality_trends_df,
    get_repositioning_df as _get_repositioning_df,
)
from invoca_intent_portal.lib.calls_repo import (
    get_brands_df,
    get_call_detail_by_invoca_id,
    get_call_detail_by_numeric_id,
    get_calls_df as _get_calls_df,
    get_dimension_options as _get_dimension_options,
)
from invoca_intent_portal.lib.filter_state import CallFilters
from invoca_intent_portal.lib.ops_repo import get_data_freshness_snapshot, get_pipeline_snapshot
from invoca_intent_portal.lib.review_repo import get_review_queue_df, save_review_result


def _merge_filters(
    filters: CallFilters | None,
    brand_code: str | None = None,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
) -> CallFilters:
    merged = filters or CallFilters()
    updates: dict[str, Any] = {}

    if brand_code is not None:
        updates["brand_code"] = brand_code
    if media_source is not None:
        updates["media_source"] = media_source
    if campaign_name is not None:
        updates["campaign_name"] = campaign_name
    if campaign_query is not None:
        updates["campaign_query"] = campaign_query
    if publisher is not None:
        updates["publisher"] = publisher
    if channel is not None:
        updates["channel"] = channel
    if advertiser_name is not None:
        updates["advertiser_name"] = advertiser_name
    if advertiser_query is not None:
        updates["advertiser_query"] = advertiser_query
    if utm_source is not None:
        updates["utm_source"] = utm_source
    if utm_campaign is not None:
        updates["utm_campaign"] = utm_campaign
    if device_type is not None:
        updates["device_type"] = device_type
    if geo_region is not None:
        updates["geo_region"] = geo_region
    if geo_city is not None:
        updates["geo_city"] = geo_city
    if call_status is not None:
        updates["call_status"] = call_status

    if not updates:
        return merged
    return replace(merged, **updates)


def get_dimension_options(
    client: Any,
    column_name: str,
    start_date: date,
    end_date: date,
    brand_code: str | None = None,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
    limit: int = 1000,
    filters: CallFilters | None = None,
) -> list[str]:
    resolved_filters = _merge_filters(
        filters=filters,
        brand_code=brand_code,
        media_source=media_source,
        campaign_name=campaign_name,
        campaign_query=campaign_query,
        publisher=publisher,
        channel=channel,
        advertiser_name=advertiser_name,
        advertiser_query=advertiser_query,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        device_type=device_type,
        geo_region=geo_region,
        geo_city=geo_city,
        call_status=call_status,
    )
    return _get_dimension_options(
        client=client,
        column_name=column_name,
        start_date=start_date,
        end_date=end_date,
        filters=resolved_filters,
        limit=limit,
    )


def get_calls_df(
    client: Any,
    start_date: date,
    end_date: date,
    brand_code: str | None,
    limit: int = 500,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    resolved_filters = _merge_filters(
        filters=filters,
        brand_code=brand_code,
        media_source=media_source,
        campaign_name=campaign_name,
        campaign_query=campaign_query,
        publisher=publisher,
        channel=channel,
        advertiser_name=advertiser_name,
        advertiser_query=advertiser_query,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        device_type=device_type,
        geo_region=geo_region,
        geo_city=geo_city,
        call_status=call_status,
    )
    return _get_calls_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=resolved_filters,
        limit=limit,
    )


def get_intent_summary_df(
    client: Any,
    start_date: date,
    end_date: date,
    brand_code: str | None,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    resolved_filters = _merge_filters(
        filters=filters,
        brand_code=brand_code,
        media_source=media_source,
        campaign_name=campaign_name,
        campaign_query=campaign_query,
        publisher=publisher,
        channel=channel,
        advertiser_name=advertiser_name,
        advertiser_query=advertiser_query,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        device_type=device_type,
        geo_region=geo_region,
        geo_city=geo_city,
        call_status=call_status,
    )
    return _get_intent_summary_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=resolved_filters,
    )


def get_quality_trends_df(
    client: Any,
    start_date: date,
    end_date: date,
    brand_code: str | None,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    resolved_filters = _merge_filters(
        filters=filters,
        brand_code=brand_code,
        media_source=media_source,
        campaign_name=campaign_name,
        campaign_query=campaign_query,
        publisher=publisher,
        channel=channel,
        advertiser_name=advertiser_name,
        advertiser_query=advertiser_query,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        device_type=device_type,
        geo_region=geo_region,
        geo_city=geo_city,
        call_status=call_status,
    )
    return _get_quality_trends_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=resolved_filters,
    )


def get_confusion_patterns_df(
    client: Any,
    start_date: date,
    end_date: date,
    brand_code: str | None,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    resolved_filters = _merge_filters(
        filters=filters,
        brand_code=brand_code,
        media_source=media_source,
        campaign_name=campaign_name,
        campaign_query=campaign_query,
        publisher=publisher,
        channel=channel,
        advertiser_name=advertiser_name,
        advertiser_query=advertiser_query,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        device_type=device_type,
        geo_region=geo_region,
        geo_city=geo_city,
        call_status=call_status,
    )
    return _get_confusion_patterns_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=resolved_filters,
    )


def get_repositioning_df(
    client: Any,
    start_date: date,
    end_date: date,
    brand_code: str | None,
    media_source: str | None = None,
    campaign_name: str | None = None,
    campaign_query: str | None = None,
    publisher: str | None = None,
    channel: str | None = None,
    advertiser_name: str | None = None,
    advertiser_query: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    device_type: str | None = None,
    geo_region: str | None = None,
    geo_city: str | None = None,
    call_status: str | None = None,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    resolved_filters = _merge_filters(
        filters=filters,
        brand_code=brand_code,
        media_source=media_source,
        campaign_name=campaign_name,
        campaign_query=campaign_query,
        publisher=publisher,
        channel=channel,
        advertiser_name=advertiser_name,
        advertiser_query=advertiser_query,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        device_type=device_type,
        geo_region=geo_region,
        geo_city=geo_city,
        call_status=call_status,
    )
    return _get_repositioning_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=resolved_filters,
    )


__all__ = [
    "CallFilters",
    "get_brands_df",
    "get_dimension_options",
    "get_calls_df",
    "get_intent_summary_df",
    "get_quality_trends_df",
    "get_confusion_patterns_df",
    "get_repositioning_df",
    "get_call_detail_by_numeric_id",
    "get_call_detail_by_invoca_id",
    "get_review_queue_df",
    "save_review_result",
    "get_pipeline_snapshot",
    "get_data_freshness_snapshot",
]
