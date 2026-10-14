"""
Health check route.

Purpose:
  Gives a single endpoint to verify that:
  1. The API is running.
  2. The database can be reached.
  3. The config is loaded correctly.

This is the first thing you test after starting the server.
It's also what Docker and deployment platforms use for liveness checks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from app.database.session import get_db
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """
    Returns the status of the API and its dependencies.
    A 200 response means the server is live and the DB is reachable.
    """
    # Attempt a trivial DB query to confirm connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
    }
