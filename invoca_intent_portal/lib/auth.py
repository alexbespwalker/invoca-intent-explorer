"""Simple password authentication for Invoca Intent Explorer."""

from __future__ import annotations

import streamlit as st


def check_password() -> bool:
    """Show password gate and return True if authenticated.

    If no [auth] password is configured in secrets, access is open
    (allows local dev without secrets).
    """
    if st.session_state.get("authenticated"):
        return True

    try:
        configured = st.secrets["auth"]["password"]
    except (KeyError, FileNotFoundError):
        # No auth configured — allow open access (e.g. local dev).
        return True

    if not configured:
        return True

    st.title("Invoca Intent Explorer")
    st.caption("Enter the portal password to continue.")

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        password = st.text_input(
            "Password", type="password", key="password_input",
            label_visibility="collapsed", placeholder="Password",
        )
        if st.button("Log in", type="primary", use_container_width=True):
            if password == configured:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()
    return False
