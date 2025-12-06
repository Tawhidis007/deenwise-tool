# modules/campaign_db.py
from __future__ import annotations

from typing import Dict, Any, List, Tuple
from datetime import date
from modules.db import get_supabase


# ============================================================
# Campaigns (high-level)
# ============================================================

def fetch_campaigns() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.table("campaigns").select("*").order("created_at", desc=True).execute()
    return resp.data or []


def create_campaign(
    name: str,
    start_date: date,
    end_date: date,
    distribution_mode: str = "Uniform",
    currency: str = "BDT"
) -> Dict[str, Any]:
    supabase = get_supabase()
    payload = {
        "name": name,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "distribution_mode": distribution_mode,
        "currency": currency,
    }
    resp = supabase.table("campaigns").insert(payload).execute()
    return resp.data[0]


def update_campaign(campaign_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    if "start_date" in fields and isinstance(fields["start_date"], date):
        fields["start_date"] = str(fields["start_date"])
    if "end_date" in fields and isinstance(fields["end_date"], date):
        fields["end_date"] = str(fields["end_date"])
    resp = supabase.table("campaigns").update(fields).eq("id", campaign_id).execute()
    return resp.data[0]


def get_latest_campaign_or_create_default() -> Dict[str, Any]:
    campaigns = fetch_campaigns()
    if campaigns:
        return campaigns[0]
    return create_campaign(
        name="Default Campaign",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 4, 1),
        distribution_mode="Uniform",
        currency="BDT"
    )


# ============================================================
# Campaign Quantities (YOUR table: campaign_quantities)
# ============================================================

