from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import accuracy_score, average_precision_score, log_loss, precision_score, recall_score, roc_auc_score

from app.features import MODEL_CATEGORICAL, canonicalize_orders, load_reference_data, make_features

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
REPORT_DIR = BASE_DIR / "reports"


def metrics(y_true, p):
    pred = p >= 0.5
    return {
        "roc_auc": float(roc_auc_score(y_true, p)),
        "average_precision": float(average_precision_score(y_true, p)),
        "log_loss": float(log_loss(y_true, p)),
        "accuracy_at_0_5": float(accuracy_score(y_true, pred)),
        "precision_at_0_5": float(precision_score(y_true, pred, zero_division=0)),
        "recall_at_0_5": float(recall_score(y_true, pred, zero_division=0)),
    }


def main():
    train = pd.read_csv(DATA_DIR / "train.csv")
    customers, products = load_reference_data(DATA_DIR)
    train = canonicalize_orders(train)
    train["_dt"] = pd.to_datetime(train["order_placed_at"], errors="coerce")
    train = train.sort_values("_dt").reset_index(drop=True)

    cut_index = int(len(train) * 0.8)
    cut = train.loc[cut_index, "_dt"]
    mask = train["_dt"] < cut

    X = make_features(train, customers, products)
    y = train["returned"].astype(int)
    Xtr, Xv = X.loc[mask].copy(), X.loc[~mask].copy()
    ytr, yv = y.loc[mask], y.loc[~mask]

    model = CatBoostClassifier(
        iterations=400,
        depth=5,
        learning_rate=0.03,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=42,
        l2_leaf_reg=8,
        random_strength=1,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(Xtr, ytr, cat_features=MODEL_CATEGORICAL, eval_set=(Xv, yv), early_stopping_rounds=80, verbose=False)
    val_p = model.predict_proba(Xv)[:, 1]

    MODEL_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    model.save_model(MODEL_DIR / "return_risk.cbm")

    report = {
        "train_rows_after_dedup": int(len(train)),
        "duplicate_order_rows_removed": int(pd.read_csv(DATA_DIR / "train.csv").shape[0] - len(train)),
        "train_return_rate": float(y.mean()),
        "validation_start": str(cut),
        "train_rows": int(mask.sum()),
        "validation_rows": int((~mask).sum()),
        "validation_return_rate": float(yv.mean()),
        "best_iteration": int(model.get_best_iteration()),
        "metrics": metrics(yv, val_p),
        "excluded_post_return_fields": ["last_service_event_type", "pickup_scheduled_at"],
        "note": "Validation is time-based; model uses dispatch-known fields only.",
    }
    (REPORT_DIR / "training_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.Series(model.get_feature_importance(), index=X.columns).sort_values(ascending=False).head(20).to_csv(REPORT_DIR / "feature_importance.csv", header=["importance"])
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
