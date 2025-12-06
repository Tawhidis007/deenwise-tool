# pages/1_Product_Management.py
import streamlit as st
import pandas as pd
import plotly.express as px

from modules.products import (
    load_products,
    add_product, update_product, delete_product,
    validate_product_dict, products_to_dataframe
)

st.set_page_config(page_title="Product Management", page_icon="🧵", layout="wide")
# =========================================
# Custom CSS for modern / techy design
# =========================================
st.markdown("""
    <style>
    /* ---- GLOBAL ---- */
    .main {
        background: #0d1117 !important;
        color: #e6edf3 !important;
    }

    /* ---- HEADERS ---- */
    h1, h2, h3, h4 {
    color: #f2d98d !important;  /* Updated gold color */
    letter-spacing: -0.5px;
    font-weight: 700 !important;
}

    /* ---- SUBTLE SHADOW CARDS ---- */
    .stContainer {
        background: rgba(255,255,255,0.05) !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 0 25px rgba(0,0,0,0.2);
        backdrop-filter: blur(12px);
    }

    /* ---- DATAFRAME ---- */
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #161B22 !important;
    }

    /* ---- METRICS ---- */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #58a6ff !important;
    }

    /* ---- BUTTONS ---- */
    button[kind="primary"] {
        background: linear-gradient(90deg, #238636, #2ea043) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* ---- SELECTBOX / INPUT ---- */
    .stSelectbox, .stNumberInput, .stTextInput, .stTextArea {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 10px !important;
    }
            /* ---- BETTER TABLE DESIGN ---- */
.dataframe > div {
    background-color: #161b22 !important;
    border-radius: 10px !important;
}

thead tr th {
    background-color: #1f2937 !important;
    color: #58a6ff !important;
    font-weight: 600 !important;
}

tbody tr td {
    color: #e6edf3 !important;
}
    </style>
""", unsafe_allow_html=True)

st.title("Product Management (Module 1)")
st.caption("Add, edit, and remove DeenWise products. All unit costs and margins update live. Products are persisted in Supabase.")

# =====================================================
# GLOBAL CURRENCY (SAFE, DISPLAY-ONLY)
# - Internally store everything in BDT (Supabase)
# - Convert only for display + user input
# =====================================================
if "currency" not in st.session_state:
    st.session_state.currency = "BDT"

if "exchange_rates" not in st.session_state:
    # Oct 2025 Bangladesh Bank approximate values (fallback)
    # NOTE: Later we will load these from the exchange_rates table in Settings.
    st.session_state.exchange_rates = {
        "BDT": 1.0,
        "USD": 117.0,
        "GBP": 146.0
    }

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
    st.header("🌍 Display Currency")

    sel_currency = st.selectbox(
        "Show all numbers in:",
        options=["BDT", "USD", "GBP"],
        index=["BDT", "USD", "GBP"].index(st.session_state.currency),
        help="BDT is default. All product data is stored in BDT safely; display converts automatically."
    )
    st.session_state.currency = sel_currency

    st.caption(
        f"Rates (Oct 2025 BB approx): 1 USD = {st.session_state.exchange_rates['USD']} BDT, "
        f"1 GBP = {st.session_state.exchange_rates['GBP']} BDT"
    )

