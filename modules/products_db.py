# modules/products_db.py
from __future__ import annotations
from typing import List, Dict, Any
from supabase import Client
import datetime
from modules.db import get_supabase


# -------------------------------------------
# Helpers
# -------------------------------------------
def now_ts():
    return datetime.datetime.utcnow().isoformat()


# -------------------------------------------
# CRUD wrappers for Supabase "products"
# -------------------------------------------

def db_fetch_products() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = (
        supabase.table("products")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=False)
        .execute()
    )
    return resp.data or []


def db_insert_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()

    product_data["created_at"] = now_ts()
    product_data["updated_at"] = now_ts()

    resp = supabase.table("products").insert(product_data).execute()
    return resp.data[0]


def db_update_product(product_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()

    updated_data["updated_at"] = now_ts()

    resp = (
        supabase.table("products")
        .update(updated_data)
        .eq("id", product_id)
        .execute()
    )
    return resp.data[0]


def db_delete_product(product_id: str) -> None:
    supabase = get_supabase()
    supabase.table("products").delete().eq("id", product_id).execute()
