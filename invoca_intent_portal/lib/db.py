"""Data access module for Call Intent & Confusion Portal.

Reads from public.analysis_results (Walker Brain, read-only).
Auth writes go to invoca.portal_users / invoca.portal_sessions (portal's own tables).
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st


_LIST_COLS = (
    "id, source_transcript_id, call_start_date, call_duration_seconds, "
    "primary_topic, primary_intent, outcome, emotional_tone, "
    "quality_score, case_type, summary, key_quote, "
    "category_confusion, process_confusion_points, "
    "brand_reference, other_brands_mentioned, channel_referenced, "
    "agent_empathy_score, agent_education_quality, agent_closing_effectiveness, "
    "confidence_score, needs_review, review_reason, original_language"
)


def _as_df(data: list[dict[str, Any]]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


@st.cache_data(ttl=300, show_spinner=False)
def get_calls(
    _client: Any,
    start_date: date,
    end_date: date,
    limit: int = 5000,
) -> pd.DataFrame:
    """Fetch calls from public.analysis_results (read-only)."""
    rows = (
        _client.table("analysis_results")
        .select(_LIST_COLS)
        .gte("call_start_date", f"{start_date.isoformat()}T00:00:00")
        .lte("call_start_date", f"{end_date.isoformat()}T23:59:59")
        .order("call_start_date", desc=True)
        .limit(limit)
        .execute()
        .data or []
    )
    df = _as_df(rows)
    if not df.empty and "call_start_date" in df.columns:
        df["call_start_date"] = pd.to_datetime(
            df["call_start_date"], utc=True, errors="coerce"
        )
        df["call_date"] = (
            df["call_start_date"]
            .dt.tz_convert("America/Los_Angeles")
            .dt.date
        )
    return df


def get_transcript(client: Any, call_id: int) -> str | None:
    """Fetch transcript for a single call (lazy-loaded)."""
    rows = (
        client.table("analysis_results")
        .select("transcript_original")
        .eq("id", call_id)
        .limit(1)
        .execute()
        .data or []
    )
    if rows:
        return rows[0].get("transcript_original")
    return None


# ── Auth helpers (write to invoca.portal_users / invoca.portal_sessions) ──


def authenticate_user(
    client: Any, email: str, password: str,
) -> dict[str, Any] | None:
    """Authenticate via RPC. Returns user dict or None."""
    resp = client.rpc(
        "authenticate_portal_user",
        {"p_email": email, "p_password": password},
    ).execute()
    rows = resp.data or []
    return rows[0] if rows else None


def create_session(client: Any, user_id: int) -> str:
    """Create a DB-backed session token."""
    resp = client.rpc(
        "create_portal_session",
        {"p_user_id": user_id},
    ).execute()
    return resp.data


def validate_session(
    client: Any, token: str,
) -> dict[str, Any] | None:
    """Validate a session token. Returns user dict or None."""
    resp = client.rpc(
        "validate_portal_session",
        {"p_token": token},
    ).execute()
    rows = resp.data or []
    return rows[0] if rows else None


def delete_session(client: Any, token: str) -> None:
    """Delete a session (logout)."""
    client.rpc(
        "delete_portal_session",
        {"p_token": token},
    ).execute()