# =====================================================
# Tooltips — Bangladesh context
# =====================================================
HELP_PRODUCT_NAME = "Name of the product as it will appear internally or to customers. Example: Premium T-Shirt."
HELP_CATEGORY = "Product group—for example: Tops, Hoodies, Bottoms, Accessories. Helps with reporting and analysis."
HELP_PRICE = "Retail price shown in Bangladesh (website/Facebook/Daraz). Enter in selected currency."
HELP_MANUFACTURING = "Per-unit production cost in Bangladesh—fabric, stitching, printing, finishing, factory labour."
HELP_SHIPPING = "Per-unit logistics cost inside Bangladesh—factory to warehouse, courier/transport, delivery handling."
HELP_MARKETING = "Estimated marketing spend per unit—Facebook Ads, Boosts, Influencers, content cost allocated per unit."
HELP_PACKAGING = "Packaging cost per unit—poly mailer, box, tissue paper, tags, stickers."
HELP_RETURN_RATE = "Expected % returns/exchanges. In Bangladesh typical range is 2–10% depending on category."
HELP_DISCOUNT = "Expected average discount during campaign—launch offers, influencer codes, seasonal sales."
HELP_VAT = "If ON, selling price includes VAT. Bangladesh standard VAT ~15% for apparel (may vary)."
HELP_CODE = "Optional internal code e.g., TSHIRT-001. Useful for SKUs and reporting. If empty, system generates one."


# -----------------------------
# Load products from Supabase
# -----------------------------
# We re-load each time so state is consistent across pages
products = load_products()

# -----------------------------
# Layout tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📋 Products Table", "➕ Add Product", "✏️ Edit / Delete"])


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
            "price_bdt", "manufacturing_cost_bdt", "packaging_cost_bdt",
            "shipping_cost_bdt", "marketing_cost_bdt",
            "effective_price", "total_unit_cost",
            "unit_gross_profit", "unit_net_profit"
        ]
        for c in money_cols:
            if c in df.columns:
                df[c] = df[c].apply(from_bdt)

        sym = currency_symbol()
        # NEW: Drop technical fields
        drop_cols = ["id", "created_at", "updated_at"]
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        # Rename visible columns with currency symbol
        df = df.rename(columns={
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
            "vat_included": "VAT Included?"
        })


        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Profitability Snapshot")
        c1, c2 = st.columns(2)

        with c1:
            fig = px.bar(
                df,
                x="Product Name",
                y=f"Net Profit / Unit ({sym})",
                color="Category",
                title=f"Unit Net Profit by Product ({sym})",
                text_auto=".2f"
            )
            fig.update_layout(
                height=420,
                yaxis_title=sym,
                plot_bgcolor="#0d1117",
                paper_bgcolor="#0d1117",
                font_color="#e6edf3",
                legend=dict(font=dict(color="#e6edf3"))
            )

            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = px.bar(
                df,
                x="Product Name",
                y="Net Margin (%)",
                color="Category",
                title="Net Margin % by Product",
                text_auto=".1f"
            )
            fig2.update_layout(
                height=420,
                yaxis_title=sym,
                plot_bgcolor="#0d1117",
                paper_bgcolor="#0d1117",
                font_color="#e6edf3",
                legend=dict(font=dict(color="#e6edf3"))
            )

            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.info("✅ Products are auto-saved in Supabase. No manual save needed.")


