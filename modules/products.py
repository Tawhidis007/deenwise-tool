# modules/products.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import pandas as pd
import uuid

from modules.products_db import (
    db_fetch_products,
    db_insert_product,
    db_update_product,
    db_delete_product,
)


# -------------------------------------------------------------
# Dataclass - MUST MATCH SUPABASE TABLE
# -------------------------------------------------------------
@dataclass
class Product:
    id: str
    product_code: Optional[str]
    name: str
    category: str

    price_bdt: float
    manufacturing_cost_bdt: float
    packaging_cost_bdt: float
    shipping_cost_bdt: float
    marketing_cost_bdt: float

    return_rate: float
    discount_rate: float
    vat_included: bool = True
    notes: str = ""

    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# -------------------------------------------------------------
# Load products (from Supabase)
# -------------------------------------------------------------
def load_products() -> List[Product]:
    rows = db_fetch_products()

    products = []
    for row in rows:
        # Safety: ensure missing optional fields don't break
        if "product_code" not in row:
            row["product_code"] = None
        if "created_at" not in row:
            row["created_at"] = None
        if "updated_at" not in row:
            row["updated_at"] = None

        products.append(Product(**row))

    return products


# -------------------------------------------------------------
# Save / Update / Delete
# -------------------------------------------------------------
def add_product(products: List[Product], data: Dict[str, Any]) -> List[Product]:
    # Auto-generate product_code
    if not data.get("product_code"):
        data["product_code"] = (
            data["name"].upper().replace(" ", "-") + "-" + uuid.uuid4().hex[:4]
        )

    new_row = db_insert_product(data)
    products.append(Product(**new_row))
    return products


def update_product(products: List[Product], product_id: str, updated_data: Dict[str, Any]):
    updated_row = db_update_product(product_id, updated_data)

    new_list = []
    for p in products:
        if p.id == product_id:
            new_list.append(Product(**updated_row))
        else:
            new_list.append(p)

    return new_list


def delete_product(products: List[Product], product_id: str):
    db_delete_product(product_id)
    return [p for p in products if p.id != product_id]


# -------------------------------------------------------------
# Validation
# -------------------------------------------------------------
def validate_product_dict(d: Dict[str, Any]) -> List[str]:
    errors = []
    required = ["name", "category", "price_bdt", "manufacturing_cost_bdt"]

    for r in required:
        if r not in d or d[r] in ("", None):
            errors.append(f"Missing required field: {r}")

    numeric_fields = [
        "price_bdt", "manufacturing_cost_bdt", "packaging_cost_bdt",
        "shipping_cost_bdt", "marketing_cost_bdt",
        "return_rate", "discount_rate"
    ]
    for nf in numeric_fields:
        v = float(d.get(nf, 0) or 0)
        if v < 0:
            errors.append(f"{nf} cannot be negative")

    # Rates must be 0–1
    for rf in ["return_rate", "discount_rate"]:
        v = float(d.get(rf, 0) or 0)
        if not (0 <= v <= 1):
            errors.append(f"{rf} must be between 0 and 1")

    return errors


# -------------------------------------------------------------
# Calculations (unchanged)
# -------------------------------------------------------------
def effective_price(p: Product) -> float:
    after_discount = p.price_bdt * (1 - p.discount_rate)
    realized = after_discount * (1 - p.return_rate)
    return realized


def total_unit_cost(p: Product) -> float:
    return (
        p.manufacturing_cost_bdt +
        p.packaging_cost_bdt +
        p.shipping_cost_bdt +
        p.marketing_cost_bdt
    )


def unit_gross_profit(p: Product) -> float:
    return p.price_bdt - p.manufacturing_cost_bdt


def unit_net_profit(p: Product) -> float:
    return effective_price(p) - total_unit_cost(p)


def gross_margin_pct(p: Product) -> float:
    denom = p.price_bdt if p.price_bdt else 1
    return unit_gross_profit(p) / denom


def net_margin_pct(p: Product) -> float:
    denom = effective_price(p) if effective_price(p) else 1
    return unit_net_profit(p) / denom


# -------------------------------------------------------------
# DataFrame for modules
# -------------------------------------------------------------
def products_to_dataframe(products: List[Product]) -> pd.DataFrame:
    rows = []
    for p in products:
        ep = effective_price(p)
        tuc = total_unit_cost(p)
        ugp = unit_gross_profit(p)
        unp = unit_net_profit(p)

        rows.append({
            "id": p.id,
            "product_code": p.product_code,
            "name": p.name,
            "category": p.category,

            "price_bdt": p.price_bdt,
            "manufacturing_cost_bdt": p.manufacturing_cost_bdt,
            "packaging_cost_bdt": p.packaging_cost_bdt,
            "shipping_cost_bdt": p.shipping_cost_bdt,
            "marketing_cost_bdt": p.marketing_cost_bdt,

            "return_rate_%": p.return_rate * 100,
            "discount_rate_%": p.discount_rate * 100,
            "vat_included": p.vat_included,

            "effective_price": ep,
            "total_unit_cost": tuc,
            "unit_gross_profit": ugp,
            "unit_net_profit": unp,
            "gross_margin_%": gross_margin_pct(p) * 100,
            "net_margin_%": net_margin_pct(p) * 100,

            "notes": p.notes,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        })

    return pd.DataFrame(rows)
