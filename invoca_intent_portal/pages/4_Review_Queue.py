"""Manual calibration queue for quality-review workflow."""

from __future__ import annotations

import streamlit as st

from invoca_intent_portal.lib.data_access import get_review_queue_df, save_review_result
from invoca_intent_portal.lib.supabase_client import get_supabase_client
from invoca_intent_portal.lib.ui import apply_base_styles

st.set_page_config(page_title="Review Queue", page_icon="✅", layout="wide")
apply_base_styles()
st.title("Review Queue")

client = get_supabase_client()

status_filter = st.selectbox("Queue Status", options=["pending", "in_review", "completed", "skipped", "all"], index=0)

queue_df = get_review_queue_df(client, status=status_filter, limit=300)

if queue_df.empty:
    st.info("No queue rows for this status.")
    st.stop()

st.dataframe(queue_df, use_container_width=True, hide_index=True)

queue_ids = queue_df["id"].dropna().astype(int).tolist() if "id" in queue_df.columns else []
if not queue_ids:
    st.warning("Queue rows loaded but no valid queue IDs were found.")
    st.stop()

st.subheader("Submit Review")

with st.form("review_form"):
    selected_queue_id = st.selectbox("Queue ID", options=queue_ids)
    reviewer = st.text_input("Reviewer", value="")
    reviewer_score = st.slider("Reviewer Score", min_value=1, max_value=5, value=4)
    accepted = st.checkbox("Accepted", value=True)

    disagreement_options = [
        "intent_label",
        "outcome_label",
        "confidence_score",
        "quality_score",
        "brand_confusion",
        "repositioning",
    ]
    disagreements = st.multiselect("Disagreements", options=disagreement_options, default=[])

    notes = st.text_area("Notes", value="", height=120)
    new_status = st.selectbox("New Queue Status", options=["completed", "in_review", "skipped"], index=0)

    submitted = st.form_submit_button("Save Review", type="primary")

if submitted:
    if not reviewer.strip():
        st.error("Reviewer is required.")
    else:
        save_review_result(
            client=client,
            queue_id=int(selected_queue_id),
            reviewer=reviewer.strip(),
            reviewer_score=reviewer_score,
            accepted=accepted,
            notes=notes,
            disagreements=disagreements,
            new_status=new_status,
        )
        st.success("Review result saved.")
        st.rerun()
