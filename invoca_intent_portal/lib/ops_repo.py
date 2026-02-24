"""Operational telemetry snapshots for dashboard status widgets."""

from __future__ import annotations

from typing import Any

import streamlit as st


def _table(client: Any, table_name: str) -> Any:
    return client.schema("invoca").table(table_name)


@st.cache_data(ttl=300, show_spinner=False)
def get_pipeline_snapshot(_client: Any) -> dict[str, dict[str, Any] | None]:
    rows = (
        _table(_client, "pipeline_run_log")
        .select(
            "id,workflow_name,run_context,started_at,finished_at,status,"
            "rows_discovered,rows_processed,rows_failed,error_summary,metadata"
        )
        .order("started_at", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )

    latest_by_context: dict[str, dict[str, Any]] = {}
    for row in rows:
        context = str(row.get("run_context") or "").strip().lower()
        if not context:
            continue
        if context not in latest_by_context:
            latest_by_context[context] = row

    latest = rows[0] if rows else None
    return {
        "latest": latest,
        "healthcheck": latest_by_context.get("healthcheck"),
        "discovery": latest_by_context.get("discovery"),
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_data_freshness_snapshot(_client: Any) -> dict[str, Any]:
    latest_call_row = (
        _table(_client, "calls")
        .select("updated_at,discovered_at,acquired_at,call_start_time,call_date_pt,status")
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    latest_analysis_row = (
        _table(_client, "analysis")
        .select("analyzed_at")
        .order("analyzed_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )

    call_row = latest_call_row[0] if latest_call_row else {}
    analysis_row = latest_analysis_row[0] if latest_analysis_row else {}

    return {
        "latest_call_updated_at": call_row.get("updated_at"),
        "latest_call_discovered_at": call_row.get("discovered_at"),
        "latest_call_acquired_at": call_row.get("acquired_at"),
        "latest_call_start_time": call_row.get("call_start_time"),
        "latest_call_date_pt": call_row.get("call_date_pt"),
        "latest_call_status": call_row.get("status"),
        "latest_analyzed_at": analysis_row.get("analyzed_at"),
    }
