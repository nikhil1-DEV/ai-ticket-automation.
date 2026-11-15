"""
Application Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Centralized settings management using pydantic-settings.
All configuration is loaded from environment variables (or a .env file),
with sensible defaults for local development.
"""

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings populated from environment variables.

    Attributes:
        DATABASE_URL: SQLAlchemy connection string. Defaults to a local SQLite file.
        GEMINI_API_KEY: Google Gemini API key for AI-powered ticket analysis.
        OPENAI_API_KEY: OpenAI API key (used as fallback when Gemini is unavailable).
        AI_PROVIDER: Which AI provider to use — "gemini", "openai", "fallback",
                     or "auto" (tries gemini → openai → rule-based fallback).
        WEBHOOK_URL: Default outgoing webhook URL for notifications.
        APP_NAME: Display name of the application.
        CORS_ORIGINS: Allowed CORS origins for the frontend dev servers.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Database ────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./tickets.db"

    # ── AI Provider Keys ────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "auto"  # "gemini" | "openai" | "fallback" | "auto"

    # ── Webhooks / Notifications ────────────────────────────────────────
    WEBHOOK_URL: Optional[str] = None

    # ── Application Metadata ────────────────────────────────────────────
    APP_NAME: str = "AI Ticket Automation"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]


# Singleton instance — import this wherever settings are needed.
settings = Settings()
