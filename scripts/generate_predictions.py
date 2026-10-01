from __future__ import annotations

from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier, Pool

from app.features import MODEL_CATEGORICAL, load_reference_data, make_features

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = BASE_DIR / "model" / "return_risk.cbm"
OUT_PATH = BASE_DIR / "predictions.csv"


def main():
    test = pd.read_csv(DATA_DIR / "test_unlabelled.csv")
    customers, products = load_reference_data(DATA_DIR)
    X = make_features(test, customers, products)
    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))
    p = model.predict_proba(Pool(X, cat_features=MODEL_CATEGORICAL))[:, 1]
    submission = pd.DataFrame({"order_id": test["order_id"], "score": p})
    submission.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} rows={len(submission)}")


if __name__ == "__main__":
    main()
