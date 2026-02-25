"""Invoca Intent Explorer — home page."""

from __future__ import annotations

from datetime import datetime, timedelta
import html as _html
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.auth import check_password, logout
from invoca_intent_portal.lib.supabase_client import require_supabase_client
from invoca_intent_portal.lib.db import get_analyzed_calls, get_brands, get_call_detail
from invoca_intent_portal.lib.ui import (
    apply_base_styles, apply_chart_defaults, CHART_COLORS, COLORS,
    section_divider, FLAG_STYLES, val,
)


def _fmt(val: str) -> str:
    """Format snake_case DB values into readable labels."""
    return val.replace("_", " ").title() if val else val

st.set_page_config(
    page_title="Invoca Intent Explorer",
    page_icon="\U0001F4DE",
    layout="wide",
)
apply_base_styles()
check_password()

st.markdown(
    '<div style="height:3px;background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
    'border-radius:2px;margin-bottom:1rem;"></div>',
    unsafe_allow_html=True,
)
st.title("Invoca Intent Explorer")
st.caption("BC call analysis  \u2022  caller intent  \u2022  brand confusion  \u2022  agent quality")

client = require_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

# ── Sidebar: 2 filters ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:600;letter-spacing:0.1em;'
        'text-transform:uppercase;color:#64748b;margin-bottom:0.8rem;">'
        'Walker Advertising</div>',
        unsafe_allow_html=True,
    )

    # User info + logout
    _user_display = st.session_state.get("user_display_name") or st.session_state.get("user_email")
    if _user_display:
        st.markdown(
            f'<div style="font-size:0.78rem;color:{COLORS["text_secondary"]};'
            f'margin-bottom:0.3rem;">'
            f'{_html.escape(str(_user_display))}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="logout_btn"):
            logout()
        st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)

    st.header("Filters")

    date_preset = st.selectbox(
        "Date Range",
        options=["Yesterday", "Last 7 Days", "Last 14 Days", "Custom"],
        index=1,
    )

    if date_preset == "Yesterday":
        start_date = pt_today - timedelta(days=1)
        end_date = start_date
    elif date_preset == "Last 7 Days":
        start_date = pt_today - timedelta(days=6)
        end_date = pt_today
    elif date_preset == "Last 14 Days":
        start_date = pt_today - timedelta(days=13)
        end_date = pt_today
    else:
        date_range = st.date_input(
            "Date Range (PT)",
            value=(pt_today - timedelta(days=13), pt_today),
            max_value=pt_today,
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range[0], date_range[1]
        else:
            start_date = pt_today - timedelta(days=13)
            end_date = pt_today

    brands = get_brands(client)
    brand_options = ["ALL"] + [b["brand_code"] for b in brands]
    brand_labels = {"ALL": "All Brands"}
    for b in brands:
        brand_labels[b["brand_code"]] = f"{b['brand_code']} - {b['brand_name']}"

    selected_brand = st.selectbox(
        "Brand",
        options=brand_options,
        index=0,
        format_func=lambda x: brand_labels.get(x, x),
    )

    brand_filter = None if selected_brand == "ALL" else selected_brand

# ── Load data ────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading data..."):
        calls_df = get_analyzed_calls(
            client,
            start_date=start_date,
            end_date=end_date,
            brand_code=brand_filter,
            limit=5000,
        )
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if calls_df.empty:
    st.warning("No calls found for this filter window.")
    st.stop()

# ── KPI row (4 metrics) ─────────────────────────────────────────────────
analyzed_mask = calls_df["caller_intent"].notna()
analyzed_count = int(analyzed_mask.sum())
total_count = len(calls_df)

confusion_rate = 0.0
if analyzed_count > 0:
    confusion_rate = float(
        calls_df.loc[analyzed_mask, "brand_confusion"].fillna(False).mean() * 100
    )

avg_quality = 0.0
if "agent_quality_score" in calls_df.columns:
    quality_vals = calls_df["agent_quality_score"].dropna()
    if len(quality_vals) > 0:
        avg_quality = float(quality_vals.mean())

top_intent = "n/a"
top_intent_pct = ""
if analyzed_count > 0:
    intent_counts = calls_df.loc[analyzed_mask, "caller_intent"].value_counts()
    if not intent_counts.empty:
        raw_intent = str(intent_counts.index[0])
        top_intent = raw_intent.replace("_", " ").title()
        # Abbreviate long intents for the KPI card
        _abbrev = {"New Case Inquiry": "New Case", "Existing Case Status": "Existing"}
        top_intent = _abbrev.get(top_intent, top_intent)
        top_intent_pct = f"{intent_counts.iloc[0] / analyzed_count * 100:.0f}%"

repo_success_rate = "n/a"
if "agent_repositioning_attempted" in calls_df.columns:
    attempted = calls_df["agent_repositioning_attempted"].fillna(False)
    successful = calls_df.get("agent_repositioning_successful", pd.Series(dtype=bool)).fillna(False)
    attempted_count = int(attempted.sum())
    if attempted_count > 0:
        repo_success_rate = f"{successful.sum() / attempted_count * 100:.0f}%"

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Calls", f"{total_count:,}")
m2.metric("Confusion Rate", f"{confusion_rate:.1f}%")
m3.metric("Avg Quality", f"{avg_quality:.1f}" if avg_quality else "n/a")
m4.metric("Top Intent", top_intent, delta=top_intent_pct if top_intent_pct else None)
m5.metric("Repo Success", repo_success_rate)

# ── Charts (2 columns) ──────────────────────────────────────────────────
chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    st.subheader("Intent Distribution")
    if analyzed_count > 0:
        pie_data = (
            calls_df.loc[analyzed_mask, "caller_intent"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("caller_intent")
            .reset_index(name="count")
        )
        pie_data["label"] = pie_data["caller_intent"].apply(_fmt)
        # Build explicit color mapping so pie slices get our palette
        label_names = pie_data["label"].tolist()
        label_color_map = {n: CHART_COLORS[i % len(CHART_COLORS)] for i, n in enumerate(label_names)}
        fig_pie = px.pie(
            pie_data, names="label", values="count", hole=0.45,
            color="label", color_discrete_map=label_color_map,
        )
        apply_chart_defaults(fig_pie)
        fig_pie.update_traces(textfont_color="#e2e8f0", textfont_size=12)
        fig_pie.update_layout(legend_title_text="")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No analyzed calls in current window.")

with chart_col_2:
    st.subheader("Outcome Breakdown")
    if "call_outcome" in calls_df.columns and calls_df["call_outcome"].notna().any():
        out_data = (
            calls_df["call_outcome"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("call_outcome")
            .reset_index(name="count")
        )
        out_data["label"] = out_data["call_outcome"].apply(_fmt)
        fig_out = px.bar(
            out_data, y="label", x="count", orientation="h",
            color_discrete_sequence=[CHART_COLORS[0]],
        )
        apply_chart_defaults(fig_out)
        fig_out.update_layout(yaxis_title=None, xaxis_title=None, margin=dict(l=180, t=20, b=40, r=20))
        fig_out.update_traces(marker_cornerradius=4)
        st.plotly_chart(fig_out, use_container_width=True)
    else:
        st.info("No analyzed outcomes in current window.")

# ── Case Type + Daily Trend (2 columns) ──────────────────────────────────
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Case Type Distribution")
    if "case_type" in calls_df.columns and calls_df["case_type"].notna().any():
        case_data = (
            calls_df["case_type"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("case_type")
            .reset_index(name="count")
        )
        case_data["label"] = case_data["case_type"].apply(_fmt)
        fig_case = px.bar(
            case_data, y="label", x="count", orientation="h",
            color_discrete_sequence=[CHART_COLORS[1]],
        )
        apply_chart_defaults(fig_case)
        fig_case.update_layout(yaxis_title=None, xaxis_title=None, margin=dict(l=180, t=20, b=40, r=20))
        fig_case.update_traces(marker_cornerradius=4)
        st.plotly_chart(fig_case, use_container_width=True)
    else:
        st.info("No case type data in current window.")

with row2_col2:
    st.subheader("Daily Intent Trend")
    if analyzed_count > 0:
        trend_base = calls_df.loc[analyzed_mask].copy()
        trend_base["call_date"] = pd.to_datetime(
            trend_base["call_date_pt"], errors="coerce"
        )
        trend_df = (
            trend_base.groupby(["call_date", "caller_intent"], as_index=False)
            .size()
            .rename(columns={"size": "calls"})
        )
        trend_df["intent_label"] = trend_df["caller_intent"].apply(_fmt)
        fig_trend = px.line(
            trend_df, x="call_date", y="calls", color="intent_label",
            color_discrete_sequence=CHART_COLORS, markers=True,
        )
        apply_chart_defaults(fig_trend)
        fig_trend.update_layout(yaxis_title="Calls", xaxis_title="", legend_title_text="")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No analyzed data for trend chart.")

# ── Call table ───────────────────────────────────────────────────────────
st.subheader("Call Table")
st.caption("Select a row to preview its transcript below.")

# Extract first key quote as intent quote
if "key_quotes" in calls_df.columns:
    calls_df["intent_quote"] = calls_df["key_quotes"].apply(
        lambda q: q[0]["quote"] if isinstance(q, list) and q and isinstance(q[0], dict) and "quote" in q[0] else ""
    )
else:
    calls_df["intent_quote"] = ""

show_cols = [
    "invoca_call_id", "call_date_pt", "caller_intent",
    "intent_quote", "intent_confidence", "brand_confusion",
    "agent_quality_score", "call_outcome", "case_type",
    "agent_repositioning_successful", "caller_sentiment",
    "duration_seconds",
]
existing_cols = [c for c in show_cols if c in calls_df.columns]
display_df = calls_df[existing_cols].copy()

# Format snake_case values in key columns
for col in ["caller_intent", "call_outcome", "case_type", "caller_sentiment"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda v: _fmt(str(v)) if pd.notna(v) else "")

# Rename columns to human-readable headers
display_df = display_df.rename(columns={
    "invoca_call_id": "Call ID",
    "call_date_pt": "Date",
    "caller_intent": "Intent",
    "intent_quote": "Intent Quote",
    "intent_confidence": "Confidence",
    "brand_confusion": "Brand Confused",
    "agent_quality_score": "Quality",
    "call_outcome": "Outcome",
    "case_type": "Case Type",
    "agent_repositioning_successful": "Repo OK",
    "caller_sentiment": "Sentiment",
    "duration_seconds": "Duration (s)",
})

# Map display rows back to DB IDs for on-click lookup
row_id_map = calls_df.loc[display_df.index, "id"].tolist()

selection = st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

# ── Inline call detail panel ─────────────────────────────────────────
if selection.selection.rows:
    selected_idx = selection.selection.rows[0]
    selected_call_id = str(row_id_map[selected_idx])
    selected_row = display_df.iloc[selected_idx]

    call_detail, analyses = get_call_detail(client, selected_call_id)

    # Gradient divider
    st.markdown(
        '<div style="height:2px;margin:1.5rem 0 1rem 0;'
        'background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
        'border-radius:1px;opacity:0.5;"></div>',
        unsafe_allow_html=True,
    )

    if call_detail:
        # Section label
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;'
            'text-transform:uppercase;color:#64748b;margin-bottom:0.5rem;">'
            'Call Detail</div>',
            unsafe_allow_html=True,
        )

        # Metadata header bar
        call_label = _html.escape(str(selected_row.get("Call ID", selected_call_id)))
        call_date = _html.escape(str(selected_row.get("Date", "")))
        call_intent = _html.escape(str(selected_row.get("Intent", "")))
        call_dur = _html.escape(str(selected_row.get("Duration (s)", "")))

        st.markdown(
            f'<div style="display:flex;gap:2rem;align-items:center;'
            f'background:linear-gradient(135deg,#1e293b 0%,#273548 100%);'
            f'border:1px solid #334155;border-radius:12px;'
            f'padding:0.8rem 1.2rem;margin-bottom:0.8rem;">'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Call ID</span><br>'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.88rem;'
            f'color:#22d3ee;">{call_label}</span></div>'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Date</span><br>'
            f'<span style="font-size:0.88rem;color:#e2e8f0;">{call_date}</span></div>'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Intent</span><br>'
            f'<span style="display:inline-block;margin-top:2px;padding:1px 8px;'
            f'background:#164e6380;border-radius:5px;font-size:0.84rem;'
            f'color:#22d3ee;">{call_intent}</span></div>'
            f'<div><span style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:#64748b;">Duration</span><br>'
            f'<span style="font-size:0.88rem;color:#e2e8f0;">{call_dur}s</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Metadata grid (Date/Start/Duration | Advertiser/Campaign/WordCount)
        _meta_col1, _meta_col2 = st.columns(2)
        with _meta_col1:
            st.markdown(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 1.5rem;'
                f'font-size:0.88rem;color:{COLORS["text_secondary"]};">'
                f'<span style="color:{COLORS["text_muted"]};">Date (PT)</span>'
                f'<span style="color:{COLORS["text_primary"]};">{_html.escape(val(call_detail.get("call_date_pt")))}</span>'
                f'<span style="color:{COLORS["text_muted"]};">Call Start</span>'
                f'<span style="color:{COLORS["text_primary"]};">{_html.escape(val(call_detail.get("call_start_time")))}</span>'
                f'<span style="color:{COLORS["text_muted"]};">Duration</span>'
                f'<span style="color:{COLORS["text_primary"]};">{_html.escape(val(call_detail.get("duration_seconds")))} sec</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with _meta_col2:
            st.markdown(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 1.5rem;'
                f'font-size:0.88rem;color:{COLORS["text_secondary"]};">'
                f'<span style="color:{COLORS["text_muted"]};">Advertiser</span>'
                f'<span style="color:{COLORS["text_primary"]};">{_html.escape(val(call_detail.get("advertiser_name")))}</span>'
                f'<span style="color:{COLORS["text_muted"]};">Campaign</span>'
                f'<span style="color:{COLORS["text_primary"]};">{_html.escape(val(call_detail.get("campaign_name")))}</span>'
                f'<span style="color:{COLORS["text_muted"]};">Word Count</span>'
                f'<span style="color:{COLORS["text_primary"]};">{_html.escape(val(call_detail.get("transcript_word_count")))}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Transcript
        _transcript_text = call_detail.get("transcript_text")
        if _transcript_text:
            section_divider("Transcript")
            _word_count = len(_transcript_text.split())
            st.markdown(
                f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:0.4rem;'
                f'font-family:\'JetBrains Mono\',monospace;">'
                f'{_word_count:,} words</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                "<style>"
                "div[data-testid='stCode'] {"
                "  border: 1px solid #334155;"
                "  border-radius: 10px;"
                "  overflow: hidden;"
                "}"
                "div[data-testid='stCode'] pre {"
                "  max-height: 420px;"
                "  overflow-y: auto;"
                "  background: #0f172a !important;"
                "  color: #cbd5e1 !important;"
                "  font-family: 'JetBrains Mono', monospace !important;"
                "  font-size: 0.82rem !important;"
                "  line-height: 1.7 !important;"
                "  padding: 1rem 1.2rem !important;"
                "}"
                "div[data-testid='stCode'] pre::-webkit-scrollbar {"
                "  width: 6px;"
                "}"
                "div[data-testid='stCode'] pre::-webkit-scrollbar-track {"
                "  background: #1e293b;"
                "}"
                "div[data-testid='stCode'] pre::-webkit-scrollbar-thumb {"
                "  background: #475569;"
                "  border-radius: 3px;"
                "}"
                "</style>",
                unsafe_allow_html=True,
            )
            st.code(_transcript_text, language=None, wrap_lines=True)
        else:
            section_divider("Transcript")
            st.warning("No transcript text on this call yet.")

        # ── Analysis sections ────────────────────────────────────────
        section_divider("Analysis")
        if analyses:
            latest = analyses[0]

            # 5 analysis metrics
            a1, a2, a3, a4, a5 = st.columns(5)
            a1.metric("Intent", _fmt(val(latest.get("caller_intent"))))
            a2.metric("Confidence", val(latest.get("intent_confidence")))
            a3.metric("Outcome", _fmt(val(latest.get("call_outcome"))))
            a4.metric("Agent Quality", val(latest.get("agent_quality_score")))
            a5.metric("Case Type", _fmt(val(latest.get("case_type"))))

            # Detail chips (brand confusion, sentiment, validation)
            detail_items = []
            brand_confused = latest.get("brand_confusion")
            if brand_confused:
                detail_items.append(
                    '<span style="background:#7f1d1d;color:#fca5a5;padding:3px 10px;'
                    'border-radius:6px;font-size:0.82em;">Brand Confused</span>'
                )
            else:
                detail_items.append(
                    f'<span style="background:{COLORS["bg_elevated"]};color:{COLORS["text_muted"]};'
                    f'padding:3px 10px;border-radius:6px;font-size:0.82em;">No Brand Confusion</span>'
                )

            sentiment = val(latest.get("caller_sentiment"))
            sent_color = {"positive": "#34d399", "negative": "#fb7185", "neutral": "#94a3b8"}.get(
                sentiment.lower(), COLORS["text_secondary"]
            )
            detail_items.append(
                f'<span style="background:{COLORS["bg_elevated"]};color:{sent_color};'
                f'padding:3px 10px;border-radius:6px;font-size:0.82em;">'
                f'Sentiment: {_html.escape(_fmt(sentiment))}</span>'
            )

            validation = latest.get("validation_passed")
            if validation:
                detail_items.append(
                    '<span style="background:#064e3b;color:#6ee7b7;padding:3px 10px;'
                    'border-radius:6px;font-size:0.82em;">Validated</span>'
                )

            st.markdown(
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:0.5rem 0 1rem 0;">'
                f'{"".join(detail_items)}</div>',
                unsafe_allow_html=True,
            )

            # Agent repositioning (conditional)
            repo_attempted = latest.get("agent_repositioning_attempted")
            if repo_attempted is not None:
                section_divider("Agent Repositioning")
                r1, r2, r3 = st.columns(3)
                attempted_color = COLORS["emerald"] if repo_attempted else COLORS["text_muted"]
                successful = latest.get("agent_repositioning_successful")
                success_color = COLORS["emerald"] if successful else COLORS["rose"]

                r1.markdown(
                    f'<div style="font-size:0.85rem;color:{COLORS["text_muted"]};">Attempted</div>'
                    f'<div style="font-size:1.1rem;font-weight:600;color:{attempted_color};">'
                    f'{"Yes" if repo_attempted else "No"}</div>',
                    unsafe_allow_html=True,
                )
                r2.markdown(
                    f'<div style="font-size:0.85rem;color:{COLORS["text_muted"]};">Successful</div>'
                    f'<div style="font-size:1.1rem;font-weight:600;color:{success_color};">'
                    f'{"Yes" if successful else "No"}</div>',
                    unsafe_allow_html=True,
                )
                technique = val(latest.get("repositioning_technique"))
                r3.markdown(
                    f'<div style="font-size:0.85rem;color:{COLORS["text_muted"]};">Technique</div>'
                    f'<div style="font-size:0.88rem;color:{COLORS["text_primary"]};">'
                    f'{_html.escape(technique)}</div>',
                    unsafe_allow_html=True,
                )

            # Flags (conditional)
            flags = latest.get("flags")
            if flags and isinstance(flags, list) and len(flags) > 0:
                _default_style = f"background:{COLORS['bg_elevated']};color:{COLORS['text_secondary']};"
                flag_html = " ".join(
                    f'<span style="{FLAG_STYLES.get(f, (_default_style,))[0]}'
                    f'padding:3px 10px;border-radius:6px;font-size:0.82em;font-weight:500;">'
                    f'{FLAG_STYLES.get(f, (None, _fmt(f)))[1]}</span>'
                    for f in flags
                )
                st.markdown(
                    f'<div style="margin:0.8rem 0;"><span style="font-size:0.78rem;font-weight:600;'
                    f'letter-spacing:0.06em;text-transform:uppercase;color:{COLORS["text_muted"]};">'
                    f'FLAGS</span> {flag_html}</div>',
                    unsafe_allow_html=True,
                )

            # Confusion signals (conditional)
            signals = latest.get("confusion_signals")
            if signals and isinstance(signals, list) and len(signals) > 0:
                section_divider("Confusion Signals")
                for sig in signals:
                    st.markdown(
                        f'<div style="padding:0.4rem 0.8rem;margin:0.3rem 0;'
                        f'border-left:3px solid {COLORS["rose"]};'
                        f'color:{COLORS["text_secondary"]};font-size:0.88rem;">'
                        f'{_html.escape(str(sig))}</div>',
                        unsafe_allow_html=True,
                    )

            # Key quotes (conditional)
            quotes = latest.get("key_quotes")
            if quotes and isinstance(quotes, list) and len(quotes) > 0:
                section_divider("Key Quotes")
                for q in quotes:
                    if isinstance(q, dict):
                        quote_text = _html.escape(q.get("quote", ""))
                        st.markdown(
                            f'<div style="padding:0.6rem 1rem;margin:0.5rem 0;'
                            f'border-left:3px solid {COLORS["accent"]};'
                            f'background:{COLORS["bg_elevated"]};border-radius:0 8px 8px 0;'
                            f'font-style:italic;color:{COLORS["text_primary"]};font-size:0.88rem;">'
                            f'&ldquo;{quote_text}&rdquo;</div>',
                            unsafe_allow_html=True,
                        )
                        ctx = q.get("context")
                        if ctx:
                            st.caption(ctx)
                    elif isinstance(q, str):
                        st.markdown(
                            f'<div style="padding:0.6rem 1rem;margin:0.5rem 0;'
                            f'border-left:3px solid {COLORS["accent"]};'
                            f'background:{COLORS["bg_elevated"]};border-radius:0 8px 8px 0;'
                            f'font-style:italic;color:{COLORS["text_primary"]};font-size:0.88rem;">'
                            f'&ldquo;{_html.escape(q)}&rdquo;</div>',
                            unsafe_allow_html=True,
                        )

            # Raw Analysis JSON expander
            with st.expander("Raw Analysis JSON", expanded=False):
                raw = latest.get("raw_analysis")
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except Exception:
                        pass
                st.json(raw)

            # Analysis History expander (if >1 analysis)
            if len(analyses) > 1:
                with st.expander("Analysis History", expanded=False):
                    st.dataframe(analyses, use_container_width=True, hide_index=True)
        else:
            st.info("No analysis rows found for this call.")
    else:
        st.error(f"Could not load call {selected_call_id}.")

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "\U0001F4E5 Export CSV",
    data=csv_bytes,
    file_name=f"invoca_calls_{start_date}_{end_date}.csv",
    mime="text/csv",
)
