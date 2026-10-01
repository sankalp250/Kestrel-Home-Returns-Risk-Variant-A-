from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool

from .features import MODEL_CATEGORICAL, load_reference_data, make_features

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "model" / "return_risk.cbm"

FEATURE_LABELS = {
    "customer_prior_return_rate": "Previous return history",
    "customer_prior_returns": "Previous return count",
    "customer_prior_orders": "Previous order count",
    "payment_mode": "Payment method",
    "promised_delivery_days": "Promised delivery time",
    "shield_member": "Shield membership",
    "sales_channel": "Sales channel",
    "family": "Product family",
    "sku": "Product SKU",
    "model_name": "Product model",
    "discount_pct": "Checkout discount",
    "order_value_inr": "Order value",
    "customer_tenure_days": "Customer tenure",
    "product_age_days": "Product age",
    "delivery_pincode": "Delivery pincode",
    "pincode_prefix": "Delivery area",
    "is_gift": "Gift order",
    "qty": "Quantity",
    "city": "Customer city",
    "state": "Customer state",
    "source": "Order source",
    "note_present": "Delivery note",
    "note_call": "Delivery note instruction",
    "note_security": "Security/guard instruction",
    "note_gate": "Gate instruction",
    "note_leave": "Leave-with instruction",
    "note_weekday": "Weekday delivery instruction",
    "note_address": "Address instruction",
}


class ReturnRiskPredictor:
    def __init__(self, model_path: Path = MODEL_PATH, data_dir: Path | None = None) -> None:
        self.model = CatBoostClassifier()
        self.model.load_model(str(model_path))
        self.data_dir = data_dir or BASE_DIR / "data"
        self.customers, self.products = load_reference_data(self.data_dir)

    def _row_frame(self, order: dict[str, Any]) -> pd.DataFrame:
        return pd.DataFrame([order])

    @staticmethod
    def _format_reason(feature: str, value: Any, shap_value: float) -> str:
        label = FEATURE_LABELS.get(feature, feature.replace("_", " ").title())
        higher_risk = shap_value > 0
        direction = "raised" if higher_risk else "reduced"
        if feature == "customer_prior_return_rate":
            text = f"Previous return rate is {float(value):.0%}."
        elif feature == "customer_prior_returns":
            text = f"Customer has {int(value)} previous return(s)."
        elif feature == "customer_prior_orders":
            text = f"Customer has {int(value)} previous order(s)."
        elif feature == "payment_mode":
            text = f"Payment method is {value}."
        elif feature == "promised_delivery_days":
            text = f"Promised delivery is {int(value)} day(s)."
        elif feature == "discount_pct":
            text = f"Checkout discount is {float(value):.0f}%."
        elif feature == "order_value_inr":
            text = f"Order value is ₹{float(value):,.0f}."
        elif feature == "family":
            text = f"Product family is {value}."
        elif feature == "shield_member":
            text = "Customer is a Kestrel Shield member."
        elif feature in {"sku", "model_name", "city", "state", "sales_channel", "source"}:
            text = f"{label} is {value}."
        elif feature == "customer_tenure_days":
            text = f"Customer account age is about {int(value)} day(s)."
        elif feature == "product_age_days":
            text = f"Product has been on sale for about {int(value)} day(s)."
        elif feature == "is_gift":
            text = f"Gift order flag is {value}."
        elif feature == "qty":
            text = f"Quantity is {int(value)}."
        else:
            text = f"{label} contributed to the risk estimate."
        return f"{text} This {direction} the model's risk estimate."

    def predict(self, order: dict[str, Any]) -> dict[str, Any]:
        features = make_features(self._row_frame(order), self.customers, self.products)
        pool = Pool(features, cat_features=MODEL_CATEGORICAL)
        score = float(self.model.predict_proba(pool)[:, 1][0])
        shap = self.model.get_feature_importance(pool, type="ShapValues")[0][:-1]
        ranked = sorted(zip(features.columns, shap), key=lambda t: abs(float(t[1])), reverse=True)

        reasons: list[str] = []
        seen = set()
        # Prefer positive contributions, then include one meaningful risk-reducing factor if available.
        positive = [(f, v) for f, v in ranked if v > 0]
        negative = [(f, v) for f, v in ranked if v < 0]
        for feature, contribution in positive + negative:
            if feature in seen:
                continue
            value = features.iloc[0][feature]
            # Avoid unhelpful low-information values.
            if feature == "customer_prior_return_rate" and float(value) == 0:
                continue
            if feature == "customer_prior_returns" and int(value) == 0:
                continue
            if feature == "customer_prior_orders" and int(value) == 0:
                continue
            reasons.append(self._format_reason(feature, value, float(contribution)))
            seen.add(feature)
            if len(reasons) >= 3:
                break

        if score >= 0.20:
            band = "HIGH"
            action = "REVIEW_BEFORE_DISPATCH"
        elif score >= 0.12:
            band = "MEDIUM"
            action = "CONFIRM_BEFORE_DISPATCH"
        else:
            band = "LOW"
            action = "STANDARD_DISPATCH"

        return {
            "order_id": order.get("order_id"),
            "score": round(score, 6),
            "risk_band": band,
            "recommended_action": action,
            "reasons": reasons or ["No strong individual factor dominated the model estimate."],
        }


if __name__ == "__main__":
    print(json.dumps({"status": "predictor module ready"}))
