"""
FastAPI Application Entry Point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configures middleware, registers routers, seeds default data, and
exposes health / info endpoints.

Run with::

    python -m uvicorn app.main:app --reload
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, create_tables
from app.models import Team

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Default teams to seed on first run ──────────────────────────────────
_DEFAULT_TEAMS = [
    {
        "name": "Engineering Team",
        "description": "Handles technical issues, bug reports, and critical escalations.",
        "categories": json.dumps(["technical", "bug_report"]),
    },
    {
        "name": "Finance Team",
        "description": "Handles billing inquiries, refunds, and subscription issues.",
        "categories": json.dumps(["billing"]),
    },
    {
        "name": "Account Management",
        "description": "Handles account access, password resets, and profile issues.",
        "categories": json.dumps(["account"]),
    },
    {
        "name": "Product Team",
        "description": "Reviews feature requests and product improvement suggestions.",
        "categories": json.dumps(["feature_request"]),
    },
    {
        "name": "General Support",
        "description": "Catches all other inquiries and general questions.",
        "categories": json.dumps(["general"]),
    },
]


def _seed_teams() -> None:
    """Insert default teams if the teams table is empty."""
    db: Session = SessionLocal()
    try:
        if db.query(Team).count() == 0:
            for team_data in _DEFAULT_TEAMS:
                db.add(Team(**team_data))
            db.commit()
            logger.info("Seeded %d default teams.", len(_DEFAULT_TEAMS))
        else:
            logger.info("Teams table already populated — skipping seed.")
    finally:
        db.close()


# ── Lifespan (startup / shutdown) ───────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables and seed data.  Shutdown: (no-op)."""
    logger.info("Starting %s …", settings.APP_NAME)
    create_tables()
    _seed_teams()
    logger.info("Application ready.")
    yield
    logger.info("Shutting down %s.", settings.APP_NAME)


# ── FastAPI application ────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "An intelligent support-ticket system that uses AI to automatically "
        "classify, prioritise, summarise, and route incoming tickets."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS middleware ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ───────────────────────────────────────────────────
from app.routes.tickets import router as tickets_router      # noqa: E402
from app.routes.dashboard import router as dashboard_router  # noqa: E402
from app.routes.webhooks import router as webhooks_router    # noqa: E402

app.include_router(tickets_router)
app.include_router(dashboard_router)
app.include_router(webhooks_router)


# ── Root / health endpoints ────────────────────────────────────────────

@app.get("/", tags=["Meta"])
def root() -> dict:
    """Application info and links."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Meta"])
def health_check() -> dict:
    """Lightweight health-check endpoint for load balancers and monitors."""
    return {"status": "healthy"}
