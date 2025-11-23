# modules/opex_db.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime
from modules.db import get_supabase


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def now_ts() -> str:
    return datetime.utcnow().isoformat()


# -------------------------------------------------
# OPEX master items (global list)
# Table: opex_items
# -------------------------------------------------
def fetch_opex_items(active_only: bool = True) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    q = supabase.table("opex_items").select("*")
    # You don't currently have is_active in table.
    # If you add later, this will still work.
    if active_only:
        try:
            q = q.eq("is_active", True)
        except Exception:
            pass
    resp = q.order("created_at", desc=True).execute()
    return resp.data or []


def insert_opex_item(data: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    data["created_at"] = now_ts()
    data["updated_at"] = now_ts()
    resp = supabase.table("opex_items").insert(data).execute()
    return resp.data[0]


def update_opex_item(opex_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    fields["updated_at"] = now_ts()
    resp = supabase.table("opex_items").update(fields).eq("id", opex_id).execute()
    return resp.data[0]


def delete_opex_item(opex_id: str) -> None:
    supabase = get_supabase()
    supabase.table("opex_items").delete().eq("id", opex_id).execute()


# -------------------------------------------------
# Campaign linkage
# Table: campaign_opex
# -------------------------------------------------
def fetch_campaign_opex_links(campaign_id: str) -> List[str]:
    """Return list of linked opex_ids for a campaign."""
    supabase = get_supabase()
    resp = (
        supabase.table("campaign_opex")
        .select("opex_id")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    rows = resp.data or []
    return [r["opex_id"] for r in rows]


def save_campaign_opex_links(campaign_id: str, opex_ids: List[str]) -> None:
    """
    Safe tiny-data approach:
      - delete existing links
      - insert current selection
    """
    supabase = get_supabase()
    supabase.table("campaign_opex").delete().eq("campaign_id", campaign_id).execute()

    payload = [{"campaign_id": campaign_id, "opex_id": oid} for oid in opex_ids]
    if payload:
        supabase.table("campaign_opex").insert(payload).execute()
