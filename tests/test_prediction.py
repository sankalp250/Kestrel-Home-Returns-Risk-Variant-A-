import pandas as pd
from app.predictor import ReturnRiskPredictor


def test_predictor_output():
    row = pd.read_csv("data/test_unlabelled.csv").iloc[0].where(lambda s: s.notna(), None).to_dict()
    p = ReturnRiskPredictor()
    out = p.predict(row)
    assert 0 <= out["score"] <= 1
    assert out["risk_band"] in {"LOW", "MEDIUM", "HIGH"}
    assert out["recommended_action"] in {"STANDARD_DISPATCH", "CONFIRM_BEFORE_DISPATCH", "REVIEW_BEFORE_DISPATCH"}
    assert len(out["reasons"]) >= 1
