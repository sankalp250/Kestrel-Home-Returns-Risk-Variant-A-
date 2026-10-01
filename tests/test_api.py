from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_example_endpoint():
    with TestClient(app) as client:
        r = client.get("/api/example")
        assert r.status_code == 200
        assert "order_id" in r.json()


def test_predict_endpoint():
    with TestClient(app) as client:
        row = client.get("/api/example").json()
        for k in ("pickup_scheduled_at", "last_service_event_type"):
            row[k] = None
        r = client.post("/api/predict", json=row)
        assert r.status_code == 200
        data = r.json()
        assert 0 <= data["score"] <= 1
        assert data["reasons"]


def test_presets_and_history_endpoints():
    with TestClient(app) as client:
        r_presets = client.get("/api/presets")
        assert r_presets.status_code == 200
        presets = r_presets.json()
        assert len(presets) >= 3

        r_history = client.get("/api/history")
        assert r_history.status_code == 200
        assert isinstance(r_history.json(), list)

        r_stats = client.get("/api/stats")
        assert r_stats.status_code == 200
        assert "total_checks" in r_stats.json()
