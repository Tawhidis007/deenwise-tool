# Home (app.py)

import streamlit as st

# =========================================================
# Global Defaults
# =========================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    # Bangladesh Bank approx as placeholder
    st.session_state.exchange_rates = {
        "BDT": 1.0,
        "USD": 117.0,
        "GBP": 146.0,
    }

CURRENCY_SYMBOLS = {"BDT": "৳", "USD": "$", "GBP": "£"}


# =========================================================
# Page Settings
# =========================================================
st.set_page_config(
    page_title="DeenWise Dashboard",
    page_icon="🏠",
    layout="wide",
)


# =========================================================
# Hero Section
# =========================================================
st.title("🏠 DeenWise Business Dashboard")
st.caption("A single workspace for planning, forecasting, and business decision-making.")

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
# Quick Navigation (Side navbar alternatives)
# =========================================================
st.subheader("📂 Navigate to a Module")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.page_link(
        "pages/1_Product_Management.py",
        label="Product Management",
        icon="🧵",
        help="Build and maintain the master product database."
    )

with col2:
    st.page_link(
        "pages/2_Forecast_Dashboard.py",
        label="Forecast Dashboard",
        icon="📊",
        disabled=True,
        help="Plan campaign quantities & revenue (enabled after Module 1)."
    )

with col3:
    st.page_link(
        "pages/3_OPEX_and_Profitability.py",
        label="OPEX & Profitability",
        icon="🧾",
        disabled=True,
        help="View your profit after overheads (enabled after Module 2)."
    )

with col4:
    st.page_link(
        "pages/4_Scenario_Planning.py",
        label="Scenario Planning",
        icon="🧪",
        disabled=True,
        help="Test 'What-If' changes without touching real data."
    )

with col5:
    st.page_link(
        "pages/5_Settings.py",
        label="Settings",
        icon="⚙️",
        help="Currency, defaults, and system configuration."
    )

st.markdown("---")


# =========================================================
# What Each Module Does (Updated & Cleaner)
# =========================================================
st.subheader("📘 Overview of All Modules")

st.markdown("""
### 🧵 Module 1 — Product Management  
The foundation of the entire system.  
Here you set up every product with:

- Manufacturing, packaging & shipping costs  
- Marketing cost  
- Expected return rate  
- Discount strategy  
- Final selling price  

These values automatically flow into every other module.

---

### 📊 Module 2 — Forecast Dashboard  
Plan your campaigns with confidence.

You can:

- Select campaign products  
- Set quantities  
- Distribute sales by month  
- Add size breakdowns (optional)  
- View full revenue & cost forecasts  
- Understand profit contribution per product and per month  

This module answers:  
**“If we run this campaign, how much will we make?”**

---

### 🧾 Module 3 — OPEX & Profitability  
Real overhead costs often change the final picture.

Here you can manage:

- Salaries  
- Rent  
- Utilities  
- Studio expenses  
- Marketing overhead  
- One-time or seasonal costs  

Then see:

- Net profit **after** overhead  
- Profit per unit  
- Monthly financial breakdown  
- Burn rate  
- Contribution margin  

This module answers:  
**“After all costs — what is our true profit?”**

---

### 🧪 Module 4 — Scenario Planning  
A safe sandbox for experimentation.

You can adjust:

- Prices  
- Quantity  
- Costs  
- Discounts  
- Return rates  
- USD/GBP exchange rate  
- Overheads  

Then compare scenarios instantly.  
Nothing here modifies your real campaign or product data.

This module answers:  
**“What if we change something — how does profit react?”**

---

### ⚙️ Module 5 — Settings  
Global configuration for the entire app:

- Currency  
- Exchange rates  
- Future VAT / default assumptions  
- Internal knowledge base (coming soon)  

Settings apply instantly across all modules.

---
""")


# =========================================================
# Tips for Using the Tool
# =========================================================
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
Begin with **🧵 Product Management**.
""")