def fetch_campaign_products(campaign_id: str) -> Tuple[Dict[str, float], Dict[str, str]]:
    """
    Backward compatible name:
    - quantities: product_id -> total_qty
    - row_ids: product_id -> campaign_quantities.id
    """
    supabase = get_supabase()
    resp = (
        supabase.table("campaign_quantities")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    rows = resp.data or []

    quantities: Dict[str, float] = {}
    row_ids: Dict[str, str] = {}

    for r in rows:
        pid = r["product_id"]
        # support either total_qty or qty if you still have old column
        qty_val = r.get("total_qty", r.get("qty", 0))
        quantities[pid] = float(qty_val or 0)
        row_ids[pid] = r["id"]

    return quantities, row_ids


def save_campaign_products(campaign_id: str, quantities: Dict[str, float]) -> None:
    supabase = get_supabase()

    supabase.table("campaign_quantities").delete().eq("campaign_id", campaign_id).execute()

    payload = [
        {
            "campaign_id": campaign_id,
            "product_id": pid,
            "total_qty": float(qty)
        }
        for pid, qty in quantities.items()
        if float(qty) > 0
    ]

    if payload:
        supabase.table("campaign_quantities").insert(payload).execute()


# ============================================================
# Month weights (YOUR table: campaign_month_weights)
# ============================================================

def fetch_month_weights(campaign_id: str) -> Dict[str, float]:
    """
    Legacy campaign-level month weights (rows where product_id is NULL).
    Still used for reporting / backwards compatibility.
    """
    supabase = get_supabase()
    resp = (
        supabase.table("campaign_month_weights")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    rows = resp.data or []

    # Only keep rows without product_id → campaign-level weights
    rows = [r for r in rows if not r.get("product_id")]

    return {r["month_label"]: float(r.get("weight", 1.0)) for r in rows}



def save_month_weights(campaign_id: str, weights: Dict[str, float]) -> None:
    """
    Legacy campaign-level month weights (product_id is NULL).
    """
    supabase = get_supabase()

    # Delete only legacy rows (no product_id)
    resp = (
        supabase.table("campaign_month_weights")
        .select("id, product_id")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    rows = resp.data or []
    legacy_ids = [r["id"] for r in rows if not r.get("product_id")]

    if legacy_ids:
        supabase.table("campaign_month_weights").delete().in_("id", legacy_ids).execute()

    payload = [
        {
            "campaign_id": campaign_id,
            "month_label": m,
            "weight": float(w),
            # product_id omitted → NULL
        }
        for m, w in weights.items()
        if float(w) >= 0
    ]
    if payload:
        supabase.table("campaign_month_weights").insert(payload).execute()

# ============================================================
# Per-product month weights (NEW, same table, with product_id)
# ============================================================

def fetch_product_month_weights(campaign_id: str) -> Dict[str, Dict[str, float]]:
    """
    Returns:
        {product_id: {month_label: weight, ...}, ...}
    Only rows where product_id IS NOT NULL.
    """
    supabase = get_supabase()
    resp = (
        supabase.table("campaign_month_weights")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    rows = resp.data or []

    out: Dict[str, Dict[str, float]] = {}
    for r in rows:
        pid = r.get("product_id")
        if not pid:
            continue  # skip campaign-level rows
        out.setdefault(pid, {})
        out[pid][r["month_label"]] = float(r.get("weight", 0.0) or 0.0)

    return out


def save_product_month_weights(
    campaign_id: str,
    weights_by_product: Dict[str, Dict[str, float]]
) -> None:
    """
    weights_by_product:
        {product_id: {month_label: weight, ...}, ...}
    All values are interpreted as 'weights' (we'll treat them as percentages).
    """
    supabase = get_supabase()

    for pid, month_dict in weights_by_product.items():
        # Delete existing rows for this campaign + product
        supabase.table("campaign_month_weights") \
            .delete() \
            .eq("campaign_id", campaign_id) \
            .eq("product_id", pid) \
            .execute()

        payload = [
            {
                "campaign_id": campaign_id,
                "product_id": pid,
                "month_label": m,
                "weight": float(w),
            }
            for m, w in month_dict.items()
            if float(w) >= 0
        ]

        if payload:
            supabase.table("campaign_month_weights").insert(payload).execute()


# ============================================================
# Size breakdown (YOUR table: campaign_size_breakdown)
# Stores rows directly by campaign_id + product_id
# ============================================================

def fetch_size_breakdown(campaign_id: str) -> Dict[str, Dict[str, float]]:
    supabase = get_supabase()
    resp = (
        supabase.table("campaign_size_breakdown")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    rows = resp.data or []

    out: Dict[str, Dict[str, float]] = {}
    for r in rows:
        pid = r["product_id"]
        out.setdefault(pid, {})
        out[pid][r["size"]] = float(r.get("qty", 0) or 0)

    return out


def save_size_breakdown(campaign_id: str, size_breakdown: Dict[str, Dict[str, float]]) -> None:
    supabase = get_supabase()

    supabase.table("campaign_size_breakdown").delete().eq("campaign_id", campaign_id).execute()

    payload = []
    for pid, sizes in size_breakdown.items():
        for size, qty in sizes.items():
            if float(qty) <= 0:
                continue
            payload.append({
                "campaign_id": campaign_id,
                "product_id": pid,
                "size": size,
                "qty": float(qty)
            })

    if payload:
        supabase.table("campaign_size_breakdown").insert(payload).execute()

# ============================================================
# Reporting Helpers (Module 6)
# ============================================================

def get_all_campaigns() -> List[Dict[str, Any]]:
    """
    Wrapper to fetch all campaigns in the system.
    Used by the Reporting & Export module.
    """
    return fetch_campaigns()


def get_campaign_full_data(campaign_id: str) -> Dict[str, Any]:
    """
    Return a combined dataset for reporting:
    - campaign info
    - quantities
    - month weights
    - size breakdown
    """
    meta = [c for c in fetch_campaigns() if c["id"] == campaign_id]
    if not meta:
        return {}

    meta = meta[0]

    quantities, cp_row_ids = fetch_campaign_products(campaign_id)
    month_weights = fetch_month_weights(campaign_id)
    size_breakdown = fetch_size_breakdown(campaign_id)

    return {
        "campaign": meta,
        "quantities": quantities,
        "month_weights": month_weights,
        "size_breakdown": size_breakdown
    }
