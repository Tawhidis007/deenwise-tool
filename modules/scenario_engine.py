# modules/scenario_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import pandas as pd

from modules.products import Product
from modules.revenue import (
    month_range,
    month_label_to_nice,
    build_distribution_weights,
    distribute_quantity
)

from modules.campaign_db import (
    fetch_campaign_products,
    fetch_month_weights,
    fetch_size_breakdown,
    fetch_product_month_weights,   # NEW
)

# NOTE: module_3 opex linkage table name may vary.
# We'll attempt safe fetch; if missing, overhead=0.
from modules.db import get_supabase


# ============================================================
# Scenario Product View (allows total cost override)
# ============================================================

@dataclass
class ScenarioProduct:
    """
    A lightweight product object after override application.
    """
    id: str
    name: str
    category: str

    price_bdt: float
    manufacturing_cost_bdt: float
    packaging_cost_bdt: float
    shipping_cost_bdt: float
    marketing_cost_bdt: float

    return_rate: float        # 0-1
    discount_rate: float      # 0-1
    vat_included: bool = True
    notes: str = ""

    # optional override:
    cost_override_total_bdt: Optional[float] = None


def effective_price(p: ScenarioProduct) -> float:
    after_discount = p.price_bdt * (1 - p.discount_rate)
    realized = after_discount * (1 - p.return_rate)
    return realized


def total_unit_cost(p: ScenarioProduct) -> float:
    if p.cost_override_total_bdt is not None:
        return float(p.cost_override_total_bdt)
    return (
        p.manufacturing_cost_bdt +
        p.packaging_cost_bdt +
        p.shipping_cost_bdt +
        p.marketing_cost_bdt
    )


def unit_net_profit(p: ScenarioProduct) -> float:
    return effective_price(p) - total_unit_cost(p)


# ============================================================
# Safe OPEX fetch (campaign-linked)
# ============================================================

def _fetch_campaign_opex_items(campaign_id: str) -> List[Dict[str, Any]]:
    """
    Attempts to retrieve OPEX items attached to a campaign.
    If your Module 3 uses a different table name,
    change it here only.
    """
    supabase = get_supabase()

    # Most likely table name used in Module 3:
    possible_tables = [
        "campaign_opex_links",
        "campaign_opex_items",
        "campaign_opex"
    ]

    for t in possible_tables:
        try:
            resp = (
                supabase.table(t)
                .select("opex_item_id")
                .eq("campaign_id", campaign_id)
                .execute()
            )
            if resp.data is not None:
                return resp.data
        except Exception:
            continue

    return []


def _fetch_opex_library_by_ids(ids: List[str]) -> List[Dict[str, Any]]:
    if not ids:
        return []
    supabase = get_supabase()
    resp = supabase.table("opex_items").select("*").in_("id", ids).execute()
    return resp.data or []


# ============================================================
# Apply scenario overrides
# ============================================================

def apply_product_overrides(
    products: List[Product],
    overrides: List[Dict[str, Any]]
) -> Dict[str, ScenarioProduct]:
    """
    Returns map product_id -> ScenarioProduct
    """
    ov_map = {o["product_id"]: o for o in overrides}

    out = {}
    for p in products:
        o = ov_map.get(p.id)

        price_bdt = p.price_bdt
        discount_rate = p.discount_rate
        return_rate = p.return_rate
        cost_override_total = None

        if o:
            if o.get("price_override") is not None:
                price_bdt = float(o["price_override"])

            if o.get("discount_override") is not None:
                discount_rate = float(o["discount_override"]) / 100.0

            if o.get("return_rate_override") is not None:
                return_rate = float(o["return_rate_override"]) / 100.0

            if o.get("cost_override") is not None:
                cost_override_total = float(o["cost_override"])

        out[p.id] = ScenarioProduct(
            id=p.id,
            name=p.name,
            category=p.category,
            price_bdt=price_bdt,
            manufacturing_cost_bdt=p.manufacturing_cost_bdt,
            packaging_cost_bdt=p.packaging_cost_bdt,
            shipping_cost_bdt=p.shipping_cost_bdt,
            marketing_cost_bdt=p.marketing_cost_bdt,
            return_rate=return_rate,
            discount_rate=discount_rate,
            vat_included=p.vat_included,
            notes=p.notes,
            cost_override_total_bdt=cost_override_total
        )

    return out


