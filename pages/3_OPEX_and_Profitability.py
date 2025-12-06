# pages/3_OPEX_and_Profitability.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime

from modules.products import load_products
from modules.revenue import build_campaign_forecast, campaign_totals, month_range, month_label_to_nice
from modules.campaign_db import (
    fetch_campaigns,
    get_latest_campaign_or_create_default,
    fetch_campaign_products,
    fetch_month_weights,
    fetch_size_breakdown,
    fetch_product_month_weights,
)
from modules.opex_db import (
    fetch_opex_items,
    insert_opex_item,
    update_opex_item,
    delete_opex_item,
    fetch_campaign_opex_links,
    save_campaign_opex_links,
)
from modules.opex import rows_to_opex_items, expand_opex_for_campaign, opex_month_table

# ============================================
# Currency helpers (DISPLAY ONLY)
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
# Page Setup + Styling
# ============================================
st.set_page_config(page_title="OPEX & Profitability", page_icon="🏢", layout="wide")
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
    <span class="pill">OPEX</span>
    <h2>OPEX & Profitability</h2>
    <p>Add operating expenses, attach them to campaigns, and see net profit after overheads.</p>
</div>
""",
    unsafe_allow_html=True,
)

chart_bg = "#0f1119"
palette = ["#4BA3FF", "#2EE6D6", "#1F8BAE", "#7C5CFF", "#FF6B6B", "#FFC857"]
sym = currency_symbol()

# ============================================
# Campaign selection (same pattern as Module 2)
# ============================================
campaigns = fetch_campaigns()
active_campaign = get_latest_campaign_or_create_default()

campaign_name_map = {c["name"]: c["id"] for c in campaigns} if campaigns else {active_campaign["name"]: active_campaign["id"]}
campaign_names = list(campaign_name_map.keys())

with st.sidebar:
    st.header("Active Campaign")
    selected_campaign_name = st.selectbox(
        "Select campaign",
        options=campaign_names,
        index=campaign_names.index(active_campaign["name"]) if active_campaign["name"] in campaign_names else 0,
    )
    selected_campaign_id = campaign_name_map[selected_campaign_name]

# Load current campaign details fresh
curr_campaign = [c for c in (campaigns or [active_campaign]) if c["id"] == selected_campaign_id][0]
start_date = datetime.fromisoformat(curr_campaign["start_date"]).date()
end_date = datetime.fromisoformat(curr_campaign["end_date"]).date()
distribution_mode = curr_campaign.get("distribution_mode", "Uniform")
months = month_range(start_date, end_date)

st.divider()

# ============================================
# Load campaign inputs
# ============================================
products = load_products()
quantities, _ = fetch_campaign_products(selected_campaign_id)

db_product_weights = fetch_product_month_weights(selected_campaign_id)

# Legacy campaign-level weights for old mode (we keep for compatibility)
db_weights = fetch_month_weights(selected_campaign_id)
custom_month_weights = None  # Module 3 should not use legacy weights for forecast
db_sizes = fetch_size_breakdown(selected_campaign_id)

monthly_df_bdt, product_summary_df_bdt, size_df_bdt = build_campaign_forecast(
    products=products,
    quantities=quantities,
    start_date=start_date,
    end_date=end_date,
    distribution_mode=distribution_mode,
    custom_month_weights=None,  # legacy values disabled
    per_product_month_weights=db_product_weights if distribution_mode == "Custom" else None,
    size_breakdown=db_sizes if db_sizes else None,
)

revenue_month_table = (
    monthly_df_bdt.groupby(["month", "month_nice"], as_index=False)
    .agg(
        qty=("qty", "sum"),
        gross_revenue_bdt=("gross_revenue", "sum"),
        effective_revenue_bdt=("effective_revenue", "sum"),
        variable_cost_bdt=("total_cost", "sum"),
        net_profit_variable_bdt=("net_profit", "sum"),
    )
    .sort_values("month")
)

totals_bdt = campaign_totals(monthly_df_bdt)

# ============================================
# OPEX master + campaign links
# ============================================
opex_rows = fetch_opex_items(active_only=False)
opex_items = rows_to_opex_items(opex_rows)

linked_opex_ids = fetch_campaign_opex_links(selected_campaign_id)
linked_items = [o for o in opex_items if o.id in linked_opex_ids]

opex_df_bdt = expand_opex_for_campaign(start_date, end_date, linked_items)
opex_mt_bdt = opex_month_table(opex_df_bdt)

# merge revenue + opex per month
full_mt = revenue_month_table.merge(
    opex_mt_bdt,
    on=["month", "month_nice"],
    how="left",
).fillna({"opex_cost_bdt": 0})

full_mt["net_profit_after_opex_bdt"] = full_mt["net_profit_variable_bdt"] - full_mt["opex_cost_bdt"]

# Convert for display
full_mt_disp = full_mt.copy()
for c in [
    "gross_revenue_bdt",
    "effective_revenue_bdt",
    "variable_cost_bdt",
    "net_profit_variable_bdt",
    "opex_cost_bdt",
    "net_profit_after_opex_bdt",
]:
    full_mt_disp[c.replace("_bdt", "")] = full_mt_disp[c].apply(from_bdt)

# headline totals
total_opex_bdt = float(full_mt["opex_cost_bdt"].sum())
net_after_opex_bdt = float(full_mt["net_profit_after_opex_bdt"].sum())

# ============================================
# Tabs
# ============================================
st.markdown('<div class="tab-container">', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["OPEX Items", "Attach to Campaign", "Profitability View"])
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# TAB 1 — Manage global OPEX items
# -------------------------------------------------------------------
with tab1:
    st.subheader("Global OPEX Items (Reusable Across Campaigns)")
    st.caption("These are your standard operating expenses — you can reuse them in any campaign.")

    if opex_rows:
        df_opex = pd.DataFrame(opex_rows)
        df_disp = df_opex.copy()
        df_disp["cost"] = df_disp["cost_bdt"].apply(from_bdt)
        df_disp = df_disp[["name", "category", "cost", "start_month", "end_month", "is_one_time", "notes"]]
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
    else:
        st.info("No OPEX items yet. Add your first one below.")

    st.divider()
    st.markdown("### Add New OPEX Item")

    with st.form("add_opex_form", clear_on_submit=True):
        colA, colB, colC = st.columns(3)

        with colA:
            name = st.text_input("OPEX name*", placeholder="e.g., Office Rent")
            category = st.text_input("Category*", placeholder="e.g., Admin, Marketing, Ops")
            notes = st.text_area("Notes (optional)")

        with colB:
            cost_disp = st.number_input(f"Monthly / One-time Cost ({sym})*", min_value=0.0, value=0.0, step=100.0)

        with colC:
            start_month = st.text_input("Start month (YYYY-MM)*", value=months[0] if months else "2026-02")
            end_month = st.text_input("End month (YYYY-MM or blank)", value="")
            is_one_time = st.toggle("One-time cost?", value=False)

        submitted = st.form_submit_button("Add OPEX")

        if submitted:
            payload = {
                "name": name.strip(),
                "category": category.strip(),
                "cost_bdt": float(cost_disp) * st.session_state.exchange_rates[st.session_state.currency],
                "start_month": start_month.strip(),
                "end_month": end_month.strip() or None,
                "is_one_time": bool(is_one_time),
                "notes": notes.strip(),
            }

            if not payload["name"] or not payload["category"] or not payload["start_month"]:
                st.error("Please fill the required fields.")
            else:
                insert_opex_item(payload)
                st.success("OPEX item added.")
                st.rerun()

    st.divider()
    st.markdown("### Edit / Delete OPEX Item")

    if opex_rows:
        name_map = {r["name"]: r for r in opex_rows}
        sel_name = st.selectbox("Choose item", list(name_map.keys()))
        sel_row = name_map[sel_name]

        with st.form("edit_opex_form"):
            colA, colB, colC = st.columns(3)

            with colA:
                e_name = st.text_input("name*", value=sel_row["name"])
                e_cat = st.text_input("category*", value=sel_row["category"])
                e_notes = st.text_area("notes", value=sel_row.get("notes", ""))

            with colB:
                e_cost_disp = st.number_input(
                    f"cost ({sym})*",
                    min_value=0.0,
                    value=from_bdt(sel_row["cost_bdt"]),
                    step=100.0,
                )

            with colC:
                e_start = st.text_input("start_month*", value=sel_row["start_month"])
                e_end = st.text_input("end_month", value=sel_row.get("end_month") or "")
                e_one_time = st.toggle("one_time?", value=bool(sel_row.get("is_one_time", False)))

            csave, cdel = st.columns([1, 1])
            save_btn = csave.form_submit_button("Save changes")
            del_btn = cdel.form_submit_button("Delete item")

            if save_btn:
                update_opex_item(
                    sel_row["id"],
                    {
                        "name": e_name.strip(),
                        "category": e_cat.strip(),
                        "cost_bdt": float(e_cost_disp) * st.session_state.exchange_rates[st.session_state.currency],
                        "start_month": e_start.strip(),
                        "end_month": e_end.strip() or None,
                        "is_one_time": bool(e_one_time),
                        "notes": e_notes.strip(),
                    },
                )
                st.success("Updated.")
                st.rerun()

            if del_btn:
                delete_opex_item(sel_row["id"])
                st.warning("Deleted item.")
                st.rerun()

# -------------------------------------------------------------------
# TAB 2 — Attach OPEX to campaign
# -------------------------------------------------------------------
with tab2:
    st.subheader("Attach OPEX Items to This Campaign")
    st.caption("Pick which global OPEX items should be included in this campaign's profitability.")

    if not opex_items:
        st.info("No OPEX items exist yet. Create them in the previous tab.")
        st.stop()

    options = {f"{o.name} · {o.category}": o.id for o in opex_items}
    default_sel = [k for k, v in options.items() if v in linked_opex_ids]

    selected_labels = st.multiselect(
        "OPEX included in this campaign",
        options=list(options.keys()),
        default=default_sel,
    )
    selected_ids = [options[lbl] for lbl in selected_labels]

    save_campaign_opex_links(selected_campaign_id, selected_ids)
    st.success("Campaign OPEX selection saved.")

    st.divider()
    st.markdown("### What this means")
    st.write(
        """
