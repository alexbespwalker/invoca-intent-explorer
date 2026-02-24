"""Typed filter models shared across dashboard modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CallFilters:
    """Filter state for calls and derived analysis views."""

    brand_code: str | None = None
    media_source: str | None = None
    campaign_name: str | None = None
    campaign_query: str | None = None
    publisher: str | None = None
    channel: str | None = None
    advertiser_name: str | None = None
    advertiser_query: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None
    device_type: str | None = None
    geo_region: str | None = None
    geo_city: str | None = None
    call_status: str | None = None
