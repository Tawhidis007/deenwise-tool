# modules/db.py
import streamlit as st
from supabase import create_client, Client

# ----------------------------------------
# Load credentials from Streamlit Secrets
# ----------------------------------------
def get_supabase() -> Client:
    """
    Returns a memoized Supabase client.
    Requires that st.secrets['supabase'] contains:
    - url
    - anon_key
    """
    if "supabase_client" not in st.session_state:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        st.session_state.supabase_client = create_client(url, key)

    return st.session_state.supabase_client
