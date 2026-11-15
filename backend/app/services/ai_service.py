"""
AI Analysis Service
~~~~~~~~~~~~~~~~~~~

The core intelligence layer of the ticket automation system.  Given a
ticket's subject and description, this service classifies it into a
category and priority, generates a concise summary, and drafts a
professional customer-facing response.

**Provider cascade (when AI_PROVIDER == "auto"):**

1. Google Gemini  (gemini-1.5-flash)  — fast, cost-effective
2. OpenAI         (gpt-3.5-turbo)     — widely available fallback
3. Rule-based     (keyword matching)   — works offline, no API key needed
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from app.config import settings
from app.schemas import AIAnalysisResult

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────
#  Shared prompt template
# ────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert customer-support AI.  Analyse the support ticket below
and return a JSON object with EXACTLY these keys (no markdown fences):

{
  "category": one of "billing", "technical", "account", "general", "bug_report", "feature_request",
  "priority": one of "critical", "high", "medium", "low",
  "summary": "A concise 1–2 sentence summary of the issue.",
  "draft_response": "A professional, empathetic reply to the customer.",
  "confidence": 0.0 to 1.0 indicating how confident you are in the classification
}

Return ONLY valid JSON.  No extra text.
"""

_USER_TEMPLATE = "Subject: {subject}\n\nDescription:\n{description}"


# ────────────────────────────────────────────────────────────────────────
#  Keyword dictionaries for the rule-based fallback
# ────────────────────────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: Dict[str, list[str]] = {
    "billing": ["invoice", "payment", "charge", "refund", "billing", "subscription", "price"],
    "technical": ["error", "bug", "crash", "not working", "broken", "fix", "issue"],
    "account": ["account", "password", "login", "access", "reset", "profile"],
    "feature_request": ["feature", "suggest", "would be nice", "add", "improve", "enhancement"],
    "bug_report": ["bug", "defect", "regression", "unexpected behavior"],
}

_CRITICAL_KEYWORDS = ["urgent", "asap", "critical", "immediately", "emergency"]
_HIGH_KEYWORDS = ["important", "serious", "escalate", "priority"]


# ────────────────────────────────────────────────────────────────────────
#  Helper: extract JSON from an LLM response
# ────────────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Dict[str, Any]:
    """Parse a JSON object from *text*, tolerating markdown code fences."""
    # Strip optional ```json ... ``` wrapper
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    return json.loads(cleaned)


def _clamp_confidence(value: Any) -> float:
    """Ensure confidence is a float in [0, 1]."""
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


# ────────────────────────────────────────────────────────────────────────
#  AI Service
# ────────────────────────────────────────────────────────────────────────