# -----------------------------
# TAB 2: Add product form
# -----------------------------
with tab2:
    st.subheader("Add a New Product")
    sym = currency_symbol()

    with st.form("add_product_form", clear_on_submit=True):
        colA, colB, colC = st.columns(3)

        with colA:
            product_code = st.text_input("Product Code (optional)", placeholder="e.g., TSHIRT-001", help=HELP_CODE)
            name = st.text_input("Product Name*", placeholder="e.g., Premium T-Shirt", help=HELP_PRODUCT_NAME)
            category = st.text_input("Category*", placeholder="e.g., Tops", help=HELP_CATEGORY)
            notes = st.text_area("Notes (optional)", placeholder="Anything helpful for the team")

        with colB:
            price = st.number_input(f"Selling Price ({sym})*", min_value=0.0, value=2000.0, step=50.0, help=HELP_PRICE)
            manufacturing_cost = st.number_input(f"Manufacturing Cost ({sym})*", min_value=0.0, value=800.0, step=25.0, help=HELP_MANUFACTURING)
            packaging_cost = st.number_input(f"Packaging Cost ({sym})", min_value=0.0, value=100.0, step=10.0, help=HELP_PACKAGING)

        with colC:
            shipping_cost = st.number_input(f"Shipping Cost ({sym})", min_value=0.0, value=150.0, step=10.0, help=HELP_SHIPPING)
            marketing_cost = st.number_input(f"Marketing Cost per Unit ({sym})", min_value=0.0, value=120.0, step=10.0, help=HELP_MARKETING)
            return_rate = st.slider("Expected Return Rate (%)", 0.0, 50.0, 5.0, 0.5, help=HELP_RETURN_RATE) / 100.0
            discount_rate = st.slider("Discount / Promo Rate (%)", 0.0, 80.0, 10.0, 0.5, help=HELP_DISCOUNT) / 100.0
            vat_included = st.toggle("VAT Included in price?", value=True, help=HELP_VAT)

        submitted = st.form_submit_button("➕ Add Product")

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
                "is_active": True
            }

            errors = validate_product_dict(new_dict)
            if errors:
                st.error("Fix these before adding:\n- " + "\n- ".join(errors))
            else:
                add_product(products, new_dict)
                st.success(f"Added product: {new_dict['name']} ✅")
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
                product_code = st.text_input("Product Code (optional)", value=current.get("product_code", "") or "", help=HELP_CODE)
                name = st.text_input("Product Name*", value=current["name"], help=HELP_PRODUCT_NAME)
                category = st.text_input("Category*", value=current["category"], help=HELP_CATEGORY)
                notes = st.text_area("Notes", value=current.get("notes", ""))

            with colB:
                price = st.number_input(
                    f"Selling Price ({sym})*",
                    min_value=0.0,
                    value=from_bdt(current["price_bdt"]),
                    step=50.0,
                    help=HELP_PRICE
                )
                manufacturing_cost = st.number_input(
                    f"Manufacturing Cost ({sym})*",
                    min_value=0.0,
                    value=from_bdt(current["manufacturing_cost_bdt"]),
                    step=25.0,
                    help=HELP_MANUFACTURING
                )
                packaging_cost = st.number_input(
                    f"Packaging Cost ({sym})",
                    min_value=0.0,
                    value=from_bdt(current["packaging_cost_bdt"]),
                    step=10.0,
                    help=HELP_PACKAGING
                )

            with colC:
                shipping_cost = st.number_input(
                    f"Shipping Cost ({sym})",
                    min_value=0.0,
                    value=from_bdt(current["shipping_cost_bdt"]),
                    step=10.0,
                    help=HELP_SHIPPING
                )
                marketing_cost = st.number_input(
                    f"Marketing Cost per Unit ({sym})",
                    min_value=0.0,
                    value=from_bdt(current["marketing_cost_bdt"]),
                    step=10.0,
                    help=HELP_MARKETING
                )
                return_rate = st.slider(
                    "Expected Return Rate (%)",
                    0.0, 50.0,
                    float(current["return_rate_%"]),
                    0.5,
                    help=HELP_RETURN_RATE
                ) / 100.0
                discount_rate = st.slider(
                    "Discount / Promo Rate (%)",
                    0.0, 80.0,
                    float(current["discount_rate_%"]),
                    0.5,
                    help=HELP_DISCOUNT
                ) / 100.0
                vat_included = st.toggle("VAT Included in price?", value=bool(current["vat_included"]), help=HELP_VAT)

            col_save, col_del = st.columns([1, 1])
            save_btn = col_save.form_submit_button("💾 Save Changes")
            delete_btn = col_del.form_submit_button("🗑️ Delete Product")

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
                    "notes": notes.strip()
                }

                errors = validate_product_dict(updated)
                if errors:
                    st.error("Fix these before saving:\n- " + "\n- ".join(errors))
                else:
                    update_product(products, selected_id, updated)
                    st.success("Product updated ✅")
                    st.rerun()

            if delete_btn:
                delete_product(products, selected_id)
                st.warning(f"Deleted: {selected_name}")
                st.rerun()
