import os
import sqlite3

from fastapi import APIRouter

from api.models import HealthResponse

router = APIRouter()

DB_PATH = "loterias.db"


@router.get("/api/health", response_model=HealthResponse)
def health():
    db_exists = os.path.isfile(DB_PATH)
    tables: list[str] = []

    if db_exists:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception:
            pass

    return HealthResponse(
        status="ok" if db_exists else "degraded",
        db_exists=db_exists,
        db_tables=tables,
    )
