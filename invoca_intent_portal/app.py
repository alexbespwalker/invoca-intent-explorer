"""Invoca Intent Explorer — VP-first dashboard flow."""

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
    VALID_INTENTS, TIER_COLORS, WHO_LABELS, tier_section_divider,
)


st.set_page_config(
    page_title="Invoca Intent Explorer",
    page_icon="\U0001F4DE",
    layout="wide",
)
apply_base_styles()
check_password()

# ── [1] Header ──────────────────────────────────────────────────────────
st.markdown(
    '<div style="height:3px;background:linear-gradient(90deg,#22d3ee 0%,#0ea5e9 40%,#a78bfa 70%,#f59e0b 100%);'
    'border-radius:2px;margin-bottom:0.8rem;opacity:0.9;"></div>',
    unsafe_allow_html=True,
)
st.title("Invoca Intent Explorer")
st.caption("BC call review  \u2022  caller intent  \u2022  brand confusion")
st.markdown(
    '<div style="height:0.3rem;"></div>',
    unsafe_allow_html=True,
)

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

    # Call Category quick filter
    call_category = st.radio(
        "Call Category",
        options=["All", "Valid Inquiries", "Wrong / Noise"],
        index=0,
        horizontal=True,
    )

    # Intent filter
    intent_filter = st.multiselect(
        "Intent",
        options=list(INTENT_COLORS.keys()),
        format_func=_fmt,
        default=[],
        help="Filter to specific intents",
    )

    # CSV export in sidebar
    st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)

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

# ── Computed columns ─────────────────────────────────────────────────────
calls_df["tier"] = calls_df["caller_intent"].apply(
    lambda x: "Valid Inquiries" if x in VALID_INTENTS else "Wrong / Noise"
)

calls_df["who_they_called"] = calls_df["raw_analysis"].apply(
    lambda r: r.get("who_they_thought_they_called", "unclear")
    if isinstance(r, dict) else "unclear"
)

# ── Apply filters ────────────────────────────────────────────────────────

# Call category filter
if call_category == "Valid Inquiries":
    calls_df = calls_df[calls_df["tier"] == "Valid Inquiries"]
elif call_category == "Wrong / Noise":
    calls_df = calls_df[calls_df["tier"] == "Wrong / Noise"]

# Sidebar intent filter
if intent_filter:
    calls_df = calls_df[calls_df["caller_intent"].isin(intent_filter)]

if calls_df.empty:
    st.warning("No calls match the current filters.")
    st.stop()

# ── Precompute metrics ───────────────────────────────────────────────────
analyzed_mask = calls_df["caller_intent"].notna()
total_count = len(calls_df)
valid_count = int((calls_df["tier"] == "Valid Inquiries").sum())
wrong_count = total_count - valid_count

confusion_rate = 0.0
confused_count = 0
if total_count > 0:
    confused_count = int(calls_df["brand_confusion"].fillna(False).sum())
    confusion_rate = confused_count / total_count * 100

# ── [2] KPI Strip ───────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Calls", f"{total_count:,}")
m2.metric("Valid Inquiries", f"{valid_count:,} ({valid_count/total_count*100:.0f}%)" if total_count else "0")
m3.metric("Wrong / Noise", f"{wrong_count:,} ({wrong_count/total_count*100:.0f}%)" if total_count else "0")
m4.metric("Brand Confused", f"{confusion_rate:.0f}%")

# Color-code the KPI left borders via JS injection
import streamlit.components.v1 as _components
_components.html("""
<script>
(function colorKPI() {
    const colors = ['#22d3ee','#34d399','#fb7185','#f59e0b'];
    const metrics = window.parent.document.querySelectorAll('[data-testid="stMetric"]');
    metrics.forEach((m, i) => {
        if (i < colors.length) m.style.borderLeftColor = colors[i];
    });
    if (metrics.length < 4) setTimeout(colorKPI, 500);
})();
</script>
""", height=0)

# ── [3] Charts Row 1: Daily Call Mix + Who They Called ──────────────────
chart_r1_left, chart_r1_right = st.columns(2)

