from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "kestrel_predictions.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                score REAL NOT NULL,
                risk_band TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def log_prediction(prediction: dict) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO prediction_log
            (order_id, score, risk_band, recommended_action, reasons_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                prediction["order_id"],
                prediction["score"],
                prediction["risk_band"],
                prediction["recommended_action"],
                json.dumps(prediction["reasons"]),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def get_recent_predictions(limit: int = 10) -> list[dict]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT order_id, score, risk_band, recommended_action, reasons_json, created_at
            FROM prediction_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "order_id": r["order_id"],
                "score": r["score"],
                "risk_band": r["risk_band"],
                "recommended_action": r["recommended_action"],
                "reasons": json.loads(r["reasons_json"]),
                "created_at": r["created_at"],
            })
        return result


def get_prediction_stats() -> dict:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT
                count(*) as total,
                avg(score) as avg_score,
                sum(case when risk_band = 'LOW' then 1 else 0 end) as low_count,
                sum(case when risk_band = 'MEDIUM' then 1 else 0 end) as medium_count,
                sum(case when risk_band = 'HIGH' then 1 else 0 end) as high_count
            FROM prediction_log
            """
        )
        r = cursor.fetchone()
        total = r["total"] if r and r["total"] else 0
        return {
            "total_checks": total,
            "avg_score": round(r["avg_score"], 4) if total > 0 and r["avg_score"] is not None else 0.0,
            "low_count": r["low_count"] if total > 0 and r["low_count"] is not None else 0,
            "medium_count": r["medium_count"] if total > 0 and r["medium_count"] is not None else 0,
            "high_count": r["high_count"] if total > 0 and r["high_count"] is not None else 0,
        }
