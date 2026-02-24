"""Single data access module for Invoca Intent Explorer."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st


def _table(client: Any, table_name: str) -> Any:
    return client.schema("invoca").table(table_name)


def _as_df(data: list[dict[str, Any]]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


@st.cache_data(ttl=300, show_spinner=False)
def get_analyzed_calls(
    _client: Any,
    start_date: date,
    end_date: date,
    brand_code: str | None = None,
    limit: int = 500,
) -> pd.DataFrame:
    """Join calls + analysis into a single DataFrame."""
    query = (
        _table(_client, "calls")
        .select(
            "id,invoca_call_id,brand_code,advertiser_name,"
            "call_date_pt,call_start_time,duration_seconds,status,"
            "transcript_word_count"
        )
        .gte("call_date_pt", start_date.isoformat())
        .lte("call_date_pt", end_date.isoformat())
        .order("call_start_time", desc=True)
        .limit(limit)
    )
    if brand_code and brand_code.upper() != "ALL":
        query = query.eq("brand_code", brand_code)

    calls_rows = query.execute().data or []
    calls_df = _as_df(calls_rows)
    if calls_df.empty:
        return calls_df

    call_ids = calls_df["id"].tolist()
    analysis_rows = (
        _table(_client, "analysis")
        .select(
            "call_id,analyzed_at,caller_intent,intent_confidence,brand_confusion,"
            "confusion_signals,call_outcome,agent_quality_score,caller_sentiment,"
            "key_quotes,validation_passed"
        )
        .in_("call_id", call_ids)
        .order("analyzed_at", desc=True)
        .execute()
        .data
        or []
    )
    analysis_df = _as_df(analysis_rows)

    if not analysis_df.empty:
        analysis_df["analyzed_at"] = pd.to_datetime(
            analysis_df["analyzed_at"], utc=True, errors="coerce"
        )
        analysis_df = (
            analysis_df.sort_values("analyzed_at", ascending=False)
            .drop_duplicates(subset=["call_id"], keep="first")
        )

    if not analysis_df.empty:
        calls_df = calls_df.merge(
            analysis_df, how="left", left_on="id", right_on="call_id",
        )
    calls_df["call_start_time"] = pd.to_datetime(
        calls_df.get("call_start_time"), utc=True, errors="coerce"
    )
    if "call_date_pt" in calls_df.columns:
        calls_df["call_date_pt"] = pd.to_datetime(
            calls_df["call_date_pt"], errors="coerce"
        ).dt.date
    return calls_df


@st.cache_data(ttl=3600, show_spinner=False)
def get_brands(_client: Any) -> list[dict[str, str]]:
    """Active brands for sidebar selector."""
    rows = (
        _table(_client, "brands")
        .select("brand_code,brand_name")
        .eq("active", True)
        .order("priority", desc=False)
        .execute()
        .data
        or []
    )
    return rows


def get_call_detail(
    client: Any, call_id: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Single call + analysis rows for detail page.

    Accepts either a numeric DB id or an Invoca call ID string.
    """
    if call_id.isdigit():
        call_rows = (
            _table(client, "calls")
            .select("*")
            .eq("id", int(call_id))
            .limit(1)
            .execute()
            .data or []
        )
    else:
        call_rows = (
            _table(client, "calls")
            .select("*")
            .eq("invoca_call_id", call_id)
            .order("call_start_time", desc=True)
            .limit(1)
            .execute()
            .data or []
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
