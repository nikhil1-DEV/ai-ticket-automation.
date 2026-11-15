"""
SQLAlchemy ORM Models
~~~~~~~~~~~~~~~~~~~~~

Defines the relational schema for tickets, teams, and audit logs.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.database import Base


def _utcnow() -> datetime:
    """Return the current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


# ── Ticket ──────────────────────────────────────────────────────────────

class Ticket(Base):
    """A support ticket submitted via the web form, email, API, or webhook."""

    __tablename__ = "tickets"

    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Core fields
    subject: str = Column(String(255), nullable=False)
    description: str = Column(Text, nullable=False)
    sender_name: str | None = Column(String(100), nullable=True)
    sender_email: str | None = Column(String(255), nullable=True)

    # Classification (populated by AI or rule-based fallback)
    category: str | None = Column(
        String(50),
        nullable=True,
        comment="billing | technical | account | general | bug_report | feature_request",
    )
    priority: str | None = Column(
        String(20),
        nullable=True,
        comment="critical | high | medium | low",
    )

    # Workflow
    status: str = Column(String(30), nullable=False, default="new")
    assigned_team: str | None = Column(String(50), nullable=True)

    # AI analysis artefacts
    ai_draft_response: str | None = Column(Text, nullable=True)
    ai_confidence: float | None = Column(Float, nullable=True)
    ai_summary: str | None = Column(Text, nullable=True)

    # Provenance
    source: str = Column(String(20), nullable=False, default="web_form")

    # Timestamps
    created_at: datetime = Column(DateTime, default=_utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Ticket id={self.id} subject={self.subject!r} "
            f"category={self.category} priority={self.priority} status={self.status}>"
        )


# ── Team ────────────────────────────────────────────────────────────────

class Team(Base):
    """A support team that can be assigned tickets."""

    __tablename__ = "teams"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(50), unique=True, nullable=False)
    description: str | None = Column(String(255), nullable=True)
    categories: str | None = Column(
        Text,
        nullable=True,
        comment="JSON-encoded list of categories this team handles",
    )
    webhook_url: str | None = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name!r}>"


# ── Audit Log ───────────────────────────────────────────────────────────

class AuditLog(Base):
    """Immutable log of every action taken on a ticket."""

    __tablename__ = "audit_logs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id: int = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    action: str = Column(
        String(50),
        nullable=False,
        comment="created | categorized | routed | status_changed | response_drafted",
    )
    details: str | None = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} ticket_id={self.ticket_id} action={self.action!r}>"
