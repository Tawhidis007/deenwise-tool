# modules/opex.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import date
import pandas as pd

from modules.revenue import month_range, month_label_to_nice


# -------------------------------------------------
# Dataclass to keep logic clean
# -------------------------------------------------
@dataclass
class OpexItem:
    id: str
    name: str
    category: str
    cost_bdt: float
    start_month: str              # 'YYYY-MM'
    end_month: Optional[str]      # 'YYYY-MM' or None
    is_one_time: bool
    notes: str = ""


# -------------------------------------------------
# Convert DB rows to objects
# -------------------------------------------------
def rows_to_opex_items(rows: List[Dict[str, Any]]) -> List[OpexItem]:
    items = []
    for r in rows:
        items.append(
            OpexItem(
                id=r["id"],
                name=r["name"],
                category=r["category"],
                cost_bdt=float(r["cost_bdt"]),
                start_month=r["start_month"],
                end_month=r.get("end_month"),
                is_one_time=bool(r.get("is_one_time", False)),
                notes=r.get("notes", "") or ""
            )
        )
    return items


# -------------------------------------------------
# Core monthly expansion
# -------------------------------------------------
def expand_opex_for_campaign(
    campaign_start: date,
    campaign_end: date,
    opex_items: List[OpexItem]
) -> pd.DataFrame:
    """
    Returns monthly OPEX expanded across the campaign months.
    All values are BDT.
    """
    camp_months = month_range(campaign_start, campaign_end)
    if not camp_months:
        return pd.DataFrame()

    rows = []
    for item in opex_items:
        # Determine which months this item applies to
        start_m = item.start_month
        end_m = item.end_month or "9999-12"

        for m in camp_months:
            if not (start_m <= m <= end_m):
                continue

            if item.is_one_time:
                # one-time costs apply ONLY at their start_month
                if m != start_m:
                    continue

            rows.append({
                "month": m,
                "month_nice": month_label_to_nice(m),
                "opex_id": item.id,
                "name": item.name,
                "category": item.category,
                "cost_bdt": item.cost_bdt,
                "is_one_time": item.is_one_time,
                "notes": item.notes
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # aggregate per month for quick charts
    df["cost_bdt"] = df["cost_bdt"].astype(float)
    return df


def opex_month_table(opex_df: pd.DataFrame) -> pd.DataFrame:
    if opex_df.empty:
        return pd.DataFrame(columns=["month", "month_nice", "opex_cost_bdt"])

    return (
        opex_df.groupby(["month", "month_nice"], as_index=False)
        .agg(opex_cost_bdt=("cost_bdt", "sum"))
        .sort_values("month")
    )
