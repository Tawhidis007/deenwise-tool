# pages/4_Settings.py
import streamlit as st

# =====================================================
# Ensure global currency state exists
# =====================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    # October 2025 Bangladesh Bank approximate values
    st.session_state.exchange_rates = {
        "BDT": 1.0,
        "USD": 117.0,
        "GBP": 146.0
    }

CURRENCY_SYMBOLS = {"BDT": "৳", "USD": "$", "GBP": "£"}

def currency_symbol():
    return CURRENCY_SYMBOLS.get(st.session_state.currency, "৳")


# =====================================================
# Page Config
# =====================================================
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("Settings & Global Assumptions")
st.caption("Adjust currency display and exchange rates. More settings will come as the app expands.")


# =====================================================
# Currency Display Settings
# =====================================================
st.subheader("🌍 Currency Settings")

col1, col2 = st.columns([1, 2])

with col1:
    chosen_currency = st.selectbox(
        "Display all financials in:",
        options=["BDT", "USD", "GBP"],
        index=["BDT", "USD", "GBP"].index(st.session_state.currency),
        help="This affects all modules. Internal storage remains in BDT."
    )

    st.session_state.currency = chosen_currency

with col2:
    sym = currency_symbol()
    st.metric("Current Symbol", sym)
    st.info(
        f"Showing all prices as: {sym} ({st.session_state.currency})\n\n"
        "Internally, everything is still stored in BDT to keep calculations stable."
    )


st.divider()


# =====================================================
# Exchange Rate Settings (safe minimal version)
# =====================================================
st.subheader("💱 Exchange Rates (October 2025 BB Approx)")

st.caption("Update only if needed. These rates convert **BDT → USD/GBP** for display.")

rate_bdt = st.number_input(
    "1 BDT = 1 BDT",
    value=1.0,
    disabled=True
)

rate_usd = st.number_input(
    "1 USD = ... BDT",
    min_value=1.0,
    value=float(st.session_state.exchange_rates["USD"]),
    step=0.5,
    help="Bangladesh Bank approx: 117 BDT per USD (Oct 2025)"
)

rate_gbp = st.number_input(
    "1 GBP = ... BDT",
    min_value=1.0,
    value=float(st.session_state.exchange_rates["GBP"]),
    step=0.5,
    help="Bangladesh Bank approx: 146 BDT per GBP (Oct 2025)"
)

if st.button("💾 Save Exchange Rates"):
    st.session_state.exchange_rates = {
        "BDT": 1.0,
        "USD": rate_usd,
        "GBP": rate_gbp
    }
    st.success("Exchange rates updated.")

st.divider()

# =====================================================
# Future Settings Placeholder
# =====================================================
st.info(
    """
    This Settings module will grow over time.

    Future items:
    • VAT assumptions  
    • Default return/discount rates  
    • Manufacturing & shipping multipliers  
    • Yearly inflation assumptions  
    • Currency auto-refresh  
    • User permissions & locking  
    """
)