with chart_r1_left:
    chart_title("Daily Call Mix")
    if total_count > 0:
        trend_base = calls_df.copy()
        trend_base["call_date"] = pd.to_datetime(trend_base["call_date_pt"], errors="coerce")
        daily = trend_base.groupby("call_date").agg(
            valid=("tier", lambda x: (x == "Valid Inquiries").sum()),
            wrong=("tier", lambda x: (x == "Wrong / Noise").sum()),
        ).reset_index()

        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily["call_date"], y=daily["valid"],
            name="Valid Inquiries",
            marker_color=TIER_COLORS["Valid Inquiries"],
            marker_cornerradius=4,
        ))
        fig_daily.add_trace(go.Bar(
            x=daily["call_date"], y=daily["wrong"],
            name="Wrong / Noise",
            marker_color=TIER_COLORS["Wrong / Noise"],
            marker_cornerradius=4,
        ))
        apply_chart_defaults(fig_daily)
        fig_daily.update_layout(
            barmode="stack",
            yaxis=dict(title="Calls", gridcolor="#1e293b"),
            xaxis_title="",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=11),
            ),
            margin=dict(l=50, t=30, b=40, r=20),
        )
        st.plotly_chart(fig_daily, width="stretch")
    else:
        st.info("No data for daily chart.")

with chart_r1_right:
    chart_title("Who Confused Callers Think They Reached")
    confused_df = calls_df[calls_df["brand_confusion"].fillna(False) == True]
    if len(confused_df) > 0:
        st.markdown(
            f'<div style="font-size:0.82rem;color:{COLORS["amber"]};margin-bottom:0.5rem;">'
            f'{len(confused_df)} of {total_count} callers ({confusion_rate:.0f}%) '
            f'didn\u2019t know they called BetterClaims</div>',
            unsafe_allow_html=True,
        )
        who_data = (
            confused_df["who_they_called"]
            .fillna("unclear")
            .value_counts()
            .rename_axis("who")
            .reset_index(name="count")
        )
        who_data["label"] = who_data["who"].apply(
            lambda w: WHO_LABELS.get(w, _fmt(str(w)))
        )
        # Warm amber/rose palette
        who_palette = ["#f59e0b", "#fb7185", "#fbbf24", "#f472b6", "#a78bfa", "#94a3b8"]
        bar_colors = [who_palette[i % len(who_palette)] for i in range(len(who_data))]

        fig_who = px.bar(
            who_data, y="label", x="count", orientation="h",
        )
        fig_who.update_traces(
            marker_color=bar_colors,
            marker_cornerradius=4,
            text=who_data["count"],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
        )
        apply_chart_defaults(fig_who)
        fig_who.update_layout(
            yaxis_title=None, xaxis_title=None,
            yaxis=dict(automargin=True, tickfont=dict(color="#94a3b8", size=11)),
            margin=dict(l=10, t=10, b=40, r=50),
            showlegend=False,
            height=280,
        )
        st.plotly_chart(fig_who, width="stretch")
    else:
        st.info("No brand confusion detected in current data.")

# ── [4] Charts Row 2: Intent Breakdown + MVA Donut ─────────────────────
chart_r2_left, chart_r2_right = st.columns(2)

with chart_r2_left:
    chart_title("Intent Breakdown")
    if total_count > 0:
        intent_data = (
            calls_df["caller_intent"]
            .fillna("other")
            .value_counts()
            .rename_axis("caller_intent")
            .reset_index(name="count")
        )
        intent_data["label"] = intent_data["caller_intent"].apply(_fmt)
        # Color by tier: emerald shades for valid, rose shades for wrong
        bar_colors = []
        for v in intent_data["caller_intent"]:
            if v in VALID_INTENTS:
                tc, _ = INTENT_COLORS.get(v, ("#34d399", ""))
                bar_colors.append(tc)
            else:
                tc, _ = INTENT_COLORS.get(v, ("#fb7185", ""))
                bar_colors.append(tc)

        fig_intent = px.bar(
            intent_data, y="label", x="count", orientation="h",
        )
        fig_intent.update_traces(
            marker_color=bar_colors,
            marker_cornerradius=4,
            text=intent_data["count"],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
        )
        apply_chart_defaults(fig_intent)
        fig_intent.update_layout(
            yaxis_title=None, xaxis_title=None,
            yaxis=dict(automargin=True, tickfont=dict(color="#94a3b8", size=11)),
            margin=dict(l=10, t=10, b=40, r=50),
            showlegend=False,
            height=320,
        )
        st.plotly_chart(fig_intent, width="stretch", key="intent_chart")
    else:
        st.info("No analyzed calls in current window.")

