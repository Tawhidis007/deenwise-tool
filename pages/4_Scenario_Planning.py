# pages/4_Scenario_Planning.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from modules.products import load_products, products_to_dataframe
from modules.campaign_db import fetch_campaigns
from modules.scenarios_db import (
    fetch_scenarios, create_scenario, update_scenario, delete_scenario, duplicate_scenario,
    fetch_scenario_products, save_scenario_products,
    fetch_scenario_opex, save_scenario_opex,
    fetch_scenario_fx, save_scenario_fx,
    link_scenario_to_campaign, fetch_scenario_campaign_links
)
from modules.scenario_engine import build_scenario_forecast

# ============================================
# Currency helpers (same pattern as modules 1–3)
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
    return float(amount_bdt) / rate if amount_bdt is not None else 0.0

def to_bdt(amount_display: float) -> float:
    rate = st.session_state.exchange_rates.get(st.session_state.currency, 1.0)
    return float(amount_display) * rate

sym = currency_symbol()

# ============================================
# Page setup
# ============================================
st.set_page_config(page_title="Scenario Planning", page_icon="🧪", layout="wide")
st.title("Scenario Planning (Module 4)")
st.caption("Create 'What-If' scenarios without touching real product or campaign data. Compare outcomes side-by-side.")

# ============================================
# Load base data
# ============================================
products = load_products()
prod_df_bdt = products_to_dataframe(products)

campaigns = fetch_campaigns()
if not campaigns:
    st.warning("No campaigns found. Please create a campaign in Module 2 first.")
    st.stop()

campaign_name_map = {c["name"]: c["id"] for c in campaigns}
campaign_id_map = {c["id"]: c for c in campaigns}

scenarios = fetch_scenarios()

# ============================================
# Sidebar — Scenario Controls
# ============================================
with st.sidebar:
    st.header("🧪 Scenarios")

    if not scenarios:
        st.info("No scenarios yet. Create your first one below.")
        selected_scenario = None
    else:
        scenario_name_map = {s["name"]: s["id"] for s in scenarios}
        names = list(scenario_name_map.keys())
        selected_name = st.selectbox("Select scenario", names, index=0)
        selected_id = scenario_name_map[selected_name]
        selected_scenario = [s for s in scenarios if s["id"] == selected_id][0]

    st.divider()
    st.subheader("➕ Create Scenario")

    new_s_name = st.text_input("Name", placeholder="e.g., Best Case / USD Shock / Discount Heavy")
    new_s_desc = st.text_area("Description", placeholder="Explain what this scenario changes.")
    base_campaign_name = st.selectbox("Base Campaign", list(campaign_name_map.keys()))

    if st.button("Create Scenario", use_container_width=True):
        if not new_s_name.strip():
            st.warning("Give scenario a name.")
        else:
            s = create_scenario(
                name=new_s_name.strip(),
                description=new_s_desc.strip(),
                base_campaign_id=campaign_name_map[base_campaign_name]
            )
            link_scenario_to_campaign(s["id"], campaign_name_map[base_campaign_name])
            st.success("Scenario created ✅")
            st.rerun()

    if selected_scenario:
        st.divider()
        st.subheader("🧬 Manage Scenario")

        if st.button("Duplicate Scenario", use_container_width=True):
            dup = duplicate_scenario(selected_scenario["id"], f"{selected_scenario['name']} (Copy)")
            st.success("Duplicated ✅")
            st.rerun()

        if st.button("Delete Scenario", type="primary", use_container_width=True):
            delete_scenario(selected_scenario["id"])
            st.warning("Scenario deleted.")
            st.rerun()


if not selected_scenario:
    st.stop()

scenario_id = selected_scenario["id"]

# --------------------------------------------
# Resolve base campaign for this scenario
# --------------------------------------------
links = fetch_scenario_campaign_links(scenario_id)
if links:
    base_campaign_id = links[0]["campaign_id"]
