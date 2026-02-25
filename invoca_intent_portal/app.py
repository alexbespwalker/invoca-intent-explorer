"""Invoca Intent Explorer — call review tool."""

from __future__ import annotations

from datetime import datetime, timedelta
import html as _html
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.auth import check_password, logout
from invoca_intent_portal.lib.supabase_client import require_supabase_client
from invoca_intent_portal.lib.db import get_analyzed_calls, get_brands, get_call_detail
from invoca_intent_portal.lib.ui import (
    apply_base_styles, apply_chart_defaults, chart_title, CHART_COLORS, COLORS,
    section_divider, call_card, call_detail_panel, _fmt, intent_pill, INTENT_COLORS,
)


st.set_page_config(
    page_title="Invoca Intent Explorer",
    page_icon="\U0001F4DE",
    layout="wide",
)
apply_base_styles()
check_password()

st.markdown(
    '<div style="height:2px;background:linear-gradient(90deg,#22d3ee 0%,#0ea5e9 40%,#a78bfa 70%,#f59e0b 100%);'
    'border-radius:2px;margin-bottom:1.2rem;opacity:0.85;"></div>',
    unsafe_allow_html=True,
)
st.title("Invoca Intent Explorer")
st.caption("BC call review  \u2022  caller intent  \u2022  brand confusion  \u2022  agent quality")

client = require_supabase_client()
pt_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()

# ── Sidebar: filters ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:600;letter-spacing:0.1em;'
        'text-transform:uppercase;color:#64748b;margin-bottom:0.8rem;">'
        'Walker Advertising</div>',
        unsafe_allow_html=True,
    )

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
        options=["Yesterday", "Last 7 Days", "Last 14 Days", "Last 30 Days", "Custom"],
        index=2,
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
    elif date_preset == "Last 30 Days":
        start_date = pt_today - timedelta(days=29)
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

    # Intent filter
    intent_filter = st.multiselect(
        "Intent",
        options=list(INTENT_COLORS.keys()),
        format_func=_fmt,
        default=[],
        help="Filter to specific intents",
    )

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
except Exception:
    st.error("Error loading data. Please try again or check your filters.")
    st.stop()

if calls_df.empty:
    st.warning("No calls found for this filter window.")
    st.stop()

# Apply intent filter
if intent_filter:
    calls_df = calls_df[calls_df["caller_intent"].isin(intent_filter)]
    if calls_df.empty:
        st.warning("No calls match the selected intent filter.")
        st.stop()

# ── KPI row (4 metrics) ─────────────────────────────────────────────────
analyzed_mask = calls_df["caller_intent"].notna()
analyzed_count = int(analyzed_mask.sum())
total_count = len(calls_df)

# Lead rate: % of injury_new_case
lead_count = 0
lead_rate = 0.0
if analyzed_count > 0:
    lead_count = int((calls_df.loc[analyzed_mask, "caller_intent"] == "injury_new_case").sum())
    lead_rate = lead_count / analyzed_count * 100

# Confusion rate
confusion_rate = 0.0
if analyzed_count > 0:
    confusion_rate = float(
        calls_df.loc[analyzed_mask, "brand_confusion"].fillna(False).mean() * 100
    )

# Needs review: low confidence
needs_review = 0
if "intent_confidence" in calls_df.columns:
    needs_review = int(
        (calls_df["intent_confidence"].fillna(0) < 80).sum()
    )

m1, m2, m3, m4 = st.columns(4)
m1.metric("Calls", f"{total_count:,}")
m2.metric("Lead Rate", f"{lead_rate:.0f}%")
m3.metric("Brand Confusion", f"{confusion_rate:.0f}%")
m4.metric("Needs Review", f"{needs_review:,}")

# ── CSV export ───────────────────────────────────────────────────────────
# Build export dataframe from source data
export_cols = [
    "invoca_call_id", "call_date_pt", "caller_intent", "caller_situation",
    "intent_confidence", "brand_confusion", "call_outcome", "case_type",
    "agent_quality_score", "caller_sentiment", "duration_seconds",
]
existing_export_cols = [c for c in export_cols if c in calls_df.columns]
export_df = calls_df[existing_export_cols].copy()
for col in ["caller_intent", "call_outcome", "case_type", "caller_sentiment"]:
    if col in export_df.columns:
        export_df[col] = export_df[col].apply(lambda v: _fmt(str(v)) if pd.notna(v) else "")
export_df.columns = [_fmt(c) for c in export_df.columns]

csv_bytes = export_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "\U0001F4E5 Export CSV",
    data=csv_bytes,
    file_name=f"invoca_calls_{start_date}_{end_date}.csv",
    mime="text/csv",
)

# ── Call cards (primary content) ─────────────────────────────────────────
section_divider(f"Calls ({total_count})")

# Pagination
PAGE_SIZE = 25
total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

if "page" not in st.session_state:
    st.session_state["page"] = 0

