"""Review queue and calibration persistence helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def _table(client: Any, table_name: str) -> Any:
    return client.schema("invoca").table(table_name)


def _as_df(data: list[dict[str, Any]]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def get_review_queue_df(client: Any, status: str = "pending", limit: int = 200) -> pd.DataFrame:
    query = _table(client, "review_queue").select("*").order("created_at", desc=True).limit(limit)
    if status and status.lower() != "all":
        query = query.eq("status", status)

    queue_rows = query.execute().data or []
    queue_df = _as_df(queue_rows)
    if queue_df.empty:
        return queue_df

    analysis_ids = queue_df["analysis_id"].dropna().astype(int).tolist()
    analysis_rows = (
        _table(client, "analysis")
        .select(
            "id,call_id,caller_intent,intent_confidence,brand_confusion,"
            "call_outcome,agent_quality_score,validation_passed,analyzed_at"
        )
        .in_("id", analysis_ids)
        .execute()
        .data
        or []
    )
    analysis_df = _as_df(analysis_rows)

    call_ids = analysis_df["call_id"].dropna().astype(int).tolist() if not analysis_df.empty else []
    calls_rows = (
        _table(client, "calls")
        .select("id,invoca_call_id,brand_code,call_start_time,media_source,campaign_name,publisher,channel")
        .in_("id", call_ids)
        .execute()
        .data
        or []
    )
    calls_df = _as_df(calls_rows)

    df = queue_df.merge(analysis_df, how="left", left_on="analysis_id", right_on="id", suffixes=("_queue", "_analysis"))
    df = df.merge(calls_df, how="left", left_on="call_id", right_on="id", suffixes=("", "_call"))
    return df


def save_review_result(
    client: Any,
    queue_id: int,
    reviewer: str,
    reviewer_score: int | None,
    accepted: bool,
    notes: str,
    disagreements: list[str],
    new_status: str,
) -> None:
    result_payload = {
        "queue_id": queue_id,
        "reviewer": reviewer,
        "reviewer_score": reviewer_score,
        "accepted": accepted,
        "notes": notes or None,
        "disagreements": disagreements or [],
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    _table(client, "review_results").upsert(result_payload, on_conflict="queue_id").execute()

    queue_payload = {
        "status": new_status,
        "assigned_to": reviewer or None,
        "reviewed_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    _table(client, "review_queue").update(queue_payload).eq("id", queue_id).execute()
