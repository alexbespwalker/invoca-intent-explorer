"""Analysis and trend repository helpers."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from invoca_intent_portal.lib.calls_repo import get_calls_df
from invoca_intent_portal.lib.filter_state import CallFilters


def _week_start_series(call_date_series: pd.Series) -> pd.Series:
    week_start = pd.to_datetime(call_date_series, errors="coerce")
    return week_start - pd.to_timedelta(week_start.dt.weekday, unit="D")


def _get_analyzed_calls_df(
    client: Any,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    calls_df = get_calls_df(
        client,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        limit=50000,
    )
    if calls_df.empty:
        return pd.DataFrame()

    analyzed = calls_df[calls_df["caller_intent"].notna()].copy()
    if analyzed.empty:
        return pd.DataFrame()
    return analyzed


def get_intent_summary_df(
    client: Any,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    analyzed = _get_analyzed_calls_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
    )
    if analyzed.empty:
        return pd.DataFrame()

    analyzed["call_date"] = pd.to_datetime(analyzed["call_date_pt"], errors="coerce").dt.date
    grouped = (
        analyzed.groupby(["brand_code", "call_date", "caller_intent", "call_outcome"], dropna=False, as_index=False)
        .agg(
            total_calls=("id", "size"),
            avg_intent_confidence=("intent_confidence", "mean"),
            avg_agent_quality=("agent_quality_score", "mean"),
            brand_confusion_calls=("brand_confusion", lambda x: int(pd.Series(x).fillna(False).sum())),
        )
        .sort_values(["call_date", "total_calls"], ascending=[True, False])
    )
    grouped["avg_intent_confidence"] = grouped["avg_intent_confidence"].round(2)
    grouped["avg_agent_quality"] = grouped["avg_agent_quality"].round(2)
    grouped["call_date"] = pd.to_datetime(grouped["call_date"])
    return grouped


def get_quality_trends_df(
    client: Any,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    analyzed = _get_analyzed_calls_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
    )
    if analyzed.empty:
        return pd.DataFrame()

    analyzed["call_date"] = pd.to_datetime(analyzed["call_date_pt"], errors="coerce")
    analyzed["week_start"] = _week_start_series(analyzed["call_date"])

    grouped = (
        analyzed.groupby(["brand_code", "week_start"], as_index=False)
        .agg(
            analyzed_calls=("id", "size"),
            avg_agent_quality=("agent_quality_score", "mean"),
            avg_intent_confidence=("intent_confidence", "mean"),
            confusion_rate_pct=("brand_confusion", lambda x: float(pd.Series(x).fillna(False).mean() * 100)),
            validation_pass_rate_pct=("validation_passed", lambda x: float(pd.Series(x).fillna(False).mean() * 100)),
        )
        .sort_values("week_start")
    )
    for col in ("avg_agent_quality", "avg_intent_confidence", "confusion_rate_pct", "validation_pass_rate_pct"):
        grouped[col] = grouped[col].round(2)
    return grouped


def get_confusion_patterns_df(
    client: Any,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    calls_df = get_calls_df(
        client,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        limit=50000,
    )
    if calls_df.empty or "confusion_signals" not in calls_df.columns:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for _, row in calls_df.iterrows():
        signals = row.get("confusion_signals") or []
        if not isinstance(signals, list) or not signals:
            continue
        call_date = pd.to_datetime(row.get("call_date_pt"), errors="coerce")
        week_start = call_date - pd.to_timedelta(call_date.weekday(), unit="D") if pd.notna(call_date) else pd.NaT
        for signal in signals:
            if signal is None:
                continue
            sig = str(signal).strip()
            if not sig:
                continue
            rows.append(
                {
                    "brand_code": row.get("brand_code"),
                    "week_start": week_start,
                    "confusion_signal": sig,
                    "call_id": row.get("id"),
                }
            )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    grouped = (
        df.groupby(["brand_code", "week_start", "confusion_signal"], as_index=False)
        .agg(signal_count=("confusion_signal", "size"), affected_calls=("call_id", pd.Series.nunique))
        .sort_values(["week_start", "signal_count"], ascending=[True, False])
    )
    return grouped


def get_repositioning_df(
    client: Any,
    start_date: date,
    end_date: date,
    filters: CallFilters | None = None,
) -> pd.DataFrame:
    analyzed = _get_analyzed_calls_df(
        client=client,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
    )
    if analyzed.empty:
        return pd.DataFrame()

    analyzed["call_date"] = pd.to_datetime(analyzed["call_date_pt"], errors="coerce")
    analyzed["week_start"] = _week_start_series(analyzed["call_date"])

    grouped_rows: list[dict[str, Any]] = []
    for (brand, week_start), group in analyzed.groupby(["brand_code", "week_start"], dropna=False):
        attempts = int((group["agent_repositioning_attempted"] == True).sum())  # noqa: E712
        successes = int((group["agent_repositioning_successful"] == True).sum())  # noqa: E712
        success_rate_pct = round((successes / attempts) * 100, 2) if attempts > 0 else 0.0
        techniques = group["repositioning_technique"].dropna().astype(str).str.strip()
        techniques = techniques[techniques != ""]
        top_technique = techniques.mode().iloc[0] if not techniques.empty else None
        grouped_rows.append(
            {
                "brand_code": brand,
                "week_start": week_start,
                "attempts": attempts,
                "successes": successes,
                "success_rate_pct": success_rate_pct,
                "top_technique": top_technique,
            }
        )

    df = pd.DataFrame(grouped_rows)
    if not df.empty:
        df = df.sort_values("week_start")
    return df
