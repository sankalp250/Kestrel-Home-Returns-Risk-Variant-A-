import pandas as pd


def test_submission_shape():
    pred = pd.read_csv("predictions.csv")
    test = pd.read_csv("data/test_unlabelled.csv")
    assert list(pred.columns) == ["order_id", "score"]
    assert len(pred) == len(test)
    assert pred.order_id.nunique() == len(pred)
    assert pred.score.notna().all()
    assert pred.score.between(0, 1).all()
