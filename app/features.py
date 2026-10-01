from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

MODEL_CATEGORICAL = [
    "customer_id", "sku", "model_name", "sales_channel", "payment_mode",
    "is_gift", "source", "shield_member", "state", "city", "family", "pincode_prefix",
]

MODEL_FEATURES = [
    "customer_id", "sku", "model_name", "sales_channel", "payment_mode", "is_gift", "source",
    "shield_member", "state", "city", "family", "warranty_months",
    "discount_pct", "qty", "order_value_inr", "promised_delivery_days", "delivery_pincode",
    "customer_prior_orders", "customer_prior_returns", "customer_prior_return_rate",
    "customer_no_history", "customer_tenure_days", "product_age_days", "order_hour", "order_dow",
    "order_month", "is_weekend", "is_missing_pincode", "pincode_prefix", "discount_value_inr",
    "basket_vs_list_ratio", "note_len", "note_present", "note_security", "note_gate", "note_call",
    "note_weekday", "note_leave", "note_address",
]


def load_reference_data(data_dir: Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(data_dir / "customers.csv")
    products = pd.read_csv(data_dir / "products.csv")
    return customers, products


def canonicalize_orders(train: pd.DataFrame) -> pd.DataFrame:
    """Collapse partner-feed re-imports, preferring the CRM representation."""
    if "source" not in train.columns or "order_id" not in train.columns:
        return train.copy()
    out = train.assign(_source_rank=(train["source"] != "crm").astype(int))
    out = out.sort_values(["order_id", "_source_rank"])
    return out.drop_duplicates("order_id", keep="first").drop(columns="_source_rank").reset_index(drop=True)


def _normalize_strings(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = out[col].fillna("MISSING").astype(str)
    return out


def make_features(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Create only features available at dispatch. Post-return fields are intentionally ignored."""
    x = orders.copy()
    x["order_dt"] = pd.to_datetime(x["order_placed_at"], errors="coerce")
    x = x.merge(customers, on="customer_id", how="left", validate="many_to_one")
    x = x.merge(products, on="sku", how="left", validate="many_to_one")
    x["signup_dt"] = pd.to_datetime(x["signup_date"], errors="coerce")
    x["launch_dt"] = pd.to_datetime(x["launch_date"], errors="coerce")

    x["customer_tenure_days"] = (x["order_dt"] - x["signup_dt"]).dt.days.clip(lower=0).fillna(0)
    x["product_age_days"] = (x["order_dt"] - x["launch_dt"]).dt.days.clip(lower=0).fillna(0)
    x["customer_prior_return_rate"] = np.where(
        x["customer_prior_orders"] > 0,
        x["customer_prior_returns"] / x["customer_prior_orders"],
        0.0,
    )
    x["customer_no_history"] = (x["customer_prior_orders"] == 0).astype(int)
    x["order_hour"] = x["order_dt"].dt.hour.fillna(0).astype(int)
    x["order_dow"] = x["order_dt"].dt.dayofweek.fillna(0).astype(int)
    x["order_month"] = x["order_dt"].dt.month.fillna(0).astype(int)
    x["is_weekend"] = (x["order_dow"] >= 5).astype(int)
    x["is_missing_pincode"] = (x["delivery_pincode"] == 0).astype(int)
    x["pincode_prefix"] = x["delivery_pincode"].fillna(0).astype(int).astype(str).str.zfill(6).str[:3]
    x["discount_value_inr"] = x["list_price_inr"] * x["qty"] * x["discount_pct"] / 100.0
    x["basket_vs_list_ratio"] = np.where(
        x["list_price_inr"] * x["qty"] > 0,
        x["order_value_inr"] / (x["list_price_inr"] * x["qty"]),
        0.0,
    )

    note = x["delivery_note"].fillna("").astype(str).str.lower()
    x["note_len"] = note.str.len()
    x["note_present"] = (x["note_len"] > 0).astype(int)
    patterns = {
        "note_security": r"security|guard",
        "note_gate": r"gate code|gate",
        "note_call": r"call before",
        "note_weekday": r"weekday|monday|tuesday|wednesday|thursday|friday",
        "note_leave": r"leave with|leave at|keep with",
        "note_address": r"address|flat|apartment|office|home",
    }
    for col, pattern in patterns.items():
        x[col] = note.str.contains(pattern, regex=True, na=False).astype(int)

    # Explicitly exclude last_service_event_type and pickup_scheduled_at: they may be created during the return process.
    x = _normalize_strings(x, MODEL_CATEGORICAL)
    for col in MODEL_FEATURES:
        if col not in x:
            x[col] = 0

    return x[MODEL_FEATURES].copy()
