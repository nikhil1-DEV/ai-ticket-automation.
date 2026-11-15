"""
Notification Service
~~~~~~~~~~~~~~~~~~~~

Sends outgoing webhook notifications when significant events occur
(e.g. a ticket is assigned to a team).  Uses ``httpx`` for HTTP calls
with sensible timeouts and error handling — a failed webhook should
*never* crash the main request.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.schemas import TicketResponse

logger = logging.getLogger(__name__)

# Timeout for outgoing webhook calls (connect / read / total).
_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, pool=5.0)


class NotificationService:
    """Delivers webhook notifications to external systems."""

    async def send_webhook(
        self,
        webhook_url: str,
        event: str,
        ticket_data: Dict[str, Any],
    ) -> bool:
        """POST an event payload to *webhook_url*.

        Args:
            webhook_url: The destination URL.
            event: A dot-delimited event name (e.g. ``"ticket.assigned"``).
            ticket_data: Arbitrary payload data to include.

        Returns:
            ``True`` if the webhook was delivered successfully (2xx),
            ``False`` otherwise.
        """
        payload = {
            "event": event,
            "data": ticket_data,
        }

        logger.info("Sending webhook '%s' → %s", event, webhook_url)

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(webhook_url, json=payload)

            if response.is_success:
                logger.info(
                    "Webhook delivered successfully (status %d).",
                    response.status_code,
                )
                return True

            logger.warning(
                "Webhook returned non-success status %d: %s",
                response.status_code,
                response.text[:200],
            )
            return False

        except httpx.TimeoutException:
            logger.error("Webhook timed out → %s", webhook_url)
            return False
        except httpx.HTTPError as exc:
            logger.error("Webhook HTTP error → %s: %s", webhook_url, exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error sending webhook → %s: %s", webhook_url, exc)
            return False

    async def notify_team_assignment(
        self,
        ticket: TicketResponse,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """Send a notification when a ticket is assigned to a team.

        Args:
            ticket: The ticket that was just assigned.
            webhook_url: Override URL; falls back to ``settings.WEBHOOK_URL``.

        Returns:
            ``True`` if delivered, ``False`` if skipped or failed.
        """
        if webhook_url is None:
            from app.config import settings
            webhook_url = settings.WEBHOOK_URL

        if not webhook_url:
            logger.debug("No webhook URL configured — skipping team-assignment notification.")
            return False

        ticket_data = {
            "ticket_id": ticket.id,
            "subject": ticket.subject,
            "category": ticket.category,
            "priority": ticket.priority,
            "assigned_team": ticket.assigned_team,
            "status": ticket.status,
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            event="ticket.assigned",
            ticket_data=ticket_data,
        )


# Module-level convenience instance.
notification_service = NotificationService()
