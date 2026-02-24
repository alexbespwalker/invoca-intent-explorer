"""Drill-down view for a single call and its analyses."""

from __future__ import annotations

import json

import streamlit as st

from invoca_intent_portal.lib.data_access import (
    get_call_detail_by_invoca_id,
    get_call_detail_by_numeric_id,
)
from invoca_intent_portal.lib.supabase_client import get_supabase_client
from invoca_intent_portal.lib.ui import apply_base_styles

st.set_page_config(page_title="Call Detail", page_icon="🔎", layout="wide")
apply_base_styles()
st.title("Call Detail")

client = get_supabase_client()


def _value_or_na(val: object) -> str:
    if val is None:
        return "n/a"
    text = str(val).strip()
    return text if text else "n/a"

lookup = st.text_input("Lookup by Internal Call ID (number) or Invoca Call ID", value="")
load_clicked = st.button("Load Call", type="primary")

if load_clicked and lookup.strip():
    key = lookup.strip()
    if key.isdigit():
        call, analyses = get_call_detail_by_numeric_id(client, int(key))
    else:
        call, analyses = get_call_detail_by_invoca_id(client, key)

    st.session_state["detail_call"] = call
    st.session_state["detail_analyses"] = analyses

call = st.session_state.get("detail_call")
analyses = st.session_state.get("detail_analyses", [])

if not call:
    st.info("Enter a call ID and click Load Call.")
    st.stop()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Internal Call ID", call.get("id"))
m2.metric("Invoca Call ID", call.get("invoca_call_id") or "n/a")
m3.metric("Brand", call.get("brand_code") or "n/a")
m4.metric("Status", call.get("status") or "n/a")

meta_col_1, meta_col_2 = st.columns(2)
with meta_col_1:
    st.write(f"**Call Date (PT):** {_value_or_na(call.get('call_date_pt'))}")
    st.write(f"**Call Start:** {_value_or_na(call.get('call_start_time'))}")
    st.write(f"**Duration (sec):** {_value_or_na(call.get('duration_seconds'))}")
    st.write(f"**Caller Phone:** {_value_or_na(call.get('caller_phone'))}")

with meta_col_2:
    st.write(f"**Destination Number:** {_value_or_na(call.get('destination_number'))}")
    st.write(f"**Transcript Word Count:** {_value_or_na(call.get('transcript_word_count'))}")
    st.write(f"**Brand Code:** {_value_or_na(call.get('brand_code'))}")

st.subheader("Attribution + Media")
st.markdown("<div class='portal-section-caption'>Traffic source and campaign metadata captured at intake.</div>", unsafe_allow_html=True)
attr_col_1, attr_col_2, attr_col_3 = st.columns(3)
with attr_col_1:
    st.write(f"**Advertiser:** {_value_or_na(call.get('advertiser_name'))}")
    st.write(f"**Campaign:** {_value_or_na(call.get('campaign_name'))}")
    st.write(f"**Media Source:** {_value_or_na(call.get('media_source'))}")
    st.write(f"**Media Medium:** {_value_or_na(call.get('media_medium'))}")

with attr_col_2:
    st.write(f"**Publisher:** {_value_or_na(call.get('publisher'))}")
    st.write(f"**Channel:** {_value_or_na(call.get('channel'))}")
    st.write(f"**Landing Page:** {_value_or_na(call.get('landing_page'))}")
    st.write(f"**Ad Group:** {_value_or_na(call.get('ad_group'))}")

with attr_col_3:
    st.write(f"**Creative ID:** {_value_or_na(call.get('creative_id'))}")
    st.write(f"**Placement:** {_value_or_na(call.get('placement'))}")
    st.write(f"**Device Type:** {_value_or_na(call.get('device_type'))}")
    st.write(f"**Geo:** {_value_or_na(call.get('geo_city'))}, {_value_or_na(call.get('geo_region'))}")

st.subheader("UTM + Click IDs")
st.markdown("<div class='portal-section-caption'>Useful for ad-path forensics on BC/brand calls.</div>", unsafe_allow_html=True)
utm_col_1, utm_col_2 = st.columns(2)
with utm_col_1:
    st.write(f"**UTM Source:** {_value_or_na(call.get('utm_source'))}")
    st.write(f"**UTM Medium:** {_value_or_na(call.get('utm_medium'))}")
    st.write(f"**UTM Campaign:** {_value_or_na(call.get('utm_campaign'))}")
    st.write(f"**UTM Term:** {_value_or_na(call.get('utm_term'))}")
    st.write(f"**UTM Content:** {_value_or_na(call.get('utm_content'))}")

with utm_col_2:
    st.write(f"**gclid:** {_value_or_na(call.get('gclid'))}")
    st.write(f"**fbclid:** {_value_or_na(call.get('fbclid'))}")
    st.write(f"**msclkid:** {_value_or_na(call.get('msclkid'))}")

st.subheader("Transcript")
transcript = call.get("transcript_text")
if transcript:
    st.text_area("Transcript Text", transcript, height=320)
else:
    st.warning("No transcript on this call record yet.")

st.subheader("Latest Analysis")
if analyses:
    latest = analyses[0]
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Intent", latest.get("caller_intent") or "n/a")
    a2.metric("Intent Confidence", latest.get("intent_confidence") or "n/a")
    a3.metric("Outcome", latest.get("call_outcome") or "n/a")
    a4.metric("Agent Quality", latest.get("agent_quality_score") or "n/a")

    st.write(f"**Brand Confusion:** {latest.get('brand_confusion')}")
    st.write(f"**Sentiment:** {latest.get('caller_sentiment')}")
    st.write(f"**Reposition Attempted:** {_value_or_na(latest.get('agent_repositioning_attempted'))}")
    st.write(f"**Reposition Successful:** {_value_or_na(latest.get('agent_repositioning_successful'))}")
    st.write(f"**Reposition Technique:** {_value_or_na(latest.get('repositioning_technique'))}")
    st.write(f"**Validation Passed:** {_value_or_na(latest.get('validation_passed'))}")

    with st.expander("Raw Analysis JSON", expanded=False):
        raw = latest.get("raw_analysis")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                pass
        st.json(raw)

    with st.expander("Attribution Metadata JSON", expanded=False):
        attribution = call.get("attribution_metadata")
        if isinstance(attribution, str):
            try:
                attribution = json.loads(attribution)
            except Exception:
                pass
        st.json(attribution if attribution else {})

    with st.expander("Analysis History", expanded=False):
        st.dataframe(analyses, use_container_width=True, hide_index=True)
else:
    st.info("No analysis rows found for this call.")
