import pandas as pd
from app.features import load_reference_data, make_features


def test_dispatch_features_exclude_post_return_fields():
    orders = pd.read_csv("data/test_unlabelled.csv").head(1)
    customers, products = load_reference_data()
    x = make_features(orders, customers, products)
    assert "last_service_event_type" not in x.columns
    assert "pickup_scheduled_at" not in x.columns
    assert len(x) == 1


def test_feature_shape_and_known_types():
    orders = pd.read_csv("data/test_unlabelled.csv").head(3)
    customers, products = load_reference_data()
    x = make_features(orders, customers, products)
    assert x.shape[0] == 3
    assert x["customer_prior_return_rate"].between(0, 1).all()