with chart_r2_right:
    chart_title("Case Type Breakdown (Legal Inquiries)")
    valid_df = calls_df[calls_df["tier"] == "Valid Inquiries"]
    if len(valid_df) > 0 and "case_type" in valid_df.columns:
        case_data = (
            valid_df["case_type"]
            .fillna("not_applicable")
            .value_counts()
            .rename_axis("case_type")
            .reset_index(name="count")
        )
        case_data["label"] = case_data["case_type"].apply(_fmt)

        # MVA vs Non-MVA logic
        mva_count = int(case_data.loc[case_data["case_type"] == "motor_vehicle_accident", "count"].sum())
        non_mva_count = int(case_data.loc[case_data["case_type"] != "motor_vehicle_accident", "count"].sum())

        donut_colors = [
            "#22d3ee", "#34d399", "#f59e0b", "#a78bfa", "#fb7185",
            "#38bdf8", "#fbbf24", "#6ee7b7", "#f472b6", "#818cf8",
        ]
        fig_donut = go.Figure(data=[go.Pie(
            labels=case_data["label"],
            values=case_data["count"],
            hole=0.55,
            marker=dict(colors=donut_colors[:len(case_data)]),
            textinfo="label+value",
            textfont=dict(size=11, color="#e2e8f0"),
            hoverinfo="label+value+percent",
        )])
        apply_chart_defaults(fig_donut)
        fig_donut.update_layout(
            margin=dict(l=20, t=10, b=20, r=20),
            showlegend=False,
            annotations=[dict(
                text=f"<b>{len(valid_df)}</b><br>Legal",
                x=0.5, y=0.5, font_size=16, font_color="#e2e8f0",
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, width="stretch")
    else:
        st.info("No legal inquiry data for case type chart.")

# ── [5] Filter Pills ────────────────────────────────────────────────────
st.markdown(
    '<div style="height:1px;margin:1.2rem 0 0.8rem;background:#334155;"></div>',
    unsafe_allow_html=True,
)

# Show active filter indicator
active_filters = []
if call_category != "All":
    active_filters.append(call_category)
if intent_filter:
    active_filters.append(f"Intent: {', '.join(_fmt(i) for i in intent_filter)}")
if active_filters:
    st.markdown(
        f'<div style="font-size:0.78rem;color:{COLORS["accent"]};margin-bottom:0.3rem;">'
        f'Active filters: {_html.escape(" + ".join(active_filters))}</div>',
        unsafe_allow_html=True,
    )

# ── [6] Call List — Tier-Grouped Cards ──────────────────────────────────
section_divider(f"Calls ({total_count})")

# Sort: Valid before Wrong, then by date descending
calls_df["_tier_sort"] = calls_df["tier"].map({"Valid Inquiries": 0, "Wrong / Noise": 1})
calls_df = calls_df.sort_values(["_tier_sort", "call_date_pt"], ascending=[True, False])

# Pagination — reset to page 0 when filters change
PAGE_SIZE = 25
total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

_filter_key = f"{start_date}|{end_date}|{brand_filter}|{call_category}|{','.join(sorted(intent_filter))}"
if st.session_state.get("_filter_key") != _filter_key:
    st.session_state["_filter_key"] = _filter_key
    st.session_state["page"] = 0
if "page" not in st.session_state:
    st.session_state["page"] = 0
# Clamp page to valid range
if st.session_state["page"] >= total_pages:
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

# Global tier counts for section headers
_global_tier_counts = calls_df["tier"].value_counts().to_dict()

# Group by tier within the page
current_tier = None
for idx, (_, row) in enumerate(page_df.iterrows()):
    row_dict = row.to_dict()
    row_tier = row_dict.get("tier", "Wrong / Noise")

    # Tier section header (shows global count)
    if row_tier != current_tier:
        tier_section_divider(row_tier, _global_tier_counts.get(row_tier, 0), row_tier)
        current_tier = row_tier

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

# ── [8] CSV Export ──────────────────────────────────────────────────────
with st.sidebar:
    export_cols = [
        "invoca_call_id", "call_date_pt", "caller_intent", "caller_situation",
        "tier", "intent_confidence", "brand_confusion", "call_outcome", "case_type",
        "agent_quality_score", "caller_sentiment", "duration_seconds",
    ]
    existing_export_cols = [c for c in export_cols if c in calls_df.columns]
    export_df = calls_df[existing_export_cols].copy()
    for col in ["caller_intent", "call_outcome", "case_type", "caller_sentiment", "tier"]:
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
