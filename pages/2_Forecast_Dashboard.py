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
    month_label_to_nice
)

from modules.campaign_db import (
    fetch_campaigns,
    create_campaign,
    get_latest_campaign_or_create_default,
    update_campaign,
    fetch_campaign_products,
    save_campaign_products,
    fetch_month_weights,
    save_month_weights,
    fetch_size_breakdown,
    save_size_breakdown
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
st.set_page_config(page_title="Forecast Dashboard", page_icon="📊", layout="wide")
st.title("📊 Forecast Dashboard (Module 2)")
st.caption("Plan campaign quantities by product, distribute across months, and see full revenue forecast — persistent via Supabase.")

# -----------------------------
# Load products
# -----------------------------
products = load_products()
prod_df_bdt = products_to_dataframe(products)

if prod_df_bdt.empty:
    st.warning("No products found. Please add products in **Product Management** first.")
    st.stop()

sym = currency_symbol()

# ==========================
# Campaign selection + setup
# ==========================
campaigns = fetch_campaigns()
active_campaign = get_latest_campaign_or_create_default()

campaign_name_map = {c["name"]: c["id"] for c in campaigns} if campaigns else {active_campaign["name"]: active_campaign["id"]}
campaign_names = list(campaign_name_map.keys())

with st.sidebar:
    st.header("📌 Active Campaign")

    selected_campaign_name = st.selectbox(
        "Select campaign",
        options=campaign_names,
        index=campaign_names.index(active_campaign["name"]) if active_campaign["name"] in campaign_names else 0
    )
    selected_campaign_id = campaign_name_map[selected_campaign_name]

    st.divider()
    st.subheader("➕ Create New Campaign")

    new_name = st.text_input("Campaign name", placeholder="e.g., Feb-Apr Launch")
    colx, coly = st.columns(2)
    new_start = colx.date_input("Start", value=date(2026, 2, 1), key="new_start")
    new_end = coly.date_input("End", value=date(2026, 4, 1), key="new_end")

    if st.button("Create Campaign"):
        if new_name.strip():
            create_campaign(
                name=new_name.strip(),
                start_date=new_start,
                end_date=new_end,
                distribution_mode="Uniform",
                currency=st.session_state.currency
            )
            st.success("Campaign created ✅")
            st.rerun()
        else:
            st.warning("Please give a name.")

# Load current campaign details
curr_campaign = [c for c in (campaigns or [active_campaign]) if c["id"] == selected_campaign_id][0]

start_date_db = datetime.fromisoformat(curr_campaign["start_date"]).date()
end_date_db = datetime.fromisoformat(curr_campaign["end_date"]).date()
distribution_mode_db = curr_campaign.get("distribution_mode", "Uniform")

# Load persistent inputs
db_quantities, _ = fetch_campaign_products(selected_campaign_id)
db_weights = fetch_month_weights(selected_campaign_id)
db_sizes = fetch_size_breakdown(selected_campaign_id)

# -----------------------------
# Sidebar / Campaign Setup
# -----------------------------
with st.sidebar:
    st.header("🗓 Campaign Setup")

    start_date_ui = st.date_input("Campaign Start Date", value=start_date_db, key=f"start_{selected_campaign_id}")
    end_date_ui = st.date_input("Campaign End Date", value=end_date_db, key=f"end_{selected_campaign_id}")

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
        help="How sales are spread across months."
    )
    if distribution_mode != distribution_mode_db:
        update_campaign(selected_campaign_id, {"distribution_mode": distribution_mode})

    st.divider()
    enable_size_breakdown = st.toggle(
        "Enable size breakdown (S/M/L/XL etc.)",
        value=False,
        key=f"size_toggle_{selected_campaign_id}"
    )

# -----------------------------
# Main Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["🧮 Quantities", "📈 Forecast Output", "🧾 Size Breakdown"])

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
        default=default_selected
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

        with st.expander(f"{pname}  •  {cat}", expanded=True):
            colA, colB, colC = st.columns(3)

            with colA:
                qty_total = st.number_input(
                    f"Total units for {pname}",
                    min_value=0.0,
                    value=prefill_qty,
                    step=10.0,
                    key=f"qty_{selected_campaign_id}_{pid}"
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
                            key=f"size_{selected_campaign_id}_{pid}_{s}"
                        )
                size_breakdown[pid] = sb

    save_campaign_products(selected_campaign_id, quantities)

    custom_month_weights = None
    if distribution_mode == "Custom":
        st.markdown("### Custom Monthly Weights")
        rows = []
        for m in months:
            nice = month_label_to_nice(m)
            prefill_w = float(db_weights.get(m, 1.0))

            w = st.number_input(
                f"Weight for {nice}",
                min_value=0.0,
                value=prefill_w,
                step=0.1,
                key=f"w_{selected_campaign_id}_{m}"
            )
            rows.append({"month": m, "month_nice": nice, "weight": w})

        df_w = pd.DataFrame(rows)
        custom_month_weights = {r["month"]: r["weight"] for r in rows}

        st.dataframe(df_w, use_container_width=True, hide_index=True)
        save_month_weights(selected_campaign_id, custom_month_weights)
    else:
        if db_weights:
            save_month_weights(selected_campaign_id, {})

    if enable_size_breakdown:
        save_size_breakdown(selected_campaign_id, size_breakdown)

    st.success("Saved to Supabase ✅")


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
        size_breakdown=size_breakdown if enable_size_breakdown else None
    )

    totals_bdt = campaign_totals(monthly_df_bdt)
    totals = {k: from_bdt(v) if ("revenue" in k or "profit" in k or "cost" in k) else v
              for k, v in totals_bdt.items()}

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
            net_profit=("net_profit", "sum")
        )
        .sort_values("month")
    )
    st.dataframe(month_table, use_container_width=True, hide_index=True)

    colA, colB = st.columns(2)
    with colA:
        fig1 = px.line(month_table, x="month_nice", y="effective_revenue", markers=True,
                       title=f"Effective Revenue Over Campaign ({sym})")
        st.plotly_chart(fig1, use_container_width=True)

    with colB:
        if not product_summary_df_bdt.empty:
            fig2 = px.bar(ps, x="product_name", y="effective_revenue", color="category",
                          title=f"Effective Revenue by Product ({sym})", text_auto=".0f")
            st.plotly_chart(fig2, use_container_width=True)

    st.session_state["monthly_forecast_df"] = mt
    st.session_state["product_summary_df"] = ps
    st.session_state["size_df"] = size_df_bdt


# =====================================================================
# TAB 3 — Size Breakdown
# =====================================================================
with tab3:
    st.subheader("Size Breakdown Summary")

    if not enable_size_breakdown:
        st.info("Turn ON size breakdown in sidebar to use this.")
        st.stop()

    if size_df_bdt is None or size_df_bdt.empty:
        st.info("Input size quantities in Quantities tab.")
    else:
        size_df = size_df_bdt.copy()
        for col in ["gross_revenue", "effective_revenue", "total_cost", "net_profit"]:
            size_df[col] = size_df[col].apply(from_bdt)

        st.dataframe(size_df, use_container_width=True, hide_index=True)
