from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import get_prediction_stats, get_recent_predictions, init_db, log_prediction
from .predictor import ReturnRiskPredictor
from .schemas import OrderRecord, PredictionResponse

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "app" / "static"
DATA_DIR = BASE_DIR / "data"

predictor: ReturnRiskPredictor | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global predictor
    required = [DATA_DIR / "customers.csv", DATA_DIR / "products.csv", BASE_DIR / "model" / "return_risk.cbm"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Missing required local assets: " + ", ".join(missing))
    predictor = ReturnRiskPredictor(data_dir=DATA_DIR)
    init_db()
    yield


app = FastAPI(title="Kestrel Returns Risk", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=FileResponse)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/example")
def example_order(index: int = 0) -> dict:
    path = DATA_DIR / "test_unlabelled.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="test_unlabelled.csv is not available")
    df = pd.read_csv(path)
    idx = index % len(df)
    row = df.iloc[idx].where(lambda s: s.notna(), None).to_dict()
    return row


@app.get("/api/presets")
def order_presets() -> list[dict]:
    return [
        {
            "id": "low_risk",
            "name": "Low Risk (Prepaid · Repeat Customer)",
            "description": "Prepaid UPI payment, 3 past orders with 0 returns, fast 2-day delivery.",
            "data": {
                "order_id": "KO269001",
                "order_placed_at": "2026-08-10 14:22",
                "customer_id": "CUST_1042",
                "sku": "SKU_BLENDER_PRO",
                "sales_channel": "app",
                "payment_mode": "prepaid_upi",
                "discount_pct": 5.0,
                "qty": 1,
                "order_value_inr": 4200.0,
                "promised_delivery_days": 2,
                "delivery_pincode": 560034,
                "is_gift": "N",
                "customer_prior_orders": 3,
                "customer_prior_returns": 0,
                "delivery_note": "Ring bell twice, leave with security if away",
                "source": "crm",
            },
        },
        {
            "id": "medium_risk",
            "name": "Medium Risk (Shield Member · Confirmation Target)",
            "description": "Shield customer, 4 orders with 1 return, 4-day delivery window. Predicted at ~17.8%, perfectly matching the confirmation call threshold.",
            "data": {
                "order_id": "KO269002",
                "order_placed_at": "2026-08-12 18:45",
                "customer_id": "CUST_2891",
                "sku": "SKU_AIRFRY_MAX",
                "sales_channel": "web",
                "payment_mode": "cod",
                "discount_pct": 20.0,
                "qty": 1,
                "order_value_inr": 8900.0,
                "promised_delivery_days": 4,
                "delivery_pincode": 400050,
                "is_gift": "N",
                "customer_prior_orders": 4,
                "customer_prior_returns": 1,
                "delivery_note": "Call before delivery between 4pm-7pm",
                "source": "crm",
            },
        },
        {
            "id": "high_risk",
            "name": "High Risk (Cash On Delivery · Past Returns)",
            "description": "COD payment, marketplace channel, 6-day transit window, customer had 2 prior returns.",
            "data": {
                "order_id": "KO269003",
                "order_placed_at": "2026-08-14 22:15",
                "customer_id": "CUST_4412",
                "sku": "SKU_ROBOT_VAC",
                "sales_channel": "marketplace",
                "payment_mode": "cod",
                "discount_pct": 30.0,
                "qty": 1,
                "order_value_inr": 18500.0,
                "promised_delivery_days": 6,
                "delivery_pincode": 110001,
                "is_gift": "N",
                "customer_prior_orders": 2,
                "customer_prior_returns": 2,
                "delivery_note": "Call before coming, ensure bill copy attached",
                "source": "partner_feed",
            },
        },
    ]


@app.get("/api/history")
def prediction_history(limit: int = 8) -> list[dict]:
    return get_recent_predictions(limit=limit)


@app.get("/api/stats")
def prediction_stats() -> dict:
    return get_prediction_stats()


@app.post("/api/predict", response_model=PredictionResponse)
def predict(order: OrderRecord) -> PredictionResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor is not loaded")
    result = predictor.predict(order.model_dump())
    log_prediction(result)
    return result
