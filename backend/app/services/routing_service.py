"""
Ticket Routing Service
~~~~~~~~~~~~~~~~~~~~~~

Determines which support team should handle a ticket based on its
category and priority.  Critical tickets are always escalated to the
Engineering Team regardless of category.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── Category → Team mapping ────────────────────────────────────────────

_TEAM_MAP: dict[str, str] = {
    "billing":          "Finance Team",
    "technical":        "Engineering Team",
    "bug_report":       "Engineering Team",
    "account":          "Account Management",
    "feature_request":  "Product Team",
    "general":          "General Support",
}


class RoutingService:
    """Routes tickets to the appropriate team."""

    def route_ticket(self, category: str, priority: str) -> str:
        """Return the team name that should handle a ticket.

        Args:
            category: The ticket's classified category
                      (e.g. ``"billing"``, ``"technical"``).
            priority: The ticket's classified priority
                      (e.g. ``"critical"``, ``"high"``).

        Returns:
            The name of the team to assign the ticket to.

        Routing rules:
            1. **Critical escalation** — any ticket with ``priority == "critical"``
               is routed straight to *Engineering Team*.
            2. Otherwise, the category is looked up in the mapping table.
            3. Unknown categories fall back to *General Support*.
        """
        # Rule 1: critical tickets are always escalated.
        if priority == "critical":
            logger.info(
                "Critical priority detected — escalating to Engineering Team "
                "(original category: %s).",
                category,
            )
            return "Engineering Team"

        # Rule 2: look up by category.
        team = _TEAM_MAP.get(category, "General Support")
        logger.info("Routing category '%s' → '%s'.", category, team)
        return team


# Module-level convenience instance.
routing_service = RoutingService()