def apply_quantity_overrides(
    base_quantities: Dict[str, float],
    overrides: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    qty_override replaces base campaign qty for that product.
    """
    out = dict(base_quantities)
    for o in overrides:
        pid = o["product_id"]
        if o.get("qty_override") is not None:
            out[pid] = float(o["qty_override"])
    return out


# ============================================================
# Scenario Forecast Builder
# ============================================================

def build_scenario_forecast(
    products: List[Product],
    campaign: Dict[str, Any],
    scenario_product_overrides: List[Dict[str, Any]],
    scenario_opex_overrides: List[Dict[str, Any]],
    distribution_mode_override: Optional[str] = None,
    custom_weights_override: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """
    Returns:
      monthly_df, product_summary_df, totals_dict
    All totals in BDT.
    """
    campaign_id = campaign["id"]
    start_date = date.fromisoformat(campaign["start_date"])
    end_date = date.fromisoformat(campaign["end_date"])
    distribution_mode = distribution_mode_override or campaign.get("distribution_mode", "Uniform")

    months = month_range(start_date, end_date)

    # pull base campaign inputs
    base_quantities, _ = fetch_campaign_products(campaign_id)

    # Legacy campaign-level weights (rows where product_id IS NULL)
    base_weights = fetch_month_weights(campaign_id)

    # NEW: per-product month weights (rows where product_id IS NOT NULL)
    base_product_weights = fetch_product_month_weights(campaign_id)

    base_sizes = fetch_size_breakdown(campaign_id)


    # apply overrides
    sp_map = apply_product_overrides(products, scenario_product_overrides)
    quantities = apply_quantity_overrides(base_quantities, scenario_product_overrides)

    # weights
    if distribution_mode == "Custom":
        weights_src = custom_weights_override or base_weights or {m: 1.0 for m in months}
        weights = build_distribution_weights(months, mode="Custom", custom_weights=weights_src)
    else:
        weights = build_distribution_weights(months, mode=distribution_mode)

    monthly_rows = []
    size_rows = []

    for pid, total_qty in quantities.items():
        if pid not in sp_map:
            continue

        p = sp_map[pid]

        # -------------------------------
        # Decide weights for THIS product
        # -------------------------------
        if distribution_mode == "Custom":
            if custom_weights_override:
                # Scenario-level override: same pattern for all products
                weights_for_pid = build_distribution_weights(
                    months,
                    mode="Custom",
                    custom_weights=custom_weights_override
                )
            elif base_product_weights and pid in base_product_weights:
                # NEW: per-product weights from campaign_month_weights
                this_custom = base_product_weights.get(pid, {})
                weights_for_pid = build_distribution_weights(
                    months,
                    mode="Custom",
                    custom_weights=this_custom
                )
            elif base_weights:
                # Fallback: legacy campaign-level weights if present
                weights_for_pid = build_distribution_weights(
                    months,
                    mode="Custom",
                    custom_weights=base_weights
                )
            else:
                # Fully fallback → equal distribution
                weights_for_pid = build_distribution_weights(
                    months,
                    mode="Custom",
                    custom_weights={m: 1.0 for m in months}
                )
        else:
            # Uniform / Front-loaded / Back-loaded → same weights for everyone
            weights_for_pid = build_distribution_weights(
                months,
                mode=distribution_mode
            )

        month_qtys = distribute_quantity(total_qty, weights_for_pid)


        # size breakdown (inherits base unless overridden by qty_override only)
        if base_sizes and pid in base_sizes:
            for size, sqty in base_sizes[pid].items():
                # scale size breakdown if qty overridden
                # ratio = overridden total / base total
                base_total = sum(base_sizes[pid].values()) or 1
                ratio = total_qty / base_total if base_total else 1
                adj_qty = float(sqty) * ratio

                ep = effective_price(p)
                tuc = total_unit_cost(p)
                unp = unit_net_profit(p)

                size_rows.append({
                    "product_id": pid,
                    "product_name": p.name,
                    "size": size,
                    "qty": adj_qty,
                    "gross_revenue": p.price_bdt * adj_qty,
                    "effective_revenue": ep * adj_qty,
                    "total_cost": tuc * adj_qty,
                    "net_profit": unp * adj_qty
                })

        for m, q in month_qtys.items():
            ep = effective_price(p)
            tuc = total_unit_cost(p)
            unp = unit_net_profit(p)

            monthly_rows.append({
                "month": m,
                "month_nice": month_label_to_nice(m),
                "product_id": pid,
                "product_name": p.name,
                "category": p.category,
                "qty": q,
                "price_bdt": p.price_bdt,
                "effective_price_bdt": ep,
                "gross_revenue": p.price_bdt * q,
                "effective_revenue": ep * q,
                "total_cost": tuc * q,
                "net_profit": unp * q
            })

    monthly_df = pd.DataFrame(monthly_rows)

    if monthly_df.empty:
        product_summary_df = pd.DataFrame()
    else:
        product_summary_df = (
            monthly_df.groupby(["product_id", "product_name", "category"], as_index=False)
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

    totals = {
        "campaign_qty": float(monthly_df["qty"].sum()) if not monthly_df.empty else 0,
        "gross_revenue": float(monthly_df["gross_revenue"].sum()) if not monthly_df.empty else 0,
        "effective_revenue": float(monthly_df["effective_revenue"].sum()) if not monthly_df.empty else 0,
        "total_cost": float(monthly_df["total_cost"].sum()) if not monthly_df.empty else 0,
        "net_profit_variable": float(monthly_df["net_profit"].sum()) if not monthly_df.empty else 0,
    }

    # ==========================
    # OPEX impact (campaign-linked + scenario overrides)
    # ==========================
    opex_total = 0.0

    # base attached opex items
    attached = _fetch_campaign_opex_items(campaign_id)
    attached_ids = [r["opex_item_id"] for r in attached] if attached else []
    lib_items = _fetch_opex_library_by_ids(attached_ids)

    # override map
    ov_map = {o["opex_item_id"]: o for o in scenario_opex_overrides}

    # sum OPEX for campaign months
    for it in lib_items:
        base_cost = float(it["cost_bdt"])
        is_one_time = bool(it.get("is_one_time", False))
        start_m = it.get("start_month")
        end_m = it.get("end_month")

        # if scenario override exists, replace cost
        if it["id"] in ov_map and ov_map[it["id"]].get("cost_override") is not None:
            base_cost = float(ov_map[it["id"]]["cost_override"])

        if is_one_time:
            opex_total += base_cost
        else:
            # monthly recurring across overlap months
            # if no window specified, assume campaign months
            if start_m is None:
                start_m = months[0]
            if end_m is None:
                end_m = months[-1]

            for m in months:
                if start_m <= m <= end_m:
                    opex_total += base_cost

    totals["opex_total"] = opex_total
    totals["net_profit_after_opex"] = totals["net_profit_variable"] - opex_total

    return monthly_df, product_summary_df, totals
