# pages/5_Settings.py
import streamlit as st

# =====================================================
# Ensure global currency state exists
# =====================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    st.session_state.exchange_rates = {"BDT": 1.0, "USD": 117.0, "GBP": 146.0}

CURRENCY_SYMBOLS = {"BDT": "৳", "USD": "$", "GBP": "£"}


def currency_symbol():
    return CURRENCY_SYMBOLS.get(st.session_state.currency, "৳")


# =====================================================
# Page Config + styling
# =====================================================
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;600&display=swap');
:root {
    --bg: #0b0c10;
    --panel: #0f1119;
    --border: #1f2533;
    --text: #e8ecf3;
    --muted: #9ea5b4;
    --accent: #3dd598;
    --accent-2: #7dd3fc;
}
html, body, [class*="css"] {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk','Inter',system-ui,-apple-system,sans-serif;
}
.main { background: var(--bg); }
h1, h2, h3, h4 { color: var(--text); letter-spacing: -0.3px; font-weight: 700; }
.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
}
.pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(61,213,152,0.12);
    border: 1px solid rgba(61,213,152,0.25);
    color: var(--accent);
    font-size: 12px;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}
.hero {
    background: radial-gradient(circle at 18% 22%, rgba(61,213,152,0.12), transparent 30%),
                radial-gradient(circle at 85% 10%, rgba(125,211,252,0.16), transparent 26%),
                linear-gradient(120deg, #0b0c10 0%, #0e1119 70%, #0b0c10 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 26px 24px;
    box-shadow: 0 18px 60px rgba(0,0,0,0.45);
    margin-bottom: 16px;
}
.hero h2 { margin: 0; font-size: 28px; letter-spacing: -0.35px; }
.hero p { margin-top: 10px; color: var(--muted); line-height: 1.6; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
    <span class="pill">Settings</span>
    <h2>Settings & Global Assumptions</h2>
    <p>Adjust currency display and exchange rates. More settings will come as the app expands.</p>
</div>
""",
    unsafe_allow_html=True,
)

# =====================================================
# Currency Display Settings
# =====================================================
st.subheader("Currency Settings")

col1, col2 = st.columns([1, 2])

with col1:
    chosen_currency = st.selectbox(
        "Display all financials in:",
        options=["BDT", "USD", "GBP"],
        index=["BDT", "USD", "GBP"].index(st.session_state.currency),
        help="This affects all modules. Internal storage remains in BDT.",
    )

    st.session_state.currency = chosen_currency

with col2:
    sym = currency_symbol()
    st.metric("Current Symbol", sym)
    st.info(
        f"Showing all prices as: {sym} ({st.session_state.currency}). "
        "Internally, everything is still stored in BDT to keep calculations stable."
    )

st.divider()

# =====================================================
# Exchange Rate Settings
# =====================================================
st.subheader("Exchange Rates")
st.caption("Update only if needed. These rates convert BDT ↔ USD/GBP for display.")

rate_bdt = st.number_input("1 BDT = 1 BDT", value=1.0, disabled=True)

rate_usd = st.number_input(
    "1 USD = ... BDT",
    min_value=1.0,
    value=float(st.session_state.exchange_rates["USD"]),
    step=0.5,
    help="Bangladesh Bank approx: 117 BDT per USD (Oct 2025)",
)

rate_gbp = st.number_input(
    "1 GBP = ... BDT",
    min_value=1.0,
    value=float(st.session_state.exchange_rates["GBP"]),
    step=0.5,
    help="Bangladesh Bank approx: 146 BDT per GBP (Oct 2025)",
)

if st.button("Save Exchange Rates"):
    st.session_state.exchange_rates = {"BDT": 1.0, "USD": rate_usd, "GBP": rate_gbp}
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