else:
    base_campaign_id = selected_scenario.get("base_campaign_id")

if base_campaign_id not in campaign_id_map:
    base_campaign_id = campaigns[0]["id"]

base_campaign = campaign_id_map[base_campaign_id]

# Load overrides
db_prod_overrides = fetch_scenario_products(scenario_id)
db_opex_overrides = fetch_scenario_opex(scenario_id)
db_fx_overrides = fetch_scenario_fx(scenario_id)

prod_ov_map = {o["product_id"]: o for o in db_prod_overrides}
opex_ov_map = {o["opex_item_id"]: o for o in db_opex_overrides}
fx_ov_map = {o["currency"]: o for o in db_fx_overrides}


# ============================================
# Tabs
# ============================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🧵 Product Overrides",
    "🧾 OPEX Overrides",
    "💱 FX Overrides",
    "📊 Scenario Results"
])

# ======================================================
# TAB 1 — Product Overrides
# ======================================================
with tab1:
    st.subheader("Product Overrides (Only for this Scenario)")
    st.caption("Leave fields empty to use real product values from Module 1 & campaign quantities from Module 2.")

    # show base campaign
    colA, colB = st.columns([2, 1])
    colA.info(f"Base Campaign: **{base_campaign['name']}**  ({base_campaign['start_date']} → {base_campaign['end_date']})")
    new_base = colB.selectbox("Change Base Campaign", list(campaign_name_map.keys()),
                             index=list(campaign_name_map.values()).index(base_campaign_id))
    if campaign_name_map[new_base] != base_campaign_id:
        link_scenario_to_campaign(scenario_id, campaign_name_map[new_base])
        st.success("Base campaign updated. Reloading...")
        st.rerun()

    st.divider()

    override_rows = []
    for _, row in prod_df_bdt.iterrows():
        pid = row["id"]
        pname = row["name"]
        cat = row["category"]

        ov = prod_ov_map.get(pid, {})

        with st.expander(f"{pname}  •  {cat}", expanded=False):
            c1, c2, c3, c4, c5 = st.columns(5)

            base_price = float(row["price_bdt"])
            base_disc = float(row["discount_rate_%"])
            base_ret = float(row["return_rate_%"])
            base_cost = float(row["total_unit_cost"])
            base_qty = None  # from campaign

            # Price override
            with c1:
                p_override_disp = st.number_input(
                    f"Price override ({sym})",
                    min_value=0.0,
                    value=from_bdt(ov.get("price_override")) if ov.get("price_override") else 0.0,
                    step=10.0,
                    key=f"price_{scenario_id}_{pid}"
                )
                use_price_override = st.checkbox("Use price override?", value=bool(ov.get("price_override")),
                                                key=f"use_price_{scenario_id}_{pid}")

            # Discount override
            with c2:
                disc_override = st.number_input(
                    "Discount override (%)",
                    min_value=0.0,
                    max_value=90.0,
                    value=float(ov.get("discount_override") or 0.0),
                    step=0.5,
                    key=f"disc_{scenario_id}_{pid}"
                )
                use_disc_override = st.checkbox("Use discount override?", value=bool(ov.get("discount_override")),
                                                key=f"use_disc_{scenario_id}_{pid}")

            # Return override
            with c3:
                ret_override = st.number_input(
                    "Return override (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=float(ov.get("return_rate_override") or 0.0),
                    step=0.5,
                    key=f"ret_{scenario_id}_{pid}"
                )
                use_ret_override = st.checkbox("Use return override?", value=bool(ov.get("return_rate_override")),
                                               key=f"use_ret_{scenario_id}_{pid}")

            # Total cost override
            with c4:
                cost_override_disp = st.number_input(
                    f"Total unit cost override ({sym})",
                    min_value=0.0,
                    value=from_bdt(ov.get("cost_override")) if ov.get("cost_override") else 0.0,
                    step=10.0,
                    key=f"cost_{scenario_id}_{pid}"
                )
                use_cost_override = st.checkbox("Use cost override?", value=bool(ov.get("cost_override")),
                                                key=f"use_cost_{scenario_id}_{pid}")

            # Quantity override
            with c5:
                qty_override = st.number_input(
                    "Qty override (units)",
                    min_value=0.0,
                    value=float(ov.get("qty_override") or 0.0),
                    step=10.0,
                    key=f"qty_{scenario_id}_{pid}"
                )
                use_qty_override = st.checkbox("Use qty override?", value=bool(ov.get("qty_override")),
                                               key=f"use_qty_{scenario_id}_{pid}")

            st.caption(
                f"Base values → Price: {sym}{from_bdt(base_price):.2f}, "
                f"Discount: {base_disc:.1f}%, Return: {base_ret:.1f}%, "
                f"Unit Cost: {sym}{from_bdt(base_cost):.2f}"
            )

            override_rows.append({
                "product_id": pid,
                "price_override": to_bdt(p_override_disp) if use_price_override else None,
                "discount_override": disc_override if use_disc_override else None,
                "return_rate_override": ret_override if use_ret_override else None,
                "cost_override": to_bdt(cost_override_disp) if use_cost_override else None,
                "qty_override": qty_override if use_qty_override else None
            })

    if st.button("💾 Save Product Overrides", use_container_width=True):
        save_scenario_products(scenario_id, override_rows)
        st.success("Product overrides saved ✅")
        st.rerun()


