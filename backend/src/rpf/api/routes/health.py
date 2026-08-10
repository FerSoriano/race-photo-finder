from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from rpf.api.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: DbSession) -> dict[str, str]:
    """Readiness probe: fails loudly if the database is unreachable."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
