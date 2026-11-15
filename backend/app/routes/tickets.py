"""
Ticket Routes
~~~~~~~~~~~~~

CRUD operations for support tickets, including AI-powered analysis
and automatic team routing on creation.

Prefix: ``/api/tickets``
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Ticket
from app.schemas import (
    AIAnalysisResult,
    AuditLogResponse,
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services.ai_service import ai_service
from app.services.routing_service import routing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

# ── Valid enum values (for input validation) ────────────────────────────

_VALID_STATUSES = {
    "new", "processing", "assigned", "in_progress",
    "pending_approval", "resolved", "closed",
}
_VALID_CATEGORIES = {
    "billing", "technical", "account", "general", "bug_report", "feature_request",
}
_VALID_PRIORITIES = {"critical", "high", "medium", "low"}
_VALID_SOURCES = {"web_form", "email", "api", "webhook"}


# ────────────────────────────────────────────────────────────────────────
#  Helper: record an audit-log entry
# ────────────────────────────────────────────────────────────────────────

def _audit(db: Session, ticket_id: int, action: str, details: str) -> None:
    """Write an immutable audit-log row."""
    entry = AuditLog(ticket_id=ticket_id, action=action, details=details)
    db.add(entry)
    # Flush (but don't commit) so the entry gets an id immediately.
    db.flush()


# ────────────────────────────────────────────────────────────────────────
#  POST /  —  Create a new ticket
# ────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=TicketResponse, status_code=201)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> Ticket:
    """Create a ticket, run AI analysis, route to a team, and log everything.

    **Flow:**
    1. Validate and persist the ticket.
    2. Run AI analysis (classify, summarise, draft response).
    3. Route the ticket to the appropriate team.
    4. Update status to ``"processing"`` → ``"assigned"``.
    5. Record audit-log entries for each step.
    """
    # Validate source
    source = (payload.source or "web_form").lower()
    if source not in _VALID_SOURCES:
        raise HTTPException(status_code=400, detail=f"Invalid source '{source}'. Must be one of {_VALID_SOURCES}.")

    # 1️⃣  Persist the ticket
    ticket = Ticket(
        subject=payload.subject,
        description=payload.description,
        sender_name=payload.sender_name,
        sender_email=payload.sender_email,
        source=source,
        status="new",
    )
    db.add(ticket)
    db.flush()  # get ticket.id
    logger.info("Ticket #%d created (subject: %s).", ticket.id, ticket.subject)
    _audit(db, ticket.id, "created", f"Ticket created via {source}.")

    # 2️⃣  AI analysis
    try:
        analysis: AIAnalysisResult = ai_service.analyze_ticket(
            subject=payload.subject,
            description=payload.description,
        )
        ticket.category = analysis.category
        ticket.priority = analysis.priority
        ticket.ai_summary = analysis.summary
        ticket.ai_draft_response = analysis.draft_response
        ticket.ai_confidence = analysis.confidence
        ticket.status = "processing"

        _audit(
            db, ticket.id, "categorized",
            f"AI classified as category={analysis.category}, "
            f"priority={analysis.priority}, confidence={analysis.confidence:.2f}.",
        )
        _audit(db, ticket.id, "response_drafted", "AI drafted a customer response.")
    except Exception as exc:
        logger.error("AI analysis failed for ticket #%d: %s", ticket.id, exc)
        # Ticket remains with status="new" and no AI fields.  Not fatal.
        _audit(db, ticket.id, "categorized", f"AI analysis failed: {exc}")

    # 3️⃣  Route to a team
    if ticket.category and ticket.priority:
        team = routing_service.route_ticket(ticket.category, ticket.priority)
        ticket.assigned_team = team
        ticket.status = "assigned"
        _audit(db, ticket.id, "routed", f"Assigned to '{team}'.")

    db.commit()
    db.refresh(ticket)
    return ticket


# ────────────────────────────────────────────────────────────────────────
#  GET /  —  List tickets (with optional filters & pagination)
# ────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=TicketListResponse)
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> dict:
    """Return a paginated list of tickets with optional filters."""
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)

    total = query.count()
    tickets = (
        query.order_by(Ticket.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {"tickets": tickets, "total": total}


# ────────────────────────────────────────────────────────────────────────
#  GET /{ticket_id}  —  Single ticket detail
# ────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    """Retrieve a single ticket by its ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found.")
    return ticket


# ────────────────────────────────────────────────────────────────────────
#  PATCH /{ticket_id}  —  Update ticket
# ────────────────────────────────────────────────────────────────────────

@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
) -> Ticket:
    """Partially update a ticket's status, assignment, or priority."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found.")

    changes: list[str] = []

    if payload.status is not None:
        if payload.status not in _VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{payload.status}'. Must be one of {_VALID_STATUSES}.",
            )
        old = ticket.status
        ticket.status = payload.status
        changes.append(f"status: {old} → {payload.status}")

    if payload.assigned_team is not None:
        old = ticket.assigned_team
        ticket.assigned_team = payload.assigned_team
        changes.append(f"assigned_team: {old} → {payload.assigned_team}")

    if payload.priority is not None:
        if payload.priority not in _VALID_PRIORITIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority '{payload.priority}'. Must be one of {_VALID_PRIORITIES}.",
            )
        old = ticket.priority
        ticket.priority = payload.priority
        changes.append(f"priority: {old} → {payload.priority}")

    if changes:
        _audit(db, ticket.id, "status_changed", "; ".join(changes))

    db.commit()
    db.refresh(ticket)
    return ticket


# ────────────────────────────────────────────────────────────────────────
#  GET /{ticket_id}/audit  —  Audit trail
# ────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}/audit", response_model=list[AuditLogResponse])
def get_ticket_audit(ticket_id: int, db: Session = Depends(get_db)) -> list[AuditLog]:
    """Return the full audit trail for a specific ticket."""
    # Verify the ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found.")

    return (
        db.query(AuditLog)
        .filter(AuditLog.ticket_id == ticket_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )


# ────────────────────────────────────────────────────────────────────────
#  POST /{ticket_id}/reanalyze  —  Re-run AI analysis
# ────────────────────────────────────────────────────────────────────────

@router.post("/{ticket_id}/reanalyze", response_model=TicketResponse)
def reanalyze_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    """Re-run AI analysis on an existing ticket and update its fields."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found.")

    try:
        analysis = ai_service.analyze_ticket(
            subject=ticket.subject,
            description=ticket.description,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI re-analysis failed: {exc}",
        ) from exc

    ticket.category = analysis.category
    ticket.priority = analysis.priority
    ticket.ai_summary = analysis.summary
    ticket.ai_draft_response = analysis.draft_response
    ticket.ai_confidence = analysis.confidence

    # Re-route based on new classification
    team = routing_service.route_ticket(analysis.category, analysis.priority)
    ticket.assigned_team = team

    _audit(
        db, ticket.id, "categorized",
        f"Re-analysed: category={analysis.category}, priority={analysis.priority}, "
        f"confidence={analysis.confidence:.2f}. Routed to '{team}'.",
    )

    db.commit()
    db.refresh(ticket)
    return ticket
