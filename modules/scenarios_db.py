# modules/scenarios_db.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime
from modules.db import get_supabase


def now_ts() -> str:
    return datetime.utcnow().isoformat()


# ============================================================
# SCENARIOS (High-level CRUD)
# ============================================================

def fetch_scenarios() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.table("scenarios").select("*").order("created_at", desc=True).execute()
    return resp.data or []


def create_scenario(
    name: str,
    description: str = "",
    base_campaign_id: Optional[str] = None
) -> Dict[str, Any]:
    supabase = get_supabase()
    payload = {
        "name": name,
        "description": description,
        "base_campaign_id": base_campaign_id,
        "created_at": now_ts(),
        "updated_at": now_ts()
    }
    resp = supabase.table("scenarios").insert(payload).execute()
    return resp.data[0]


def update_scenario(scenario_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    fields["updated_at"] = now_ts()
    resp = supabase.table("scenarios").update(fields).eq("id", scenario_id).execute()
    return resp.data[0]


def delete_scenario(scenario_id: str) -> None:
    supabase = get_supabase()
    # cascades will delete scenario_products / scenario_opex / scenario_fx / scenario_campaign_links
    supabase.table("scenarios").delete().eq("id", scenario_id).execute()


def duplicate_scenario(scenario_id: str, new_name: str) -> Dict[str, Any]:
    """
    Creates a copy of scenario + its overrides.
    """
    supabase = get_supabase()

    # Load base scenario
    s_resp = supabase.table("scenarios").select("*").eq("id", scenario_id).execute()
    if not s_resp.data:
        raise ValueError("Scenario not found")

    base = s_resp.data[0]
    new_s = create_scenario(
        name=new_name,
        description=base.get("description", ""),
        base_campaign_id=base.get("base_campaign_id")
    )

    new_id = new_s["id"]

    # Copy product overrides
    prods = fetch_scenario_products(scenario_id)
    if prods:
        for p in prods:
            p["scenario_id"] = new_id
            p.pop("id", None)
        supabase.table("scenario_products").insert(prods).execute()

    # Copy opex overrides
    opex = fetch_scenario_opex(scenario_id)
    if opex:
        for o in opex:
            o["scenario_id"] = new_id
            o.pop("id", None)
        supabase.table("scenario_opex").insert(opex).execute()

    # Copy FX overrides
    fx = fetch_scenario_fx(scenario_id)
    if fx:
        for f in fx:
            f["scenario_id"] = new_id
            f.pop("id", None)
        supabase.table("scenario_fx").insert(fx).execute()

    # Copy campaign links
    links = fetch_scenario_campaign_links(scenario_id)
    if links:
        for l in links:
            l["scenario_id"] = new_id
            l.pop("id", None)
        supabase.table("scenario_campaign_links").insert(links).execute()

    return new_s


# ============================================================
# SCENARIO CAMPAIGN LINKS
# ============================================================

def fetch_scenario_campaign_links(scenario_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.table("scenario_campaign_links").select("*").eq("scenario_id", scenario_id).execute()
    return resp.data or []


def link_scenario_to_campaign(scenario_id: str, campaign_id: str) -> None:
    supabase = get_supabase()
    # keep 1 active link per scenario → delete old, insert new
    supabase.table("scenario_campaign_links").delete().eq("scenario_id", scenario_id).execute()
    payload = {"scenario_id": scenario_id, "campaign_id": campaign_id}
    supabase.table("scenario_campaign_links").insert(payload).execute()


# ============================================================
# SCENARIO PRODUCT OVERRIDES
# ============================================================

def fetch_scenario_products(scenario_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.table("scenario_products").select("*").eq("scenario_id", scenario_id).execute()
    return resp.data or []


def save_scenario_products(
    scenario_id: str,
    rows: List[Dict[str, Any]]
) -> None:
    """
    overwrite all product overrides for that scenario.
    """
    supabase = get_supabase()
    supabase.table("scenario_products").delete().eq("scenario_id", scenario_id).execute()

    payload = []
    for r in rows:
        payload.append({
            "scenario_id": scenario_id,
            "product_id": r["product_id"],
            "price_override": r.get("price_override"),
            "discount_override": r.get("discount_override"),
            "return_rate_override": r.get("return_rate_override"),
            "cost_override": r.get("cost_override"),
            "qty_override": r.get("qty_override"),
            "created_at": now_ts(),
            "updated_at": now_ts()
        })

    if payload:
        supabase.table("scenario_products").insert(payload).execute()


# ============================================================
# SCENARIO OPEX OVERRIDES
# ============================================================

def fetch_scenario_opex(scenario_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.table("scenario_opex").select("*").eq("scenario_id", scenario_id).execute()
    return resp.data or []


def save_scenario_opex(scenario_id: str, rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.table("scenario_opex").delete().eq("scenario_id", scenario_id).execute()

    payload = []
    for r in rows:
        payload.append({
            "scenario_id": scenario_id,
            "opex_item_id": r["opex_item_id"],
            "cost_override": r.get("cost_override"),
            "created_at": now_ts(),
            "updated_at": now_ts()
        })

    if payload:
        supabase.table("scenario_opex").insert(payload).execute()


# ============================================================
# SCENARIO FX OVERRIDES
# ============================================================

def fetch_scenario_fx(scenario_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.table("scenario_fx").select("*").eq("scenario_id", scenario_id).execute()
    return resp.data or []


def save_scenario_fx(scenario_id: str, rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.table("scenario_fx").delete().eq("scenario_id", scenario_id).execute()

    payload = []
    for r in rows:
        payload.append({
            "scenario_id": scenario_id,
            "currency": r["currency"],
            "rate": float(r["rate"]),
            "created_at": now_ts(),
            "updated_at": now_ts()
        })

    if payload:
        supabase.table("scenario_fx").insert(payload).execute()
