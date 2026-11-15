"""
Seed Data Script
~~~~~~~~~~~~~~~~

Populates the database with sample tickets for demonstration purposes.
Runs AI analysis on each ticket if an API key is available; otherwise
falls back to the rule-based classifier.

Usage::

    cd backend
    python seed_data.py
"""

from __future__ import annotations

import logging
import sys

# Ensure the backend directory is on sys.path so `app` can be imported.
sys.path.insert(0, ".")

from app.database import SessionLocal, create_tables  # noqa: E402
from app.models import AuditLog, Ticket                # noqa: E402
from app.services.ai_service import ai_service          # noqa: E402
from app.services.routing_service import routing_service  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Sample tickets ──────────────────────────────────────────────────────

SAMPLE_TICKETS = [
    {
        "subject": "Cannot login to my account after password reset",
        "description": (
            "I reset my password yesterday using the forgot-password link, "
            "but now I keep getting 'Invalid credentials' every time I try "
            "to log in.  I've cleared my cookies and tried a different "
            "browser.  This is urgent because I need to access my billing "
            "information before end of day."
        ),
        "sender_name": "Alice Martinez",
        "sender_email": "alice.m@example.com",
        "source": "web_form",
    },
    {
        "subject": "Duplicate charge on my credit card",
        "description": (
            "I was charged twice for my monthly subscription on Nov 1st — "
            "two identical transactions of $29.99.  Please refund the "
            "duplicate payment as soon as possible.  My account ID is 78432."
        ),
        "sender_name": "Bob Chen",
        "sender_email": "bob.chen@example.com",
        "source": "email",
    },
    {
        "subject": "App crashes when uploading large files",
        "description": (
            "Every time I try to upload a file larger than 50 MB the desktop "
            "app crashes immediately with a white screen.  I'm on Windows 11 "
            "with version 4.2.1.  This is a critical bug because our team "
            "relies on large file uploads daily.  Please fix ASAP."
        ),
        "sender_name": "Carlos Rivera",
        "sender_email": "carlos@techstartup.io",
        "source": "api",
    },
    {
        "subject": "Feature request: dark mode for the dashboard",
        "description": (
            "It would be great if the dashboard had a dark mode option. "
            "I work late at night and the bright white background is hard "
            "on my eyes.  Many modern apps offer this.  An improvement "
            "like this would make a huge difference for accessibility."
        ),
        "sender_name": "Diana Patel",
        "sender_email": "diana.p@designco.com",
        "source": "web_form",
    },
    {
        "subject": "How do I export my data?",
        "description": (
            "I'd like to export all of my project data to CSV so I can "
            "share it with my manager.  I looked through the settings but "
            "couldn't find an export option.  Is this feature available? "
            "If so, could you point me to the right place?"
        ),
        "sender_name": "Erik Johansson",
        "sender_email": "erik.j@example.com",
        "source": "web_form",
    },
    {
        "subject": "Billing address update not saving",
        "description": (
            "I've been trying to update my billing address in the account "
            "settings page but the save button doesn't seem to do anything. "
            "No error message appears — the page just stays the same.  "
            "This is important because my next invoice needs the correct address."
        ),
        "sender_name": "Fatima Al-Rashid",
        "sender_email": "fatima@enterprise.co",
        "source": "email",
    },
    {
        "subject": "Unexpected error 500 on the reports page",
        "description": (
            "Since this morning the reports page returns a server error "
            "(HTTP 500) every time I try to generate the weekly summary.  "
            "Other pages work fine.  I've attached a screenshot of the "
            "error in the browser console.  This is seriously blocking "
            "our operations — we need this resolved immediately."
        ),
        "sender_name": "George Tanaka",
        "sender_email": "g.tanaka@corp.com",
        "source": "webhook",
    },
    {
        "subject": "Suggestion: integrate with Slack notifications",
        "description": (
            "Our team lives in Slack.  Would it be possible to add a Slack "
            "integration so we get notified when a ticket is assigned or "
            "updated?  This enhancement would really streamline our workflow."
        ),
        "sender_name": "Hannah Kim",
        "sender_email": "hannah.k@startup.dev",
        "source": "web_form",
    },
]


def main() -> None:
    """Create tables (if needed) and insert sample tickets."""
    create_tables()

    db = SessionLocal()
    try:
        existing = db.query(Ticket).count()
        if existing > 0:
            logger.info(
                "Database already contains %d ticket(s) — skipping seed to avoid duplicates.",
                existing,
            )
            return

        for data in SAMPLE_TICKETS:
            ticket = Ticket(**data, status="new")
            db.add(ticket)
            db.flush()

            # Run AI analysis
            try:
                analysis = ai_service.analyze_ticket(
                    subject=data["subject"],
                    description=data["description"],
                )
                ticket.category = analysis.category
                ticket.priority = analysis.priority
                ticket.ai_summary = analysis.summary
                ticket.ai_draft_response = analysis.draft_response
                ticket.ai_confidence = analysis.confidence
            except Exception as exc:
                logger.warning("AI analysis failed for '%s': %s", data["subject"], exc)

            # Route to team
            if ticket.category and ticket.priority:
                team = routing_service.route_ticket(ticket.category, ticket.priority)
                ticket.assigned_team = team
                ticket.status = "assigned"

            # Audit log
            db.add(AuditLog(
                ticket_id=ticket.id,
                action="created",
                details=f"Seeded sample ticket via {data['source']}.",
            ))

            logger.info(
                "  ✓ Ticket #%d  %-12s %-8s → %s",
                ticket.id,
                ticket.category or "—",
                ticket.priority or "—",
                ticket.assigned_team or "—",
            )

        db.commit()
        logger.info("Seeded %d sample tickets.", len(SAMPLE_TICKETS))

    finally:
        db.close()


if __name__ == "__main__":
    main()
