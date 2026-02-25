"""Drill-down view for a single call and its analysis."""

from __future__ import annotations

import html
import json
from pathlib import Path
import sys

import streamlit as st

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from invoca_intent_portal.lib.auth import check_password
from invoca_intent_portal.lib.supabase_client import require_supabase_client
from invoca_intent_portal.lib.db import get_call_detail
from invoca_intent_portal.lib.ui import apply_base_styles, COLORS

st.set_page_config(page_title="Call Detail", page_icon="\U0001F50E", layout="wide")
apply_base_styles()
check_password()
st.markdown(
    '<div style="height:3px;background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
    'border-radius:2px;margin-bottom:1rem;"></div>',
    unsafe_allow_html=True,
)
st.title("Call Detail")

client = require_supabase_client()


def _val(val: object) -> str:
    if val is None:
        return "n/a"
    text = str(val).strip()
    return text if text else "n/a"


def _fmt(val: str) -> str:
    """Format snake_case DB values into readable labels."""
    return val.replace("_", " ").title() if val else val


def _section_divider(label: str) -> None:
    """Render a styled section divider with label."""
    st.markdown(
        f'<div style="margin:1.5rem 0 0.8rem 0;padding-bottom:0.4rem;'
        f'border-bottom:1px solid {COLORS["border"]};'
        f'font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:{COLORS["text_muted"]};">'
        f'{html.escape(label)}</div>',
        unsafe_allow_html=True,
    )


# Support deep links via ?call_id=... query parameter
query_params = st.query_params
initial_value = ""
if "call_id" in query_params and not st.session_state.get("detail_call"):
    initial_value = str(query_params["call_id"])

lookup = st.text_input(
    "Lookup by Internal ID (number) or Invoca Call ID", value=initial_value
)
load_clicked = st.button("Load Call", type="primary")

should_load = load_clicked and lookup.strip()
if not should_load and initial_value and not st.session_state.get("detail_call"):
    should_load = True

if should_load and lookup.strip():
    try:
        call, analyses = get_call_detail(client, lookup.strip())
    except Exception as e:
        st.error(f"Error looking up call: {e}")
        call, analyses = None, []

    st.session_state["detail_call"] = call
    st.session_state["detail_analyses"] = analyses

call = st.session_state.get("detail_call")
analyses = st.session_state.get("detail_analyses", [])

if call is None and should_load:
    st.warning(f"No call found for: {lookup.strip()}")

if not call:
    st.info("Enter a call ID and click Load Call.")
    st.stop()

# ── Call metadata ────────────────────────────────────────────────────────
_section_divider("Call Metadata")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Internal ID", call.get("id"))
m2.metric("Invoca Call ID", _val(call.get("invoca_call_id")))
m3.metric("Brand", _val(call.get("brand_code")))
m4.metric("Status", _fmt(_val(call.get("status"))))

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 1.5rem;'
        f'font-size:0.88rem;color:{COLORS["text_secondary"]};">'
        f'<span style="color:{COLORS["text_muted"]};">Date (PT)</span>'
        f'<span style="color:{COLORS["text_primary"]};">{html.escape(_val(call.get("call_date_pt")))}</span>'
        f'<span style="color:{COLORS["text_muted"]};">Call Start</span>'
        f'<span style="color:{COLORS["text_primary"]};">{html.escape(_val(call.get("call_start_time")))}</span>'
        f'<span style="color:{COLORS["text_muted"]};">Duration</span>'
        f'<span style="color:{COLORS["text_primary"]};">{html.escape(_val(call.get("duration_seconds")))} sec</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 1.5rem;'
        f'font-size:0.88rem;color:{COLORS["text_secondary"]};">'
        f'<span style="color:{COLORS["text_muted"]};">Advertiser</span>'
        f'<span style="color:{COLORS["text_primary"]};">{html.escape(_val(call.get("advertiser_name")))}</span>'
        f'<span style="color:{COLORS["text_muted"]};">Campaign</span>'
        f'<span style="color:{COLORS["text_primary"]};">{html.escape(_val(call.get("campaign_name")))}</span>'
        f'<span style="color:{COLORS["text_muted"]};">Word Count</span>'
        f'<span style="color:{COLORS["text_primary"]};">{html.escape(_val(call.get("transcript_word_count")))}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Transcript ───────────────────────────────────────────────────────────
_section_divider("Transcript")
transcript = call.get("transcript_text")
if transcript:
    st.text_area("Transcript Text", transcript, height=280, label_visibility="collapsed")
else:
    st.warning("No transcript on this call record yet.")

