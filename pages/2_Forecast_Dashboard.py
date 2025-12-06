# pages/2_Forecast_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime

from modules.products import load_products, products_to_dataframe
from modules.revenue import (
    build_campaign_forecast,
    campaign_totals,
    month_range,
    month_label_to_nice,
)
from modules.campaign_db import (
    fetch_campaigns,
    create_campaign,
    get_latest_campaign_or_create_default,
    update_campaign,
    fetch_campaign_products,
    save_campaign_products,
    fetch_product_month_weights,
    save_product_month_weights,
    fetch_size_breakdown,
    save_size_breakdown,
)

# ============================================
# Currency helpers (global display)
# ============================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    st.session_state.exchange_rates = {"BDT": 1.0, "USD": 117.0, "GBP": 146.0}

CURRENCY_SYMBOLS = {"BDT": "৳", "USD": "$", "GBP": "£"}


def currency_symbol():
    return CURRENCY_SYMBOLS.get(st.session_state.currency, "৳")


def from_bdt(amount_bdt: float) -> float:
    rate = st.session_state.exchange_rates.get(st.session_state.currency, 1.0)
    return float(amount_bdt) / rate


# ============================================
# Page Setup
# ============================================
st.set_page_config(page_title="Forecast Dashboard", page_icon="📈", layout="wide")

