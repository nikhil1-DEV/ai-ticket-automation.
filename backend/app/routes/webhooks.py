"""
Webhook Routes
~~~~~~~~~~~~~~

Handles **incoming** webhooks (e.g. from an email gateway or integration
platform like Boomi) and provides a **test** endpoint to verify
outgoing webhook delivery.

Prefix: ``/api/webhooks``
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AuditLog, Ticket
from app.schemas import TicketResponse, WebhookPayload
from app.services.ai_service import ai_service
from app.services.notification_service import notification_service
from app.services.routing_service import routing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


# ────────────────────────────────────────────────────────────────────────
#  POST /incoming  —  Receive an external webhook and create a ticket
# ────────────────────────────────────────────────────────────────────────

@router.post("/incoming", response_model=TicketResponse, status_code=201)
def incoming_webhook(payload: WebhookPayload, db: Session = Depends(get_db)) -> Ticket:
    """Receive an inbound webhook and create a ticket from its data.

    Expected ``data`` fields::

        {
            "subject": "...",
            "description": "...",
            "sender_name": "...",   // optional
            "sender_email": "..."   // optional
        }
    """
    data = payload.data

    subject = data.get("subject")
    description = data.get("description")

    if not subject or not description:
        raise HTTPException(
            status_code=400,
            detail="Webhook data must include 'subject' and 'description'.",
        )

    # Create the ticket
    ticket = Ticket(
        subject=subject,
        description=description,
        sender_name=data.get("sender_name"),
        sender_email=data.get("sender_email"),
        source="webhook",
        status="new",
    )
    db.add(ticket)
    db.flush()

    logger.info("Ticket #%d created from incoming webhook (event: %s).", ticket.id, payload.event)

    audit = AuditLog(
        ticket_id=ticket.id,
        action="created",
        details=f"Created from incoming webhook event '{payload.event}'.",
    )
    db.add(audit)

    # Run AI analysis
    try:
        analysis = ai_service.analyze_ticket(subject=subject, description=description)
        ticket.category = analysis.category
        ticket.priority = analysis.priority
        ticket.ai_summary = analysis.summary
        ticket.ai_draft_response = analysis.draft_response
        ticket.ai_confidence = analysis.confidence
        ticket.status = "processing"

        db.add(AuditLog(
            ticket_id=ticket.id,
            action="categorized",
            details=(
                f"AI classified: category={analysis.category}, "
                f"priority={analysis.priority}, confidence={analysis.confidence:.2f}."
            ),
        ))
    except Exception as exc:
        logger.error("AI analysis failed for webhook ticket #%d: %s", ticket.id, exc)

    # Route to team
    if ticket.category and ticket.priority:
        team = routing_service.route_ticket(ticket.category, ticket.priority)
        ticket.assigned_team = team
        ticket.status = "assigned"
        db.add(AuditLog(
            ticket_id=ticket.id,
            action="routed",
            details=f"Assigned to '{team}'.",
        ))

    db.commit()
    db.refresh(ticket)
    return ticket


# ────────────────────────────────────────────────────────────────────────
#  POST /test  —  Send a test webhook to the configured URL
# ────────────────────────────────────────────────────────────────────────

@router.post("/test")
async def test_webhook() -> dict:
    """Fire a test event to the configured ``WEBHOOK_URL``.

    Returns a JSON object indicating whether delivery succeeded.
    """
    if not settings.WEBHOOK_URL:
        raise HTTPException(
            status_code=400,
            detail="No WEBHOOK_URL configured. Set it in your .env file.",
        )

    success = await notification_service.send_webhook(
        webhook_url=settings.WEBHOOK_URL,
        event="test.ping",
        ticket_data={"message": "This is a test webhook from AI Ticket Automation."},
    )

    return {
        "delivered": success,
        "webhook_url": settings.WEBHOOK_URL,
        "event": "test.ping",
    }
