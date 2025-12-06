# Home.py
import streamlit as st

# =========================================================
# Global Defaults
# =========================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    st.session_state.exchange_rates = {"BDT": 1.0, "USD": 117.0, "GBP": 146.0}

CURRENCY_SYMBOLS = {"BDT": "BDT", "USD": "$", "GBP": "£"}

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="DeenWise Financial Planning",
    page_icon="📊",
    layout="wide",
)

# =========================================================
# Minimal, professional styling
# =========================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {
    --bg: #0b0c10;
    --panel: #0f1119;
    --border: #1d2230;
    --text: #e9edf5;
    --muted: #9ea5b4;
    --accent: #3dd598;
    --accent-2: #7dd3fc;
}
html, body, [class*="css"] {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif;
}
.main { background: var(--bg); }
.hero {
    background: radial-gradient(circle at 20% 20%, rgba(61,213,152,0.12), transparent 30%),
                radial-gradient(circle at 80% 0%, rgba(125,211,252,0.16), transparent 26%),
                linear-gradient(120deg, #0b0c10 0%, #0e1119 70%, #0b0c10 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 30px 28px;
    box-shadow: 0 18px 60px rgba(0,0,0,0.45);
    margin-bottom: 20px;
}
.hero h1 { margin: 0; font-size: 32px; letter-spacing: -0.4px; }
.hero p { margin-top: 10px; color: var(--muted); font-size: 16px; line-height: 1.6; }
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
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 22px;
    margin-top: 12px;
    margin-bottom: 8px;
}
.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 16px 45px rgba(0,0,0,0.35);
    transition: all 0.2s ease;
}
.card:hover { border-color: var(--accent); transform: translateY(-3px); }
.card h3 { margin: 0 0 6px 0; font-size: 18px; }
.card p { margin: 0; color: var(--muted); line-height: 1.5; }
.metric {
    background: linear-gradient(120deg, rgba(61,213,152,0.12), rgba(125,211,252,0.12));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
}
.metric-label { color: var(--muted); font-size: 12px; letter-spacing: 0.6px; text-transform: uppercase; }
.metric-value { color: var(--text); font-size: 24px; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# HERO SECTION
# =========================================================
st.markdown(
    """
<div class="hero">
    <span class="pill">Financial workspace</span>
    <h1>DeenWise Planning Hub</h1>
    <p>
        Build products, plan campaigns, layer OPEX, and test scenarios — all from one streamlined console.
        Everything is stored in BDT and converted for display.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# Quick metrics / reminders
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="metric"><div class="metric-label">Start with</div><div class="metric-value">Module 1 · Products</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric"><div class="metric-label">Currency</div><div class="metric-value">{}</div></div>'.format(st.session_state.currency), unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric"><div class="metric-label">Data source</div><div class="metric-value">Supabase</div></div>', unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# MAIN MODULE CARDS
# =========================================================
modules = [
    {
        "title": "Product Management",
        "desc": "Define products, costs, discounts, and returns. Feeds every other module.",
        "page": "pages/1_Product_Management.py",
        "icon": "📦",
    },
    {
        "title": "Forecast Dashboard",
        "desc": "Plan quantities, spread them across months, and see revenue and profit instantly.",
        "page": "pages/2_Forecast_Dashboard.py",
        "icon": "📈",
    },
    {
        "title": "OPEX & Profitability",
        "desc": "Attach operating expenses to campaigns and view net profit after overheads.",
        "page": "pages/3_OPEX_and_Profitability.py",
        "icon": "🏢",
    },
    {
        "title": "Scenario Planning",
        "desc": "Run what-if tests with price, cost, or FX overrides without touching live data.",
        "page": "pages/4_Scenario_Planning.py",
        "icon": "🧭",
    },
    {
        "title": "Settings",
        "desc": "Control display currency and exchange rates; more global defaults coming soon.",
        "page": "pages/5_Settings.py",
        "icon": "⚙️",
    },
    {
        "title": "Reports & Exports",
        "desc": "Export products, campaigns, and scenarios to Excel for sharing.",
        "page": "pages/6_Reports_and_Exports.py",
        "icon": "📑",
    },
]

st.subheader("Navigate the suite")
st.markdown('<div class="card-grid">', unsafe_allow_html=True)

for mod in modules:
    st.markdown(
        f"""
        <div class="card">
            <h3>{mod['icon']} {mod['title']}</h3>
            <p>{mod['desc']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

link_cols = st.columns(3)
for idx, mod in enumerate(modules[:6]):
    col = link_cols[idx % 3]
    col.page_link(mod["page"], label=f"Open {mod['title']}", icon="➡️")

st.markdown("---")

st.subheader("Working order")
st.markdown(
    """
1) Set up **Product Management** first — every other module needs it.  
2) Plan volumes in **Forecast Dashboard**, then add **OPEX**.  
3) Stress-test ideas in **Scenario Planning** before launching.
"""
)

st.markdown(
    "Need help? Start with the Product module, or jump to Settings to confirm exchange rates."
)
