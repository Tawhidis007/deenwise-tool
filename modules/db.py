# modules/db.py
import streamlit as st
from supabase import create_client, Client
import os

def get_supabase() -> Client:
    """
    Works locally and on Streamlit Cloud.
    Priority:
    1. Streamlit st.secrets["supabase"]
    2. OS environment variables (optional fallback)
    """

    # Already created once → return memoized client
    if "supabase_client" in st.session_state:
        return st.session_state.supabase_client

    # ------------------------------
    # 1. Try Streamlit Secrets
    # ------------------------------
    if "supabase" in st.secrets:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
    else:
        # ------------------------------
        # 2. Fallback: Environment vars (local dev option)
        # ------------------------------
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise RuntimeError(
                "Supabase credentials not found.\n"
                "Set them in `.streamlit/secrets.toml` (local) or Streamlit Cloud Secrets."
            )

    # Create client and store in session state
    st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client
