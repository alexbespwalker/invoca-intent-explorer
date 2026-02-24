"""Drill-down view for a single call and its analysis."""

from __future__ import annotations

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
from invoca_intent_portal.lib.ui import apply_base_styles

st.set_page_config(page_title="Call Detail", page_icon="\U0001F50E", layout="wide")
apply_base_styles()
check_password()
st.title("Call Detail")

client = require_supabase_client()


def _val(val: object) -> str:
    if val is None:
        return "n/a"
    text = str(val).strip()
    return text if text else "n/a"


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
m1, m2, m3, m4 = st.columns(4)
m1.metric("Internal ID", call.get("id"))
m2.metric("Invoca Call ID", _val(call.get("invoca_call_id")))
m3.metric("Brand", _val(call.get("brand_code")))
m4.metric("Status", _val(call.get("status")))

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Call Date (PT):** {_val(call.get('call_date_pt'))}")
    st.write(f"**Call Start:** {_val(call.get('call_start_time'))}")
    st.write(f"**Duration (sec):** {_val(call.get('duration_seconds'))}")
with col2:
    st.write(f"**Advertiser:** {_val(call.get('advertiser_name'))}")
    st.write(f"**Campaign:** {_val(call.get('campaign_name'))}")
    st.write(f"**Word Count:** {_val(call.get('transcript_word_count'))}")

# ── Transcript ───────────────────────────────────────────────────────────
st.subheader("Transcript")
transcript = call.get("transcript_text")
if transcript:
    st.text_area("Transcript Text", transcript, height=320)
else:
    st.warning("No transcript on this call record yet.")

# ── Analysis ─────────────────────────────────────────────────────────────
st.subheader("Analysis")
if analyses:
    latest = analyses[0]

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Intent", _val(latest.get("caller_intent")))
    a2.metric("Confidence", _val(latest.get("intent_confidence")))
    a3.metric("Outcome", _val(latest.get("call_outcome")))
    a4.metric("Agent Quality", _val(latest.get("agent_quality_score")))

    st.write(f"**Brand Confusion:** {latest.get('brand_confusion')}")
    st.write(f"**Sentiment:** {_val(latest.get('caller_sentiment'))}")
    st.write(f"**Validation Passed:** {_val(latest.get('validation_passed'))}")

    # Confusion signals
    signals = latest.get("confusion_signals")
    if signals and isinstance(signals, list) and len(signals) > 0:
        st.write("**Confusion Signals:**")
        for sig in signals:
            st.write(f"- {sig}")

    # Key quotes
    quotes = latest.get("key_quotes")
    if quotes and isinstance(quotes, list) and len(quotes) > 0:
        st.subheader("Key Quotes")
        for q in quotes:
            if isinstance(q, dict):
                st.markdown(f"> *\"{q.get('quote', '')}\"*")
                ctx = q.get("context")
                if ctx:
                    st.caption(ctx)
            elif isinstance(q, str):
                st.markdown(f"> *\"{q}\"*")

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
