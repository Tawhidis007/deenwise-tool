# modules/revenue.py
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import calendar
import pandas as pd
import streamlit as st  # SAFE import for optional currency helpers

from modules.products import (
    Product,
    effective_price,
    total_unit_cost,
    unit_net_profit
)

# ============================================================
# OPTIONAL CURRENCY HELPERS (DISPLAY ONLY)
# ============================================================
def convert_currency(amount_bdt: float) -> float:
    """Convert BDT → selected display currency."""
    if "currency" not in st.session_state:
        return amount_bdt
    currency = st.session_state.currency
    rate = st.session_state.exchange_rates.get(currency, 1.0)
    return amount_bdt / rate


def currency_symbol() -> str:
    c = st.session_state.get("currency", "BDT")
    return {"BDT": "৳", "USD": "$", "GBP": "£"}.get(c, "৳")


# -----------------------------
# Date / Month helpers
# -----------------------------
def month_range(start: date, end: date) -> List[str]:
    if end < start:
        start, end = end, start

    months = []
    y, m = start.year, start.month
    while (y < end.year) or (y == end.year and m <= end.month):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def month_label_to_nice(label: str) -> str:
    y, m = label.split("-")
    m_int = int(m)
    return f"{calendar.month_abbr[m_int]} {y}"


# -----------------------------
# Distribution Logic
# -----------------------------
def build_distribution_weights(
    months: List[str],
    mode: str = "Uniform",
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    n = len(months)
    if n == 0:
        return {}

    if mode == "Uniform":
        w = [1] * n
    elif mode == "Front-loaded":
        w = list(range(n, 0, -1))
    elif mode == "Back-loaded":
        w = list(range(1, n + 1))
    elif mode == "Custom":
        if not custom_weights:
            w = [1] * n
        else:
            w = [max(0.0, float(custom_weights.get(m, 0.0))) for m in months]
            if sum(w) == 0:
                w = [1] * n
    else:
        w = [1] * n

    total = sum(w)
    return {months[i]: w[i] / total for i in range(n)}


def distribute_quantity(total_qty: float, weights: Dict[str, float]) -> Dict[str, float]:
    return {m: total_qty * w for m, w in weights.items()}


# -----------------------------
# Core Revenue Calculations (BDT ONLY)
# -----------------------------
def revenue_for_product_month(product: Product, qty: float) -> Dict[str, float]:
    ep = effective_price(product)
    tuc = total_unit_cost(product)
    unp = unit_net_profit(product)

    gross_revenue = product.price_bdt * qty
    effective_revenue = ep * qty
    total_cost = tuc * qty
    total_profit = unp * qty

    return {
        "gross_revenue": gross_revenue,
        "effective_revenue": effective_revenue,
        "total_unit_cost": total_cost,
        "net_profit": total_profit
    }


def build_campaign_forecast(
    products: List[Product],
    quantities: Dict[str, float],
    start_date: date,
    end_date: date,
    distribution_mode: str = "Uniform",
    custom_month_weights: Optional[Dict[str, float]] = None,
    per_product_month_weights: Optional[Dict[str, Dict[str, float]]] = None,
    size_breakdown: Optional[Dict[str, Dict[str, float]]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    months = month_range(start_date, end_date)

    # Base campaign-level weights (used when no per-product override)
    base_weights = build_distribution_weights(
        months,
        mode=distribution_mode,
        custom_weights=custom_month_weights
    )


    monthly_rows = []
    size_rows = []

    prod_map = {p.id: p for p in products}

    for pid, total_qty in quantities.items():
        if pid not in prod_map:
            continue

        p = prod_map[pid]

        # Decide weights for THIS product
        if (
            distribution_mode == "Custom"
            and per_product_month_weights
            and pid in per_product_month_weights
        ):
            this_custom = per_product_month_weights.get(pid, {})
            weights_for_pid = build_distribution_weights(
                months,
                mode="Custom",
                custom_weights=this_custom
            )
        else:
            # Uniform / Front / Back, or no per-product override
            weights_for_pid = base_weights

        month_qtys = distribute_quantity(total_qty, weights_for_pid)


        if size_breakdown and pid in size_breakdown:
            sdict = size_breakdown[pid]
            for size, sqty in sdict.items():
                econ = revenue_for_product_month(p, sqty)
                size_rows.append({
                    "product_id": pid,
                    "product_name": p.name,
                    "size": size,
                    "qty": sqty,
                    "gross_revenue": econ["gross_revenue"],
                    "effective_revenue": econ["effective_revenue"],
                    "total_cost": econ["total_unit_cost"],
                    "net_profit": econ["net_profit"]
                })

        for m, q in month_qtys.items():
            econ = revenue_for_product_month(p, q)
            monthly_rows.append({
                "month": m,
                "month_nice": month_label_to_nice(m),
                "product_id": pid,
                "product_name": p.name,
                "category": p.category,
                "qty": q,

                # keep BOTH keys for backward compatibility
                "price_bdt": p.price_bdt,
                "price": p.price_bdt,

                "effective_price": effective_price(p),
                "gross_revenue": econ["gross_revenue"],
                "effective_revenue": econ["effective_revenue"],
                "total_cost": econ["total_unit_cost"],
                "net_profit": econ["net_profit"]
            })

    monthly_df = pd.DataFrame(monthly_rows)

    if monthly_df.empty:
        product_summary_df = pd.DataFrame()
    else:
        product_summary_df = (
            monthly_df
            .groupby(["product_id", "product_name", "category"], as_index=False)
            .agg(
                campaign_qty=("qty", "sum"),
                gross_revenue=("gross_revenue", "sum"),
                effective_revenue=("effective_revenue", "sum"),
                total_cost=("total_cost", "sum"),
                net_profit=("net_profit", "sum")
            )
        )
        product_summary_df["gross_margin_%"] = (
            (product_summary_df["gross_revenue"] - product_summary_df["total_cost"])
            / product_summary_df["gross_revenue"].replace(0, 1)
        ) * 100
        product_summary_df["net_margin_%"] = (
            product_summary_df["net_profit"]
            / product_summary_df["effective_revenue"].replace(0, 1)
        ) * 100

    size_df = pd.DataFrame(size_rows) if size_rows else pd.DataFrame()
    return monthly_df, product_summary_df, size_df


def campaign_totals(monthly_df: pd.DataFrame) -> Dict[str, float]:
    if monthly_df.empty:
        return {
            "campaign_qty": 0,
            "gross_revenue": 0,
            "effective_revenue": 0,
            "total_cost": 0,
            "net_profit": 0
        }

    return {
        "campaign_qty": float(monthly_df["qty"].sum()),
        "gross_revenue": float(monthly_df["gross_revenue"].sum()),
        "effective_revenue": float(monthly_df["effective_revenue"].sum()),
        "total_cost": float(monthly_df["total_cost"].sum()),
        "net_profit": float(monthly_df["net_profit"].sum())
    }