class AIService:
    """Analyses support tickets using LLM providers with automatic fallback."""

    # Valid values that the analysis must produce.
    _VALID_CATEGORIES = {
        "billing", "technical", "account", "general", "bug_report", "feature_request",
    }
    _VALID_PRIORITIES = {"critical", "high", "medium", "low"}

    # ── Public API ──────────────────────────────────────────────────────

    def analyze_ticket(self, subject: str, description: str) -> AIAnalysisResult:
        """Classify, summarise, and draft a response for a support ticket.

        The provider is chosen according to ``settings.AI_PROVIDER``:

        * ``"gemini"``   — use Google Gemini only.
        * ``"openai"``   — use OpenAI only.
        * ``"fallback"`` — use the rule-based classifier only.
        * ``"auto"``     — try Gemini → OpenAI → rule-based (default).

        Returns:
            An ``AIAnalysisResult`` with category, priority, summary,
            draft_response, and confidence.
        """
        provider = settings.AI_PROVIDER.lower()

        if provider == "gemini":
            return self._analyze_with_gemini(subject, description)
        if provider == "openai":
            return self._analyze_with_openai(subject, description)
        if provider == "fallback":
            return self._analyze_with_rules(subject, description)

        # Auto mode: cascade through providers
        return self._analyze_auto(subject, description)

    # ── Auto cascade ────────────────────────────────────────────────────

    def _analyze_auto(self, subject: str, description: str) -> AIAnalysisResult:
        """Try each provider in order, falling back on failure."""

        # 1️⃣  Gemini
        if settings.GEMINI_API_KEY:
            try:
                result = self._analyze_with_gemini(subject, description)
                logger.info("AI analysis completed via Google Gemini.")
                return result
            except Exception as exc:
                logger.warning("Gemini analysis failed (%s); falling back.", exc)

        # 2️⃣  OpenAI
        if settings.OPENAI_API_KEY:
            try:
                result = self._analyze_with_openai(subject, description)
                logger.info("AI analysis completed via OpenAI.")
                return result
            except Exception as exc:
                logger.warning("OpenAI analysis failed (%s); falling back.", exc)

        # 3️⃣  Rule-based
        logger.info("Using rule-based fallback for ticket analysis.")
        return self._analyze_with_rules(subject, description)

    # ── Google Gemini ───────────────────────────────────────────────────

    def _analyze_with_gemini(self, subject: str, description: str) -> AIAnalysisResult:
        """Call Google Gemini (gemini-1.5-flash) for ticket analysis."""
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        user_message = _USER_TEMPLATE.format(subject=subject, description=description)
        response = model.generate_content(
            [
                {"role": "user", "parts": [_SYSTEM_PROMPT + "\n\n" + user_message]},
            ],
        )

        data = _extract_json(response.text)
        return self._validate_result(data, provider="gemini")

    # ── OpenAI ──────────────────────────────────────────────────────────

    def _analyze_with_openai(self, subject: str, description: str) -> AIAnalysisResult:
        """Call OpenAI (gpt-3.5-turbo) for ticket analysis."""
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        user_message = _USER_TEMPLATE.format(subject=subject, description=description)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=600,
        )

        raw = completion.choices[0].message.content or ""
        data = _extract_json(raw)
        return self._validate_result(data, provider="openai")

    # ── Rule-based fallback ─────────────────────────────────────────────

    def _analyze_with_rules(self, subject: str, description: str) -> AIAnalysisResult:
        """Classify a ticket using keyword matching (no API key required)."""
        combined = f"{subject} {description}".lower()

        # ── Category detection ──────────────────────────────────────────
        category = "general"
        best_score = 0
        for cat, keywords in _CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > best_score:
                best_score = score
                category = cat

        # ── Priority detection ──────────────────────────────────────────
        priority = "medium"
        if any(kw in combined for kw in _CRITICAL_KEYWORDS):
            priority = "critical"
        elif any(kw in combined for kw in _HIGH_KEYWORDS):
            priority = "high"

        # ── Summary (first 120 chars of description) ────────────────────
        summary = description[:120].strip()
        if len(description) > 120:
            summary += "…"

        # ── Draft response ──────────────────────────────────────────────
        draft_response = (
            f"Thank you for reaching out to us regarding \"{subject}\". "
            f"We have received your request and our {category.replace('_', ' ')} team "
            f"will review it shortly. We appreciate your patience and will "
            f"get back to you as soon as possible."
        )

        logger.info("AI analysis completed via rule-based fallback (category=%s, priority=%s).", category, priority)

        return AIAnalysisResult(
            category=category,
            priority=priority,
            summary=summary,
            draft_response=draft_response,
            confidence=round(min(best_score * 0.25, 0.75), 2) if best_score else 0.3,
        )

    # ── Result validation ───────────────────────────────────────────────

    def _validate_result(self, data: Dict[str, Any], provider: str) -> AIAnalysisResult:
        """Sanitise and validate the raw dict returned by an LLM provider."""
        category = str(data.get("category", "general")).lower().strip()
        if category not in self._VALID_CATEGORIES:
            logger.warning("Provider %s returned invalid category '%s'; defaulting to 'general'.", provider, category)
            category = "general"

        priority = str(data.get("priority", "medium")).lower().strip()
        if priority not in self._VALID_PRIORITIES:
            logger.warning("Provider %s returned invalid priority '%s'; defaulting to 'medium'.", provider, priority)
            priority = "medium"

        return AIAnalysisResult(
            category=category,
            priority=priority,
            summary=str(data.get("summary", "No summary available.")),
            draft_response=str(data.get("draft_response", "Thank you for contacting us. We will look into this.")),
            confidence=_clamp_confidence(data.get("confidence", 0.5)),
        )


# Module-level convenience instance.
ai_service = AIService()