col_prev, col_info, col_next = st.columns([1, 3, 1])
with col_prev:
    if st.button("\u2190 Prev", disabled=st.session_state["page"] <= 0):
        st.session_state["page"] -= 1
        st.rerun()
with col_info:
    st.markdown(
        f'<div style="text-align:center;font-size:0.8rem;color:{COLORS["text_muted"]};'
        f'padding-top:0.4rem;">Page {st.session_state["page"] + 1} of {total_pages}</div>',
        unsafe_allow_html=True,
    )
with col_next:
    if st.button("Next \u2192", disabled=st.session_state["page"] >= total_pages - 1):
        st.session_state["page"] += 1
        st.rerun()

page_start = st.session_state["page"] * PAGE_SIZE
page_end = min(page_start + PAGE_SIZE, total_count)
page_df = calls_df.iloc[page_start:page_end]

for idx, (_, row) in enumerate(page_df.iterrows()):
    row_dict = row.to_dict()
    call_card(row_dict, page_start + idx)

    with st.expander("Details", expanded=False):
        call_detail_panel(row_dict, None, page_start + idx)
        # Transcript loading: fetch only when button is clicked
        call_id = str(row_dict.get("id", ""))
        tx_key = f"show_tx_{page_start + idx}_{call_id}"
        if st.button("Load transcript", key=f"txbtn_{page_start + idx}_{call_id}"):
            st.session_state[tx_key] = True
        if st.session_state.get(tx_key):
            detail, _ = get_call_detail(client, call_id) if call_id else (None, [])
            if detail and detail.get("transcript_text"):
                wc = len(detail["transcript_text"].split())
                st.markdown(
                    f'<div style="font-size:0.73rem;color:#64748b;margin-bottom:0.3rem;'
                    f'font-family:\'JetBrains Mono\',monospace;">'
                    f'{wc:,} words</div>',
                    unsafe_allow_html=True,
                )
                st.code(detail["transcript_text"], language=None, wrap_lines=True)
            else:
                st.warning("No transcript available for this call.")

# ── Charts (below cards) ────────────────────────────────────────────────
st.markdown(
    '<div style="height:2px;margin:2rem 0 1rem 0;'
    'background:linear-gradient(90deg,#22d3ee 0%,#0ea5e9 35%,#a78bfa 65%,#f59e0b 100%);'
    'border-radius:1px;opacity:0.4;"></div>',
    unsafe_allow_html=True,
)

chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    chart_title("Intent Breakdown")
    if analyzed_count > 0:
        intent_data = (
            calls_df.loc[analyzed_mask, "caller_intent"]
            .fillna("other")
            .value_counts()
            .rename_axis("caller_intent")
            .reset_index(name="count")
        )
        intent_data["label"] = intent_data["caller_intent"].apply(_fmt)
        # Color map from INTENT_COLORS
        bar_colors = [
            INTENT_COLORS.get(v, ("#94a3b8", ""))[0]
            for v in intent_data["caller_intent"]
        ]
        fig_intent = px.bar(
            intent_data, y="label", x="count", orientation="h",
            color_discrete_sequence=[CHART_COLORS[0]],
        )
        fig_intent.update_traces(
            marker_color=bar_colors,
            marker_cornerradius=4,
        )
        apply_chart_defaults(fig_intent)
        fig_intent.update_layout(
            yaxis_title=None, xaxis_title=None,
            margin=dict(l=180, t=20, b=40, r=20),
        )
        st.plotly_chart(fig_intent, use_container_width=True)
    else:
        st.info("No analyzed calls in current window.")

with chart_col_2:
    chart_title("Daily Volume & Lead Rate")
    if analyzed_count > 0:
        trend_base = calls_df.loc[analyzed_mask].copy()
        trend_base["call_date"] = pd.to_datetime(
            trend_base["call_date_pt"], errors="coerce"
        )
        daily = trend_base.groupby("call_date").agg(
            total=("caller_intent", "size"),
            leads=("caller_intent", lambda x: (x == "injury_new_case").sum()),
        ).reset_index()
        daily["lead_rate"] = (daily["leads"] / daily["total"] * 100).round(1)

        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily["call_date"], y=daily["total"],
            name="Total Calls",
            marker_color=CHART_COLORS[0],
            marker_cornerradius=4,
            opacity=0.7,
        ))
        fig_daily.add_trace(go.Scatter(
            x=daily["call_date"], y=daily["lead_rate"],
            name="Lead Rate %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color=CHART_COLORS[2], width=2),
            marker=dict(size=6),
        ))
        apply_chart_defaults(fig_daily)
        fig_daily.update_layout(
            yaxis=dict(title="Calls", gridcolor="#1e293b"),
            yaxis2=dict(
                title="Lead Rate %", overlaying="y", side="right",
                gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#64748b", size=11),
                range=[0, 100],
            ),
            xaxis_title="",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=11),
            ),
            margin=dict(l=50, t=30, b=40, r=50),
        )
        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("No analyzed data for trend chart.")
