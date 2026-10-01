from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def main():
    test = pd.read_csv(DATA_DIR / "test_unlabelled.csv")
    sample = pd.read_csv(DATA_DIR / "sample_submission.csv")
    pred = pd.read_csv(BASE_DIR / "predictions.csv")
    assert list(pred.columns) == list(sample.columns) == ["order_id", "score"]
    assert len(pred) == len(test) == len(sample)
    assert pred["order_id"].nunique() == len(pred)
    assert pred["score"].notna().all()
    assert ((pred["score"] >= 0) & (pred["score"] <= 1)).all()
    assert pred["order_id"].tolist() == test["order_id"].tolist()
    print("submission validation: PASS")


if __name__ == "__main__":
    main()
