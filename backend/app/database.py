"""
Database Setup
~~~~~~~~~~~~~~

Configures the SQLAlchemy engine, session factory, and provides a
dependency-injection helper for FastAPI route handlers.

Uses synchronous SQLAlchemy (perfectly adequate for SQLite) to keep the
setup straightforward and easy to reason about.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# ── Engine & Session Factory ────────────────────────────────────────────
# `check_same_thread=False` is required for SQLite when used with FastAPI,
# because requests may be served by different threads.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set True to see generated SQL (noisy in production)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for all ORM models.
Base = declarative_base()


def create_tables() -> None:
    """Create all tables that don't already exist.

    Called once at application startup (see ``app.main``).
    """
    from app import models  # noqa: F401 — ensure models are imported so Base knows about them

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    The session is automatically closed when the request finishes,
    even if an exception occurs.

    Usage in a route::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