# ── Analysis ─────────────────────────────────────────────────────────────
_section_divider("Analysis")
if analyses:
    latest = analyses[0]

    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Intent", _fmt(_val(latest.get("caller_intent"))))
    a2.metric("Confidence", _val(latest.get("intent_confidence")))
    a3.metric("Outcome", _fmt(_val(latest.get("call_outcome"))))
    a4.metric("Agent Quality", _val(latest.get("agent_quality_score")))
    a5.metric("Case Type", _fmt(_val(latest.get("case_type"))))

    # Inline detail chips
    detail_items = []
    brand_confused = latest.get("brand_confusion")
    if brand_confused:
        detail_items.append(
            f'<span style="background:#7f1d1d;color:#fca5a5;padding:3px 10px;'
            f'border-radius:6px;font-size:0.82em;">Brand Confused</span>'
        )
    else:
        detail_items.append(
            f'<span style="background:{COLORS["bg_elevated"]};color:{COLORS["text_muted"]};'
            f'padding:3px 10px;border-radius:6px;font-size:0.82em;">No Brand Confusion</span>'
        )

    sentiment = _val(latest.get("caller_sentiment"))
    sent_color = {"positive": "#34d399", "negative": "#fb7185", "neutral": "#94a3b8"}.get(
        sentiment.lower(), COLORS["text_secondary"]
    )
    detail_items.append(
        f'<span style="background:{COLORS["bg_elevated"]};color:{sent_color};'
        f'padding:3px 10px;border-radius:6px;font-size:0.82em;">'
        f'Sentiment: {html.escape(_fmt(sentiment))}</span>'
    )

    validation = latest.get("validation_passed")
    if validation:
        detail_items.append(
            f'<span style="background:#064e3b;color:#6ee7b7;padding:3px 10px;'
            f'border-radius:6px;font-size:0.82em;">Validated</span>'
        )

    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:0.5rem 0 1rem 0;">'
        f'{"".join(detail_items)}</div>',
        unsafe_allow_html=True,
    )

    # ── Repositioning ────────────────────────────────────────────────
    repo_attempted = latest.get("agent_repositioning_attempted")
    if repo_attempted is not None:
        _section_divider("Agent Repositioning")
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
        technique = _val(latest.get("repositioning_technique"))
        r3.markdown(
            f'<div style="font-size:0.85rem;color:{COLORS["text_muted"]};">Technique</div>'
            f'<div style="font-size:0.88rem;color:{COLORS["text_primary"]};">'
            f'{html.escape(technique)}</div>',
            unsafe_allow_html=True,
        )

    # ── Flags ────────────────────────────────────────────────────────
    flags = latest.get("flags")
    if flags and isinstance(flags, list) and len(flags) > 0:
        FLAG_STYLES = {
            "compliance_concern": ("background:#7f1d1d;color:#fca5a5;", "Compliance Concern"),
            "training_opportunity": ("background:#78350f;color:#fbbf24;", "Training Opportunity"),
            "exceptional_handling": ("background:#064e3b;color:#6ee7b7;", "Exceptional Handling"),
        }
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

    # Confusion signals
    signals = latest.get("confusion_signals")
    if signals and isinstance(signals, list) and len(signals) > 0:
        _section_divider("Confusion Signals")
        for sig in signals:
            st.markdown(
                f'<div style="padding:0.4rem 0.8rem;margin:0.3rem 0;'
                f'border-left:3px solid {COLORS["rose"]};'
                f'color:{COLORS["text_secondary"]};font-size:0.88rem;">'
                f'{html.escape(str(sig))}</div>',
                unsafe_allow_html=True,
            )

    # Key quotes
    quotes = latest.get("key_quotes")
    if quotes and isinstance(quotes, list) and len(quotes) > 0:
        _section_divider("Key Quotes")
        for q in quotes:
            if isinstance(q, dict):
                quote_text = html.escape(q.get("quote", ""))
                st.markdown(
                    f'<div style="padding:0.6rem 1rem;margin:0.5rem 0;'
                    f'border-left:3px solid {COLORS["accent"]};'
                    f'background:{COLORS["bg_elevated"]};border-radius:0 8px 8px 0;'
                    f'font-style:italic;color:{COLORS["text_primary"]};font-size:0.88rem;">'
                    f'"{quote_text}"</div>',
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
                    f'"{html.escape(q)}"</div>',
                    unsafe_allow_html=True,
                )

    with st.expander("Raw Analysis JSON", expanded=False):
        raw = latest.get("raw_analysis")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                pass
        st.json(raw)

    if len(analyses) > 1:
        with st.expander("Analysis History", expanded=False):
            st.dataframe(analyses, use_container_width=True, hide_index=True)
else:
    st.info("No analysis rows found for this call.")
