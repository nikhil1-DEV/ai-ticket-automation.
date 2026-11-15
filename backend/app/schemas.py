"""
Pydantic v2 Schemas
~~~~~~~~~~~~~~~~~~~

Request / response models used by the API layer.  These are intentionally
decoupled from the SQLAlchemy ORM models so the public contract can evolve
independently of the database schema.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ────────────────────────────────────────────────────────────────────────
#  Ticket Schemas
# ────────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    """Payload for creating a new support ticket."""

    subject: str = Field(..., min_length=1, max_length=255, description="Brief summary of the issue")
    description: str = Field(..., min_length=1, description="Full description of the issue")
    sender_name: Optional[str] = Field(None, max_length=100, description="Name of the person submitting the ticket")
    sender_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    source: Optional[str] = Field("web_form", description="Origin: web_form | email | api | webhook")


class TicketResponse(BaseModel):
    """Complete ticket representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    description: str
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str
    assigned_team: Optional[str] = None
    ai_draft_response: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_summary: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime


class TicketUpdate(BaseModel):
    """Partial update payload for an existing ticket."""

    status: Optional[str] = Field(None, description="New workflow status")
    assigned_team: Optional[str] = Field(None, description="Team to assign the ticket to")
    priority: Optional[str] = Field(None, description="Revised priority level")


class TicketListResponse(BaseModel):
    """Paginated list of tickets."""

    tickets: List[TicketResponse]
    total: int


# ────────────────────────────────────────────────────────────────────────
#  Dashboard Schemas
# ────────────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    """Aggregated statistics for the dashboard view."""

    total_tickets: int
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    by_status: Dict[str, int]
    avg_confidence: Optional[float] = None
    recent_tickets: List[TicketResponse]


# ────────────────────────────────────────────────────────────────────────
#  Audit Log Schema
# ────────────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    """A single audit-log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    action: str
    details: Optional[str] = None
    created_at: datetime


# ────────────────────────────────────────────────────────────────────────
#  Webhook Schemas
# ────────────────────────────────────────────────────────────────────────

class WebhookPayload(BaseModel):
    """Incoming or outgoing webhook envelope."""

    event: str = Field(..., description="Event type, e.g. 'ticket.created'")
    ticket_id: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)


# ────────────────────────────────────────────────────────────────────────
#  AI Analysis Schema
# ────────────────────────────────────────────────────────────────────────

class AIAnalysisResult(BaseModel):
    """Structured output from the AI analysis pipeline."""

    category: str
    priority: str
    summary: str
    draft_response: str
    confidence: float = Field(ge=0.0, le=1.0)