- Items you select here will be counted every time this campaign loads.
- If you later edit an OPEX item's value, every campaign using it updates automatically.
        """
    )

# -------------------------------------------------------------------
# TAB 3 — Profitability view (Revenue + Variable Cost + OPEX)
# -------------------------------------------------------------------
with tab3:
    st.subheader("Profitability After OPEX")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Campaign Units", f"{totals_bdt['campaign_qty']:.0f}")
    c2.metric("Gross Revenue", f"{sym}{from_bdt(totals_bdt['gross_revenue']):,.0f}")
    c3.metric("Effective Revenue", f"{sym}{from_bdt(totals_bdt['effective_revenue']):,.0f}")
    c4.metric("Variable Profit", f"{sym}{from_bdt(totals_bdt['net_profit']):,.0f}")
    c5.metric("Total OPEX", f"{sym}{from_bdt(total_opex_bdt):,.0f}")
    c6.metric("Net Profit After OPEX", f"{sym}{from_bdt(net_after_opex_bdt):,.0f}")

    st.divider()

    st.markdown("### Monthly Financial Table")
    show_cols = [
        "month_nice",
        "qty",
        "gross_revenue",
        "effective_revenue",
        "variable_cost",
        "net_profit_variable",
        "opex_cost",
        "net_profit_after_opex",
    ]
    st.dataframe(full_mt_disp[show_cols], use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Charts")

    colA, colB = st.columns(2)

    with colA:
        fig1 = px.line(
            full_mt_disp,
            x="month_nice",
            y="effective_revenue",
            markers=True,
            title=f"Effective Revenue Over Campaign ({sym})",
            color_discrete_sequence=palette,
        )
        fig1.update_layout(height=380, yaxis_title=sym, xaxis_title="", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font_color="#e6edf3")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(
            full_mt_disp,
            x="month_nice",
            y="opex_cost",
            markers=True,
            title=f"OPEX Over Campaign ({sym})",
            color_discrete_sequence=palette,
        )
        fig2.update_layout(height=380, yaxis_title=sym, xaxis_title="", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font_color="#e6edf3")
        st.plotly_chart(fig2, use_container_width=True)

    with colB:
        fig3 = px.area(
            full_mt_disp,
            x="month_nice",
            y="net_profit_after_opex",
            title=f"Net Profit After OPEX ({sym})",
            color_discrete_sequence=palette,
        )
        fig3.update_layout(height=380, yaxis_title=sym, xaxis_title="", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font_color="#e6edf3")
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.bar(
            full_mt_disp,
            x="month_nice",
            y=["effective_revenue", "variable_cost", "opex_cost"],
            barmode="group",
            title=f"Revenue vs Variable Cost vs OPEX ({sym})",
            color_discrete_sequence=palette,
        )
        fig4.update_layout(height=380, yaxis_title=sym, xaxis_title="", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font_color="#e6edf3")
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.markdown("### OPEX Breakdown by Category")
    if not opex_df_bdt.empty:
        cat_df = opex_df_bdt.groupby("category", as_index=False).agg(cost_bdt=("cost_bdt", "sum"))
        cat_df["cost"] = cat_df["cost_bdt"].apply(from_bdt)

        fig5 = px.pie(
            cat_df,
            names="category",
            values="cost",
            title=f"OPEX Mix by Category ({sym})",
            color_discrete_sequence=palette,
        )
        fig5.update_layout(height=380, paper_bgcolor=chart_bg, font_color="#e6edf3")
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No OPEX linked to this campaign yet.")
