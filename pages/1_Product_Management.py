# pages/1_Product_Management.py
import streamlit as st
import pandas as pd
import plotly.express as px

from modules.products import (
    load_products,
    add_product,
    update_product,
    delete_product,
    validate_product_dict,
    products_to_dataframe,
)

st.set_page_config(page_title="Product Management", page_icon="📦", layout="wide")

# =========================================
# Polished minimal styling
# =========================================
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
.section-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 18px 60px rgba(0,0,0,0.42);
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
button, .stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
}
button[kind="primary"], .stButton button[kind="primary"] {
    background: linear-gradient(120deg, var(--accent), var(--accent-2)) !important;
    color: #0b0c10 !important;
    border: none !important;
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
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin: 12px 0 6px 0;
}
.stat-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
}
.stat-label { color: var(--muted); font-size: 12px; letter-spacing: 0.6px; text-transform: uppercase; }
.stat-value { color: var(--text); font-size: 20px; font-weight: 700; }
.panel-inline {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
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
    <span class="pill">Products</span>
    <h2>Product Management</h2>
    <p>Create, review, and maintain your product catalogue. All margins update live and sync to Supabase.</p>
</div>
""",
    unsafe_allow_html=True,
)

# =====================================================
# GLOBAL CURRENCY (display only)
# =====================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    st.session_state.exchange_rates = {"BDT": 1.0, "USD": 117.0, "GBP": 146.0}

CURRENCY_SYMBOLS = {"BDT": "৳", "USD": "$", "GBP": "£"}


def currency_symbol():
    return CURRENCY_SYMBOLS.get(st.session_state.currency, "৳")


def to_bdt(amount_display: float) -> float:
    """Convert display currency -> BDT for storage."""
    rate = st.session_state.exchange_rates.get(st.session_state.currency, 1.0)
    return float(amount_display) * rate


def from_bdt(amount_bdt: float) -> float:
    """Convert BDT -> display currency for UI."""
    rate = st.session_state.exchange_rates.get(st.session_state.currency, 1.0)
    return float(amount_bdt) / rate


# -----------------------------
# Sidebar: Currency selector
# -----------------------------
with st.sidebar:
    st.header("Display Currency")

    sel_currency = st.selectbox(
        "Show all numbers in:",
        options=["BDT", "USD", "GBP"],
        index=["BDT", "USD", "GBP"].index(st.session_state.currency),
        help="BDT is default. All product data is stored in BDT; display converts automatically.",
    )
    st.session_state.currency = sel_currency

    st.caption(
        f"Rates (approx): 1 USD = {st.session_state.exchange_rates['USD']} BDT, "
        f"1 GBP = {st.session_state.exchange_rates['GBP']} BDT"
    )

# =====================================================
# Tooltips — Bangladesh context
# =====================================================
HELP_PRODUCT_NAME = "Name of the product as it will appear internally or to customers. Example: Premium T-Shirt."
HELP_CATEGORY = "Product group — for example: Tops, Hoodies, Bottoms, Accessories. Helps with reporting and analysis."
HELP_PRICE = "Retail price shown in Bangladesh (website/Facebook/Daraz). Enter in selected currency."
HELP_MANUFACTURING = "Per-unit production cost in Bangladesh — fabric, stitching, printing, finishing, factory labour."
HELP_SHIPPING = "Per-unit logistics cost inside Bangladesh — factory to warehouse, courier/transport, delivery handling."
HELP_MARKETING = "Estimated marketing spend per unit — Facebook Ads, Boosts, Influencers, content cost allocated per unit."
HELP_PACKAGING = "Packaging cost per unit — poly mailer, box, tissue paper, tags, stickers."
HELP_RETURN_RATE = "Expected % returns/exchanges. In Bangladesh typical range is 2–10% depending on category."
HELP_DISCOUNT = "Expected average discount during campaign — launch offers, influencer codes, seasonal sales."
HELP_VAT = "If ON, selling price includes VAT. Bangladesh standard VAT ~15% for apparel (may vary)."
HELP_CODE = "Optional internal code e.g., TSHIRT-001. Useful for SKUs and reporting. If empty, system generates one."

# -----------------------------
# Load products from Supabase
# -----------------------------
products = load_products()

# -----------------------------
# Layout tabs
# -----------------------------
st.markdown('<div class="tab-container">', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["Products", "Add Product", "Edit / Delete"])
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# TAB 1: Table + quick charts
# -----------------------------
with tab1:
    df_bdt = products_to_dataframe(products)

    st.subheader("Current Product Catalogue")
    if df_bdt.empty:
        st.warning("No products yet. Add your first one in the next tab.")
    else:
        # Convert money columns for display
        df = df_bdt.copy()
        money_cols = [
            "price_bdt",
            "manufacturing_cost_bdt",
            "packaging_cost_bdt",
            "shipping_cost_bdt",
            "marketing_cost_bdt",
            "effective_price",
            "total_unit_cost",
            "unit_gross_profit",
            "unit_net_profit",
        ]
        for c in money_cols:
            if c in df.columns:
                df[c] = df[c].apply(from_bdt)

        sym = currency_symbol()
        # NEW: Drop technical fields
        drop_cols = ["id", "created_at", "updated_at"]
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        # Rename visible columns with currency symbol
        df = df.rename(
            columns={
                # ID & code
                "id": "ID",
                "product_code": "Product Code",
                # Text fields
                "name": "Product Name",
                "category": "Category",
                "notes": "Notes",
                # Costs & prices with currency symbol
                "price_bdt": f"Price ({sym})",
                "manufacturing_cost_bdt": f"Manufacturing Cost ({sym})",
                "packaging_cost_bdt": f"Packaging Cost ({sym})",
                "shipping_cost_bdt": f"Shipping Cost ({sym})",
                "marketing_cost_bdt": f"Marketing Cost ({sym})",
                # Profit & cost calculations
                "effective_price": f"Effective Price ({sym})",
                "total_unit_cost": f"Total Unit Cost ({sym})",
                "unit_gross_profit": f"Gross Profit / Unit ({sym})",
                "unit_net_profit": f"Net Profit / Unit ({sym})",
                # Percentage fields
                "return_rate_%": "Return Rate (%)",
                "discount_rate_%": "Discount Rate (%)",
                "net_margin_%": "Net Margin (%)",
                # Flags
                "vat_included": "VAT Included?",
            }
        )

        with st.container():
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Profitability Snapshot")
        c1, c2 = st.columns(2)

        chart_bg = "#0f1119"
        palette = ["#4BA3FF", "#2EE6D6", "#1F8BAE", "#7C5CFF", "#FF6B6B", "#FFC857"]

        with c1:
            fig = px.bar(
                df,
                x="Product Name",
                y=f"Net Profit / Unit ({sym})",
                color="Category",
                title=f"Unit Net Profit by Product ({sym})",
                text_auto=".2f",
                color_discrete_sequence=palette,
            )
            fig.update_layout(
                height=420,
                yaxis_title=sym,
                plot_bgcolor=chart_bg,
                paper_bgcolor=chart_bg,
                font_color="#e6edf3",
                legend=dict(font=dict(color="#e6edf3")),
            )

            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = px.bar(
                df,
                x="Product Name",
                y="Net Margin (%)",
                color="Category",
                title="Net Margin % by Product",
                text_auto=".1f",
                color_discrete_sequence=palette,
            )
            fig2.update_layout(
                height=420,
                yaxis_title=sym,
                plot_bgcolor=chart_bg,
                paper_bgcolor=chart_bg,
                font_color="#e6edf3",
                legend=dict(font=dict(color="#e6edf3")),
            )

            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.info("Products are auto-saved in Supabase. No manual save needed.")

# -----------------------------
# TAB 2: Add product form
# -----------------------------
with tab2:
    st.subheader("Add a New Product")
    sym = currency_symbol()

    with st.form("add_product_form", clear_on_submit=True):
        colA, colB, colC = st.columns(3)

        with colA:
            product_code = st.text_input(
                "Product Code (optional)", placeholder="e.g., TSHIRT-001", help=HELP_CODE
            )
            name = st.text_input(
                "Product Name*", placeholder="e.g., Premium T-Shirt", help=HELP_PRODUCT_NAME
            )
            category = st.text_input("Category*", placeholder="e.g., Tops", help=HELP_CATEGORY)
            notes = st.text_area("Notes (optional)", placeholder="Anything helpful for the team")

        with colB:
            price = st.number_input(
                f"Selling Price ({sym})*",
                min_value=0.0,
                value=2000.0,
                step=50.0,
                help=HELP_PRICE,
            )
            manufacturing_cost = st.number_input(
                f"Manufacturing Cost ({sym})*",
                min_value=0.0,
                value=800.0,
                step=25.0,
                help=HELP_MANUFACTURING,
            )
            packaging_cost = st.number_input(
                f"Packaging Cost ({sym})", min_value=0.0, value=100.0, step=10.0, help=HELP_PACKAGING
            )

        with colC:
            shipping_cost = st.number_input(
                f"Shipping Cost ({sym})", min_value=0.0, value=150.0, step=10.0, help=HELP_SHIPPING
            )
            marketing_cost = st.number_input(
                f"Marketing Cost per Unit ({sym})",
                min_value=0.0,
                value=120.0,
                step=10.0,
                help=HELP_MARKETING,
            )
            return_rate = st.slider(
                "Expected Return Rate (%)", 0.0, 50.0, 5.0, 0.5, help=HELP_RETURN_RATE
            ) / 100.0
            discount_rate = st.slider(
                "Discount / Promo Rate (%)", 0.0, 80.0, 10.0, 0.5, help=HELP_DISCOUNT
            ) / 100.0
            vat_included = st.toggle("VAT Included in price?", value=True, help=HELP_VAT)

        submitted = st.form_submit_button("Add Product")

        if submitted:
            new_dict = {
                "product_code": product_code.strip() or None,
                "name": name.strip(),
                "category": category.strip(),
                # Convert to BDT for storage (DB)
                "price_bdt": to_bdt(price),
                "manufacturing_cost_bdt": to_bdt(manufacturing_cost),
                "packaging_cost_bdt": to_bdt(packaging_cost),
                "shipping_cost_bdt": to_bdt(shipping_cost),
                "marketing_cost_bdt": to_bdt(marketing_cost),
                "return_rate": float(return_rate),
                "discount_rate": float(discount_rate),
                "vat_included": bool(vat_included),
                "notes": notes.strip(),
                "is_active": True,
            }

            errors = validate_product_dict(new_dict)
            if errors:
                st.error("Fix these before adding:\n- " + "\n- ".join(errors))
            else:
                add_product(products, new_dict)
                st.success(f"Added product: {new_dict['name']}.")
                st.rerun()

# -----------------------------
# TAB 3: Edit / Delete
# -----------------------------
with tab3:
    st.subheader("Edit or Delete Existing Products")

    if not products:
        st.info("No products to edit yet.")
    else:
        df_bdt = products_to_dataframe(products)

        prod_name_map = {row["name"]: row["id"] for _, row in df_bdt.iterrows()}
        selected_name = st.selectbox("Choose product", list(prod_name_map.keys()))
        selected_id = prod_name_map[selected_name]

        current = df_bdt[df_bdt["id"] == selected_id].iloc[0].to_dict()
        sym = currency_symbol()

        with st.form("edit_product_form"):
            colA, colB, colC = st.columns(3)

            with colA:
                product_code = st.text_input(
                    "Product Code (optional)",
                    value=current.get("product_code", "") or "",
                    help=HELP_CODE,
                )
                name = st.text_input("Product Name*", value=current["name"], help=HELP_PRODUCT_NAME)
                category = st.text_input("Category*", value=current["category"], help=HELP_CATEGORY)
                notes = st.text_area("Notes", value=current.get("notes", ""))

            with colB:
                price = st.number_input(
                    f"Selling Price ({sym})*",
                    min_value=0.0,
                    value=from_bdt(current["price_bdt"]),
                    step=50.0,
                    help=HELP_PRICE,
                )
                manufacturing_cost = st.number_input(
                    f"Manufacturing Cost ({sym})*",
                    min_value=0.0,
                    value=from_bdt(current["manufacturing_cost_bdt"]),
                    step=25.0,
                    help=HELP_MANUFACTURING,
                )
                packaging_cost = st.number_input(
                    f"Packaging Cost ({sym})",
                    min_value=0.0,
                    value=from_bdt(current["packaging_cost_bdt"]),
                    step=10.0,
                    help=HELP_PACKAGING,
                )

            with colC:
                shipping_cost = st.number_input(
                    f"Shipping Cost ({sym})",
                    min_value=0.0,
                    value=from_bdt(current["shipping_cost_bdt"]),
                    step=10.0,
                    help=HELP_SHIPPING,
                )
                marketing_cost = st.number_input(
                    f"Marketing Cost per Unit ({sym})",
                    min_value=0.0,
                    value=from_bdt(current["marketing_cost_bdt"]),
                    step=10.0,
                    help=HELP_MARKETING,
                )
                return_rate = (
                    st.slider(
                        "Expected Return Rate (%)",
                        0.0,
                        50.0,
                        float(current["return_rate_%"]),
                        0.5,
                        help=HELP_RETURN_RATE,
                    )
                    / 100.0
                )
                discount_rate = (
                    st.slider(
                        "Discount / Promo Rate (%)",
                        0.0,
                        80.0,
                        float(current["discount_rate_%"]),
                        0.5,
                        help=HELP_DISCOUNT,
                    )
                    / 100.0
                )
                vat_included = st.toggle(
                    "VAT Included in price?", value=bool(current["vat_included"]), help=HELP_VAT
                )

            col_save, col_del = st.columns([1, 1])
            save_btn = col_save.form_submit_button("Save Changes")
            delete_btn = col_del.form_submit_button("Delete Product")

            if save_btn:
                updated = {
                    "product_code": product_code.strip() or None,
                    "name": name.strip(),
                    "category": category.strip(),
                    # Convert to BDT for storage (DB)
                    "price_bdt": to_bdt(price),
                    "manufacturing_cost_bdt": to_bdt(manufacturing_cost),
                    "packaging_cost_bdt": to_bdt(packaging_cost),
                    "shipping_cost_bdt": to_bdt(shipping_cost),
                    "marketing_cost_bdt": to_bdt(marketing_cost),
                    "return_rate": float(return_rate),
                    "discount_rate": float(discount_rate),
                    "vat_included": bool(vat_included),
                    "notes": notes.strip(),
                }

                errors = validate_product_dict(updated)
                if errors:
                    st.error("Fix these before saving:\n- " + "\n- ".join(errors))
                else:
                    update_product(products, selected_id, updated)
                    st.success("Product updated.")
                    st.rerun()

            if delete_btn:
                delete_product(products, selected_id)
                st.warning(f"Deleted: {selected_name}")
                st.rerun()
