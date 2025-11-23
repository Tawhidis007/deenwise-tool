# Home.py — Premium Black & Gold Responsive Version
import streamlit as st

# =========================================================
# Global Defaults (kept exactly same as your original)
# =========================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    st.session_state.exchange_rates = {
        "BDT": 1.0,
        "USD": 117.0,
        "GBP": 146.0,
    }

CURRENCY_SYMBOLS = {"BDT": "৳", "USD": "$", "GBP": "£"}

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="DeenWise Financial Planning Tool",
    page_icon="☪︎",
    layout="wide",
)

# =========================================================
# Custom CSS — Premium Black/Gold UI + Mobile Responsive Cards
# =========================================================
st.markdown("""
<style>
    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #f2f2f2;
        background: #0d0d0d;
    }

    /* Hide top Streamlit default header */
    header {visibility: hidden;}

    /* Hero section spacing */
    .hero {
        padding: 0.5rem 0 1.2rem 0;
    }

    /* Cards container */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 36px;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    /* Card styling */
    .card {
        background: #141414;
        border-radius: 14px;
        padding: 22px;
        border: 1px solid #232323;
        transition: all 0.25s ease;
        height: 100%;
    }

    .card:hover {
        border-color: #f5d67b;
        background: #1b1b1b;
        transform: translateY(-4px);
    }

    .card h3 {
        color: #f5d67b;
        margin-bottom: 10px;
        font-size: 1.3rem;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# HERO SECTION
# =========================================================
st.markdown("""
<div class='hero'>
    <h1 style='color:#f5d67b;'> ☪︎ DeenWise Financial Planning Tool</h1>
    <p style='font-size:1.05rem; color:#d6d6d6;'>
        A single workspace for planning, forecasting, and business decision-making.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
### Welcome to your DeenWise Financial Control Center

This dashboard brings all core financial planning tools into one place —  
from product costing to forecasting, overhead management, and scenario testing.

It is designed for **every team**:

- **Design** — understand cost impact of new products  
- **Marketing** — plan campaign quantities & revenue expectations  
- **Finance** — validate margins, overheads & profitability  
- **Operations** — assess production feasibility & monthly demand  

Everything updates automatically and stays consistent across modules.
""")

st.markdown("---")

# =========================================================
# MAIN — MODULE CARDS (Black & Gold)
# =========================================================

st.subheader("📘 Overview of All Modules")

st.markdown("<div class='card-grid'>", unsafe_allow_html=True)

# ---------------- Card 1 ----------------
st.markdown("""
<div class='card'>
    <h3> Module 1 — Product Management</h3>
    <p>
        The foundation of the entire system.<br><br>
        Define products with:<br>
        • Manufacturing, packaging & shipping costs<br>
        • Marketing cost<br>
        • Expected return rate<br>
        • Discount strategy<br>
        • Final selling price<br><br>
        These values automatically flow into every other module.
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
# ---------------- Card 2 ----------------
st.markdown("""
<div class='card'>
    <h3> Module 2 — Forecast Dashboard</h3>
    <p>
        Plan campaign quantities, revenue, and monthly distribution.<br><br>
        Features:<br>
        • Choose campaign products<br>
        • Set quantities<br>
        • Custom month distribution<br>
        • Optional size breakdowns<br>
        • Revenue & cost forecasts<br>
        • Profit contribution charts<br><br>
        <b>Answers:</b> “If we run this campaign, how much will we make?”
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
# ---------------- Card 3 ----------------
st.markdown("""
<div class='card'>
    <h3> Module 3 — OPEX & Profitability</h3>
    <p>
        Add real overhead costs and see true profit after expenses.<br><br>
        Includes:<br>
        • Salaries<br>
        • Rent & utilities<br>
        • Studio expenses<br>
        • Marketing overhead<br>
        • One-time or seasonal costs<br><br>
        <b>Answers:</b> “After all costs — what is our true profit?”
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
# ---------------- Card 4 ----------------
st.markdown("""
<div class='card'>
    <h3> Module 4 — Scenario Planning</h3>
    <p>
        A safe sandbox to test ideas.<br><br>
        Adjust:<br>
        • Prices, costs, discounts<br>
        • Quantities<br>
        • Return rates<br>
        • FX rates<br>
        • Overheads<br><br>
        Compare scenarios instantly — without touching real data.
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
# ---------------- Card 5 ----------------
st.markdown("""
<div class='card'>
    <h3> Settings</h3>
    <p>
        Global configuration for the entire system.<br><br>
        Control:<br>
        • Currency display<br>
        • Exchange rates<br>
        • VAT & default assumptions<br>
        • Knowledge base (coming soon)<br><br>
        Settings apply instantly across all modules.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# Tips Section
# =========================================================

st.markdown("---")
st.subheader("💡 Helpful Tips")
st.markdown("""
- Always begin with **Module 1** — other modules rely on product data  
- Use realistic return rates and discounts  
- Check Settings if currency or exchange rate looks off  
- Forecast first, then apply OPEX  
- Use Scenario Planning to test ideas before committing  
- Nothing breaks — feel free to experiment  

---
### Ready to get started?  
Begin with **Product Management**.
""")
