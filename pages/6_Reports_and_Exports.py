import streamlit as st
import pandas as pd
import io

from modules.products import load_products
from modules.campaign_db import (
    fetch_campaigns,
    fetch_campaign_products,
    fetch_month_weights,
    fetch_size_breakdown
)
from modules.opex_db import fetch_opex_items, fetch_campaign_opex_links
from modules.scenarios_db import (
    fetch_scenarios,
    fetch_scenario_products,
    fetch_scenario_opex,
    fetch_scenario_fx,
    fetch_scenario_campaign_links
)

from modules.revenue import (
    build_campaign_forecast,
    campaign_totals
)


# ============================================================
# Helpers
# ============================================================

def to_excel(sheets: dict) -> bytes:
    """
    sheets = {"SheetName": dataframe}
    Returns a downloadable XLSX file as bytes.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])  # Excel sheet name limit
    return buffer.getvalue()


# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="Reports & Exports",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Reports & Exports")
st.caption("Download campaign, scenario, product, and OPEX reports as Excel files.")

st.markdown("---")


# ============================================================
# SECTION 1 — Export Product Master
# ============================================================
st.header("📦 Product Master Export")

if st.button("Download Product Master (Excel)"):
    products = load_products()
    df = pd.DataFrame(products)
    
    st.download_button(
        "⬇ Download Products.xlsx",
        data=to_excel({"Products": df}),
        file_name="Products.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


st.markdown("---")


# ============================================================
# SECTION 2 — Export OPEX Master
# ============================================================
st.header("💼 OPEX Master Export")

if st.button("Download OPEX Master (Excel)"):
    opex = fetch_opex_items(active_only=False)
    df = pd.DataFrame(opex)

    st.download_button(
        "⬇ Download OPEX_Items.xlsx",
        data=to_excel({"OPEX_Items": df}),
        file_name="OPEX_Items.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")


# ============================================================
# 2️⃣ Export Campaign Forecast (FIXED)
# ============================================================

st.subheader("📦 Export Campaign Forecast")

# Load campaigns
campaigns = fetch_campaigns()
if campaigns:
    campaign_options = {c["name"]: c for c in campaigns}
    selected_campaign_name = st.selectbox("Select Campaign", list(campaign_options.keys()))
    selected_campaign = campaign_options[selected_campaign_name]
    selected_campaign_id = selected_campaign["id"]

    # Load Campaign Data
    products = load_products()
    quantities, _ = fetch_campaign_products(selected_campaign_id)
    custom_month_weights = fetch_month_weights(selected_campaign_id)
    size_breakdown = fetch_size_breakdown(selected_campaign_id)

    # Campaign dates
    from datetime import datetime as dt
    start_date = dt.fromisoformat(selected_campaign["start_date"]).date()
    end_date = dt.fromisoformat(selected_campaign["end_date"]).date()

    # Empty campaign?
    if not quantities:
        st.warning("This campaign has no product quantities.")
    else:
        # ---------------------------------------------------------
        # FIXED: call build_campaign_forecast with correct params
        # ---------------------------------------------------------
        monthly_df_bdt, product_df_bdt, size_df_bdt = build_campaign_forecast(
            products=products,
            quantities=quantities,
            start_date=start_date,
            end_date=end_date,
            distribution_mode=selected_campaign["distribution_mode"],
            custom_month_weights=custom_month_weights or None,
            size_breakdown=size_breakdown or None,
        )

        # Convert to nice Excel structure
        export_dict = {
            "Campaign Overview": pd.DataFrame([selected_campaign]),
            "Product Summary": product_df_bdt,
            "Monthly Forecast": monthly_df_bdt,
        }

        if size_df_bdt is not None and not size_df_bdt.empty:
            export_dict["Size Breakdown"] = size_df_bdt

        # Export Button
        st.success("Campaign forecast ready for export.")

        if st.button("📤 Export Campaign as Excel"):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for sheet, df in export_dict.items():
                    df.to_excel(writer, index=False, sheet_name=sheet)

            st.download_button(
                label="⬇️ Download Excel File",
                data=buffer.getvalue(),
                file_name=f"campaign_{selected_campaign_name.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

else:
    st.info("No campaigns found. Create one in the Forecast Dashboard.")


# ============================================================
# SECTION 4 — SCENARIO EXPORT
# ============================================================
st.header("🧪 Scenario Reports Export")

scenarios = fetch_scenarios()
if not scenarios:
    st.info("No scenarios found.")
    st.stop()

scenario_map = {s["name"]: s["id"] for s in scenarios}
selected_scenario_name = st.selectbox("Select a scenario", list(scenario_map.keys()))
scenario_id = scenario_map[selected_scenario_name]

if st.button("Generate Scenario Excel Report"):
    s = next(s for s in scenarios if s["id"] == scenario_id)

    # Load scenario components
    prod_overrides = fetch_scenario_products(scenario_id)
    opex_overrides = fetch_scenario_opex(scenario_id)
    fx_overrides = fetch_scenario_fx(scenario_id)
    campaign_links = fetch_scenario_campaign_links(scenario_id)

    excel_bytes = to_excel({
        "Scenario_Info": pd.DataFrame([s]),
        "Product_Overrides": pd.DataFrame(prod_overrides),
        "OPEX_Overrides": pd.DataFrame(opex_overrides),
        "FX_Overrides": pd.DataFrame(fx_overrides),
        "Linked_Campaigns": pd.DataFrame(campaign_links)
    })

    st.download_button(
        "⬇ Download Scenario_Report.xlsx",
        data=excel_bytes,
        file_name=f"Scenario_{selected_scenario_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
