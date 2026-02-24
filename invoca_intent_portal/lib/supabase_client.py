"""Supabase client bootstrap for the Invoca Intent Explorer portal."""

from __future__ import annotations

import os

import streamlit as st
from supabase import Client, create_client


def _secret_value(key: str) -> str | None:
    """Read a key from Streamlit secrets if available."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def get_supabase_config() -> tuple[str, str]:
    """Resolve Supabase URL + key from env vars or Streamlit secrets."""
    url = os.getenv("SUPABASE_URL") or _secret_value("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or _secret_value("SUPABASE_SERVICE_KEY")
        or _secret_value("SUPABASE_KEY")
    )

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase configuration. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_KEY (or SUPABASE_KEY)."
        )

    return str(url), str(key)


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    """Create and cache a Supabase client."""
    url, key = get_supabase_config()
    return create_client(url, key)