# ======================================================
# TAB 2 — OPEX Overrides
# ======================================================
with tab2:
    st.subheader("OPEX Overrides (Only for this Scenario)")
    st.caption("These apply on top of the OPEX attached to the base campaign in Module 3.")

    # show current attached opex library for info
    try:
        supabase = __import__("modules.db", fromlist=["get_supabase"]).get_supabase()
        lib_resp = supabase.table("opex_items").select("*").execute()
        lib = lib_resp.data or []
    except Exception:
        lib = []

    if not lib:
        st.info("No OPEX items found yet. Add items in Module 3 first.")
    else:
        opex_rows = []
        for it in lib:
            oid = it["id"]
            name = it["name"]
            cat = it.get("category", "General")
            base_cost = float(it["cost_bdt"])

            ov = opex_ov_map.get(oid, {})
            ov_cost_disp = from_bdt(ov.get("cost_override")) if ov.get("cost_override") else 0.0

            with st.expander(f"{name}  •  {cat}", expanded=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    cost_override_disp = st.number_input(
                        f"Override monthly/one-time cost ({sym})",
                        min_value=0.0,
                        value=ov_cost_disp,
                        step=100.0,
                        key=f"opex_cost_{scenario_id}_{oid}"
                    )
                with c2:
                    use_override = st.checkbox(
                        "Use override?",
                        value=bool(ov.get("cost_override")),
                        key=f"use_opex_{scenario_id}_{oid}"
                    )

                st.caption(f"Base cost: {sym}{from_bdt(base_cost):,.0f}")

                opex_rows.append({
                    "opex_item_id": oid,
                    "cost_override": to_bdt(cost_override_disp) if use_override else None
                })

        if st.button("💾 Save OPEX Overrides", use_container_width=True):
            save_scenario_opex(scenario_id, opex_rows)
            st.success("OPEX overrides saved ✅")
            st.rerun()


# ======================================================
# TAB 3 — FX Overrides
# ======================================================
with tab3:
    st.subheader("FX / Exchange Rate Overrides")
    st.caption("Optional for future versions. Useful if supplier costs depend on USD/GBP.")

    fx_rows = []
    for ccy in ["USD", "GBP"]:
        base_rate = st.session_state.exchange_rates.get(ccy, 1.0)
        ov = fx_ov_map.get(ccy, {})
        ov_rate = float(ov.get("rate") or base_rate)

        colA, colB = st.columns([2, 1])
        with colA:
            r = st.number_input(
                f"{ccy} rate override (BDT per {ccy})",
                min_value=0.0,
                value=float(ov_rate),
                step=1.0,
                key=f"fx_{scenario_id}_{ccy}"
            )
        with colB:
            use_override = st.checkbox(
                f"Use {ccy} override?",
                value=bool(ov.get("currency")),
                key=f"use_fx_{scenario_id}_{ccy}"
            )

        fx_rows.append({
            "currency": ccy,
            "rate": r if use_override else base_rate
        })

    if st.button("💾 Save FX Overrides", use_container_width=True):
        save_scenario_fx(scenario_id, fx_rows)
        st.success("FX overrides saved ✅")
        st.rerun()


# ======================================================
# TAB 4 — Results + Comparison
# ======================================================
with tab4:
    st.subheader("Scenario Results (Compared to Base Campaign)")

    # rebuild overrides fresh
    db_prod_overrides = fetch_scenario_products(scenario_id)
    db_opex_overrides = fetch_scenario_opex(scenario_id)

    # scenario forecast
    monthly_df_bdt, product_summary_df_bdt, totals_bdt = build_scenario_forecast(
        products=products,
        campaign=base_campaign,
        scenario_product_overrides=db_prod_overrides,
        scenario_opex_overrides=db_opex_overrides
    )

    if monthly_df_bdt.empty:
        st.warning("No quantities in base campaign or scenario.")
        st.stop()

    # Display totals
    totals_disp = {
        k: from_bdt(v) if ("revenue" in k or "profit" in k or "cost" in k or "opex" in k) else v
        for k, v in totals_bdt.items()
    }

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Scenario Units", f"{totals_disp['campaign_qty']:.0f}")
    c2.metric("Gross Revenue", f"{sym}{totals_disp['gross_revenue']:,.0f}")
    c3.metric("Effective Revenue", f"{sym}{totals_disp['effective_revenue']:,.0f}")
    c4.metric("Variable Profit", f"{sym}{totals_disp['net_profit_variable']:,.0f}")
    c5.metric("Total OPEX", f"{sym}{totals_disp['opex_total']:,.0f}")
    c6.metric("Net Profit After OPEX", f"{sym}{totals_disp['net_profit_after_opex']:,.0f}")

    st.divider()

    # Product summary table
    ps = product_summary_df_bdt.copy()
    for col in ["gross_revenue", "effective_revenue", "total_cost", "net_profit"]:
        ps[col] = ps[col].apply(from_bdt)

    st.markdown("### Product-Level Outcome")
    st.dataframe(ps, use_container_width=True, hide_index=True)

    # Monthly table
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

    st.markdown("### Monthly Outcome")
    st.dataframe(month_table, use_container_width=True, hide_index=True)

    # Charts
    st.markdown("### Charts")
    colA, colB = st.columns(2)

    with colA:
        fig1 = px.line(
            month_table,
            x="month_nice",
            y="effective_revenue",
            markers=True,
            title=f"Effective Revenue Curve ({sym})"
        )
        fig1.update_layout(height=420, yaxis_title=sym)
        st.plotly_chart(fig1, use_container_width=True)

    with colB:
        fig2 = px.bar(
            ps,
            x="product_name",
            y="effective_revenue",
            color="category",
            text_auto=".0f",
            title=f"Effective Revenue by Product ({sym})"
        )
        fig2.update_layout(height=420)
        st.plotly_chart(fig2, use_container_width=True)

    colC, colD = st.columns(2)

    with colC:
        fig3 = px.area(
            month_table,
            x="month_nice",
            y="net_profit",
            title=f"Variable Net Profit Curve ({sym})"
        )
        fig3.update_layout(height=380, yaxis_title=sym)
        st.plotly_chart(fig3, use_container_width=True)

    with colD:
        fig4 = px.pie(
            ps,
            values="campaign_qty",
            names="product_name",
            title="Scenario Unit Mix"
        )
        fig4.update_layout(height=380)
        st.plotly_chart(fig4, use_container_width=True)