# =========================================
# Consistent dark styling
# =========================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;600&display=swap');
:root {
    --bg: #0b0c10;
    --panel: #11141b;
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
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    background: var(--panel);
}
thead tr th {
    background: #141923 !important;
    color: var(--text) !important;
    font-weight: 600 !important;
}
tbody tr td { color: var(--muted) !important; }
.js-plotly-plot .plotly-title,
.js-plotly-plot .legend text,
.js-plotly-plot .xtick text,
.js-plotly-plot .ytick text { fill: var(--text) !important; }
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
.tab-container [role="tablist"] button {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px 12px 0 0;
    color: var(--text);
}
.tab-container [role="tablist"] button[aria-selected="true"] {
    border-bottom: 2px solid var(--accent);
    color: var(--accent);
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
    <span class="pill">Forecast</span>
    <h2>Forecast Dashboard</h2>
    <p>Plan campaign quantities by product, distribute across months, and see revenue forecasts saved to Supabase.</p>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Load products
# -----------------------------
products = load_products()
prod_df_bdt = products_to_dataframe(products)

if prod_df_bdt.empty:
    st.warning("No products found. Please add products in **Product Management** first.")
    st.stop()

sym = currency_symbol()
chart_bg = "#0f1119"
palette = ["#4BA3FF", "#2EE6D6", "#1F8BAE", "#7C5CFF", "#FF6B6B", "#FFC857"]

# ==========================
# Campaign selection + setup
# ==========================
campaigns = fetch_campaigns()
active_campaign = get_latest_campaign_or_create_default()

campaign_name_map = (
    {c["name"]: c["id"] for c in campaigns}
    if campaigns
    else {active_campaign["name"]: active_campaign["id"]}
)
campaign_names = list(campaign_name_map.keys())

with st.sidebar:
    st.header("Active Campaign")

    selected_campaign_name = st.selectbox(
        "Select campaign",
        options=campaign_names,
        index=campaign_names.index(active_campaign["name"])
        if active_campaign["name"] in campaign_names
        else 0,
    )
    selected_campaign_id = campaign_name_map[selected_campaign_name]

    st.divider()
    st.subheader("Create New Campaign")

    new_name = st.text_input("Campaign name", placeholder="e.g., Feb-Apr Launch")
    colx, coly = st.columns(2)
    new_start = colx.date_input("Start", value=date(2026, 2, 1), key="new_start")
    new_end = coly.date_input("End", value=date(2026, 4, 1), key="new_end")

    if st.button("Create Campaign", use_container_width=True):
        if new_name.strip():
            create_campaign(
                name=new_name.strip(),
                start_date=new_start,
                end_date=new_end,
                distribution_mode="Uniform",
                currency=st.session_state.currency,
            )
            st.success("Campaign created.")
            st.rerun()
        else:
            st.warning("Please provide a name.")

# Load current campaign details
curr_campaign = [c for c in (campaigns or [active_campaign]) if c["id"] == selected_campaign_id][0]

start_date_db = datetime.fromisoformat(curr_campaign["start_date"]).date()
end_date_db = datetime.fromisoformat(curr_campaign["end_date"]).date()
distribution_mode_db = curr_campaign.get("distribution_mode", "Uniform")

# Load persistent inputs
db_quantities, _ = fetch_campaign_products(selected_campaign_id)
db_sizes = fetch_size_breakdown(selected_campaign_id)
db_product_weights = fetch_product_month_weights(selected_campaign_id)

# -----------------------------
# Sidebar / Campaign Setup
# -----------------------------
with st.sidebar:
    st.header("Campaign Setup")

    start_date_ui = st.date_input(
        "Campaign Start Date", value=start_date_db, key=f"start_{selected_campaign_id}"
    )
    end_date_ui = st.date_input(
        "Campaign End Date", value=end_date_db, key=f"end_{selected_campaign_id}"
    )

    if (start_date_ui != start_date_db) or (end_date_ui != end_date_db):
        update_campaign(selected_campaign_id, {"start_date": start_date_ui, "end_date": end_date_ui})
        st.rerun()

    months = month_range(start_date_ui, end_date_ui)
    st.caption(", ".join([month_label_to_nice(m) for m in months]) or "—")

    distribution_mode = st.selectbox(
        "Sales Distribution Mode",
        ["Uniform", "Front-loaded", "Back-loaded", "Custom"],
        index=["Uniform", "Front-loaded", "Back-loaded", "Custom"].index(distribution_mode_db),
        key=f"mode_{selected_campaign_id}",
        help="How sales are spread across months.",
    )
    if distribution_mode != distribution_mode_db:
        update_campaign(selected_campaign_id, {"distribution_mode": distribution_mode})

    st.divider()
    # Default to ON when saved size data already exists for this campaign
    enable_size_breakdown = st.toggle(
        "Enable size breakdown (S/M/L/XL etc.)",
        value=bool(db_sizes),
        key=f"size_toggle_{selected_campaign_id}",
    )

# -----------------------------
# Main Tabs
# -----------------------------
product_month_weights = {}
custom_month_weights = None  # kept for compatibility, unused for per-product path

tab1, tab2, tab3 = st.tabs(["Quantities", "Forecast Output", "Size Breakdown"])

# =====================================================================
# TAB 1 — Quantities (persistent)
# =====================================================================
with tab1:
    st.subheader("Select Products & Campaign Quantities")

    default_selected = prod_df_bdt["name"].tolist()
    if db_quantities:
        default_selected = prod_df_bdt[prod_df_bdt["id"].isin(db_quantities.keys())]["name"].tolist()

    sel_products = st.multiselect(
        "Products in this campaign",
        options=prod_df_bdt["name"].tolist(),
        default=default_selected,
    )

    if not sel_products:
        st.info("Select at least one product.")
        st.stop()

    sel_prod_df = prod_df_bdt[prod_df_bdt["name"].isin(sel_products)]
    quantities = {}
    size_breakdown = {}

    for _, row in sel_prod_df.iterrows():
        pid = row["id"]
        pname = row["name"]
        cat = row["category"]
        prefill_qty = float(db_quantities.get(pid, 100.0))

        with st.expander(f"{pname} · {cat}", expanded=True):
            colA, colB, colC = st.columns(3)

            with colA:
                qty_total = st.number_input(
                    f"Total units for {pname}",
                    min_value=0.0,
                    value=prefill_qty,
                    step=10.0,
                    key=f"qty_{selected_campaign_id}_{pid}",
                )
                quantities[pid] = float(qty_total)

            with colB:
                st.metric(f"Price ({sym})", f"{from_bdt(row['price_bdt']):.2f}")
                st.metric(f"Effective Price ({sym})", f"{from_bdt(row['effective_price']):.2f}")

            with colC:
                st.metric(f"Unit Net Profit ({sym})", f"{from_bdt(row['unit_net_profit']):.2f}")
                st.metric("Net Margin %", f"{row['net_margin_%']:.1f}%")

            if enable_size_breakdown:
                sizes = ["XS", "S", "M", "L", "XL", "XXL"]
                cols = st.columns(len(sizes))
                sb = {}
                prefill_sizes = db_sizes.get(pid, {})

                for i, s in enumerate(sizes):
                    with cols[i]:
                        sb[s] = st.number_input(
                            f"{s}",
                            min_value=0.0,
                            value=float(prefill_sizes.get(s, 0.0)),
                            step=1.0,
                            key=f"size_{selected_campaign_id}_{pid}_{s}",
                        )
                size_breakdown[pid] = sb

            # --------------------------------------------
            # Per-product custom monthly percentages
            # --------------------------------------------
            if distribution_mode == "Custom":
                st.markdown("#### Custom Monthly % for this Product")

                existing = db_product_weights.get(pid, {})  # {month_label: weight}
                this_weights = {}
                used_pct = 0.0

                for i, m in enumerate(months):
                    nice = month_label_to_nice(m)

                    # Last month auto-fills remaining %
                    if i == len(months) - 1:
                        remaining = max(0.0, 100.0 - used_pct)
                        this_weights[m] = remaining
                        units = qty_total * remaining / 100.0
                        st.markdown(f"**{nice}: {remaining:.1f}% → ≈ {units:.1f} units (auto)**")
                    else:
                        prefill = float(existing.get(m, 0.0))
                        pct = st.number_input(
                            f"{nice} (%) for {pname}",
                            min_value=0.0,
                            max_value=100.0,
                            value=prefill,
                            step=1.0,
                            key=f"pct_{selected_campaign_id}_{pid}_{m}",
                        )
                        pct = float(pct)
                        this_weights[m] = pct
                        used_pct += pct

                        units = qty_total * pct / 100.0
                        st.caption(f"≈ {units:.1f} units")

                product_month_weights[pid] = this_weights

                total_pct = sum(this_weights.values())
                if abs(total_pct - 100.0) > 0.01:
                    st.warning(
                        f"Total percentage for {pname} = {total_pct:.1f}%. "
                        "The last month auto-adjusts, but try to keep the sum near 100%."
                    )

    save_campaign_products(selected_campaign_id, quantities)

    # We keep custom_month_weights for backwards compatibility,
    # but per-product weights are the primary thing for Custom mode.
    custom_month_weights = None

    if distribution_mode == "Custom" and product_month_weights:
        # Save per-product month percentages (as weights)
        save_product_month_weights(selected_campaign_id, product_month_weights)
    else:
        # For non-Custom modes, you can optionally clear legacy campaign-level weights
        # or leave them alone. We'll leave them as-is here.
        pass

    if enable_size_breakdown:
        save_size_breakdown(selected_campaign_id, size_breakdown)

    st.success("Saved to Supabase.")

# =====================================================================
# TAB 2 — Forecast Output
# =====================================================================
with tab2:
    st.subheader("Forecast Output")

    monthly_df_bdt, product_summary_df_bdt, size_df_bdt = build_campaign_forecast(
        products=products,
        quantities=quantities,
        start_date=start_date_ui,
        end_date=end_date_ui,
        distribution_mode=distribution_mode,
        custom_month_weights=custom_month_weights,
        per_product_month_weights=product_month_weights if distribution_mode == "Custom" else None,
        size_breakdown=size_breakdown if enable_size_breakdown else None,
    )

    totals_bdt = campaign_totals(monthly_df_bdt)
    totals = {
        k: from_bdt(v) if ("revenue" in k or "profit" in k or "cost" in k) else v
        for k, v in totals_bdt.items()
    }

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Campaign Units", f"{totals['campaign_qty']:.0f}")
    c2.metric("Gross Revenue", f"{sym}{totals['gross_revenue']:,.0f}")
    c3.metric("Effective Revenue", f"{sym}{totals['effective_revenue']:,.0f}")
    c4.metric("Total Variable Cost", f"{sym}{totals['total_cost']:,.0f}")
    c5.metric("Net Profit", f"{sym}{totals['net_profit']:,.0f}")

    st.divider()

    if not product_summary_df_bdt.empty:
        ps = product_summary_df_bdt.copy()
        for col in ["gross_revenue", "effective_revenue", "total_cost", "net_profit"]:
            ps[col] = ps[col].apply(from_bdt)
        st.dataframe(ps, use_container_width=True, hide_index=True)

    mt = monthly_df_bdt.copy()
    for col in ["gross_revenue", "effective_revenue", "total_cost", "net_profit"]:
        mt[col] = mt[col].apply(from_bdt)

    month_table = (
        mt.groupby(["month", "month_nice"], as_index=False)
        .agg(
            qty=("qty", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            effective_revenue=("effective_revenue", "sum"),
            total_cost=("total_cost", "sum"),
            net_profit=("net_profit", "sum"),
        )
        .sort_values("month")
    )
    st.dataframe(month_table, use_container_width=True, hide_index=True)

    colA, colB = st.columns(2)
    # ========================================
    # Line chart
    # ========================================
    with colA:
        fig1 = px.line(
            month_table,
            x="month_nice",
            y="effective_revenue",
            markers=True,
            title=f"Effective Revenue Over Campaign ({sym})",
            color_discrete_sequence=palette,
        )

        fig1.update_layout(
            height=420,
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font_color="#e6edf3",
            xaxis_title="",
            yaxis_title=f"{sym}",
            legend=dict(font=dict(color="#e6edf3")),
        )

        st.plotly_chart(fig1, use_container_width=True)

    # ========================================
    # Bar chart
    # ========================================
    with colB:
        if not product_summary_df_bdt.empty:
            fig2 = px.bar(
                ps,
                x="product_name",
                y="effective_revenue",
                color="category",
                title=f"Effective Revenue by Product ({sym})",
                text_auto=".0f",
                color_discrete_sequence=palette,
            )

            fig2.update_layout(
                height=420,
                plot_bgcolor=chart_bg,
                paper_bgcolor=chart_bg,
                font_color="#e6edf3",
                xaxis_title="",
                yaxis_title=f"{sym}",
                legend=dict(font=dict(color="#e6edf3")),
            )

            st.plotly_chart(fig2, use_container_width=True)

    st.session_state["monthly_forecast_df"] = mt
    st.session_state["product_summary_df"] = ps if not product_summary_df_bdt.empty else pd.DataFrame()
    st.session_state["size_df"] = size_df_bdt

# =====================================================================
# TAB 3 — Size Breakdown
# =====================================================================
with tab3:
    st.subheader("Size Breakdown Summary")

    if not enable_size_breakdown:
        st.info("Turn ON size breakdown in the sidebar to use this.")
        st.stop()

    if size_df_bdt is None or size_df_bdt.empty:
        st.info("Input size quantities in Quantities tab.")
    else:
        size_df = size_df_bdt.copy()
        for col in ["gross_revenue", "effective_revenue", "total_cost", "net_profit"]:
            size_df[col] = size_df[col].apply(from_bdt)

        st.dataframe(size_df, use_container_width=True, hide_index=True)
