"""Supabase client bootstrap for the Invoca Intent Explorer portal."""

from __future__ import annotations

import os

import streamlit as st
from supabase import Client, create_client


def _secret_nested(section: str, key: str) -> str | None:
    """Read a nested key from Streamlit secrets, e.g. st.secrets["database"]["url"]."""
    try:
        return st.secrets[section][key]
    except (KeyError, TypeError, FileNotFoundError):
        return None


def _secret_flat(key: str) -> str | None:
    """Read a flat key from Streamlit secrets, e.g. st.secrets["SUPABASE_URL"]."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def get_supabase_config() -> tuple[str, str]:
    """Resolve Supabase URL + key from env vars or Streamlit secrets.

    Supports two TOML layouts:
      1. Walker Brain style:  [database] url = "..." / key = "..."
      2. Flat style:          SUPABASE_URL = "..." / SUPABASE_KEY = "..."
    """
    url = (
        os.getenv("SUPABASE_URL")
        or _secret_nested("database", "url")
        or _secret_flat("SUPABASE_URL")
    )
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or _secret_nested("database", "key")
        or _secret_flat("SUPABASE_SERVICE_KEY")
        or _secret_flat("SUPABASE_KEY")
    )

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase configuration. Set [database] url/key "
            "or SUPABASE_URL + SUPABASE_KEY in app secrets."
        )

    return str(url), str(key)


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    """Create and cache a Supabase client."""
    url, key = get_supabase_config()
    return create_client(url, key)


def require_supabase_client() -> Client:
    """Get client with friendly error on missing config.

    Validates config BEFORE calling the cached ``get_supabase_client()``
    so a ``StopException`` is never cached inside ``@st.cache_resource``.
    """
    url = (
        os.getenv("SUPABASE_URL")
        or _secret_nested("database", "url")
        or _secret_flat("SUPABASE_URL")
    )
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or _secret_nested("database", "key")
        or _secret_flat("SUPABASE_SERVICE_KEY")
        or _secret_flat("SUPABASE_KEY")
    )
    if not url or not key:
        st.error(
            "Database not configured. Add [database] section with url/key "
            "to app secrets (or set SUPABASE_URL + SUPABASE_KEY)."
        )
        st.stop()
    try:
        return get_supabase_client()
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        st.stop()
