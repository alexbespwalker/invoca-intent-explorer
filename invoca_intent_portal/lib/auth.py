"""Supabase email/password authentication for Invoca Intent Explorer."""

from __future__ import annotations

import streamlit as st

from invoca_intent_portal.lib.supabase_client import get_supabase_config
from invoca_intent_portal.lib.db import (
    authenticate_user, create_session, validate_session, delete_session,
)


def _get_client():
    """Import here to avoid circular import at module load."""
    from invoca_intent_portal.lib.supabase_client import get_supabase_client
    return get_supabase_client()


def check_password() -> bool:
    """Authenticate via Supabase email/password with session persistence.

    Flow:
    1. session_state["authenticated"] — same-tab fast path
    2. query_params["_session"] — cross-refresh persistence via DB
    3. Legacy st.secrets["auth"]["password"] — transition fallback
    4. Login form — email + password
    5. No [database] config — open access (local dev)
    """
    # 1. Already authenticated this tab
    if st.session_state.get("authenticated"):
        return True

    # Check if DB is configured at all
    try:
        get_supabase_config()
    except RuntimeError:
        # No DB config — open access for local dev
        return True

    client = _get_client()

    # 2. Session token in URL — validate against DB
    session_token = st.query_params.get("_session")
    if session_token:
        user = validate_session(client, session_token)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = user["user_email"]
            st.session_state["user_display_name"] = user.get("user_display_name") or user["user_email"]
            st.session_state["session_token"] = session_token
            return True
        else:
            # Expired/invalid token — clear it
            del st.query_params["_session"]

    # 3. Legacy password fallback (transition period)
    try:
        legacy_pw = st.secrets["auth"]["password"]
    except (KeyError, FileNotFoundError):
        legacy_pw = None

    # 4. Show login form
    st.markdown(
        '<div style="height:3px;background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 50%,#f59e0b 100%);'
        'border-radius:2px;margin-bottom:1rem;"></div>',
        unsafe_allow_html=True,
    )
    st.title("Invoca Intent Explorer")
    st.caption("Sign in with your Walker Advertising email.")

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        email = st.text_input(
            "Email", key="login_email",
            placeholder="you@walkeradvertising.com",
        )
        password = st.text_input(
            "Password", type="password", key="login_password",
            placeholder="Password",
        )
        if st.button("Sign in", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Enter both email and password.")
            else:
                # Try Supabase auth first
                user = authenticate_user(client, email.strip(), password)
                if user:
                    token = create_session(client, user["user_id"])
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = user["user_email"]
                    st.session_state["user_display_name"] = user.get("user_display_name") or user["user_email"]
                    st.session_state["session_token"] = token
                    st.query_params["_session"] = token
                    st.rerun()
                elif legacy_pw and password == legacy_pw:
                    # Legacy password match — no DB session, just in-memory
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email.strip()
                    st.session_state["user_display_name"] = email.strip()
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    st.stop()
    return False


def logout() -> None:
    """Delete DB session and clear all auth state."""
    token = st.session_state.get("session_token")
    if token:
        try:
            client = _get_client()
            delete_session(client, token)
        except Exception:
            pass  # best-effort cleanup

    for key in ("authenticated", "user_email", "user_display_name", "session_token"):
        st.session_state.pop(key, None)
    if "_session" in st.query_params:
        del st.query_params["_session"]
    st.rerun()
