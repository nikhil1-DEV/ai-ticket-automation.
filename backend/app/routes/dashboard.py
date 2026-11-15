"""
Dashboard Routes
~~~~~~~~~~~~~~~~

Provides aggregated statistics and recent-ticket views for the
front-end dashboard.

Prefix: ``/api/dashboard``
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.schemas import DashboardStats, TicketResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ────────────────────────────────────────────────────────────────────────
#  GET /stats  —  Aggregated dashboard statistics
# ────────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)) -> dict:
    """Return counts grouped by category, priority, and status,
    average AI confidence, and the 5 most recent tickets."""

    total = db.query(func.count(Ticket.id)).scalar() or 0

    # ── Group-by helpers ────────────────────────────────────────────────
    def _group_counts(column) -> dict[str, int]:
        rows = (
            db.query(column, func.count(Ticket.id))
            .group_by(column)
            .all()
        )
        return {str(label or "unknown"): count for label, count in rows}

    by_category = _group_counts(Ticket.category)
    by_priority = _group_counts(Ticket.priority)
    by_status = _group_counts(Ticket.status)

    # ── Average confidence ──────────────────────────────────────────────
    avg_conf: Optional[float] = (
        db.query(func.avg(Ticket.ai_confidence))
        .filter(Ticket.ai_confidence.isnot(None))
        .scalar()
    )
    if avg_conf is not None:
        avg_conf = round(avg_conf, 3)

    # ── Recent tickets ──────────────────────────────────────────────────
    recent = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_tickets": total,
        "by_category": by_category,
        "by_priority": by_priority,
        "by_status": by_status,
        "avg_confidence": avg_conf,
        "recent_tickets": recent,
    }


# ────────────────────────────────────────────────────────────────────────
#  GET /recent  —  10 most recent tickets
# ────────────────────────────────────────────────────────────────────────

@router.get("/recent", response_model=list[TicketResponse])
def get_recent(db: Session = Depends(get_db)) -> list[Ticket]:
    """Return the 10 most recently created tickets."""
    return (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .limit(10)
        .all()
    )
