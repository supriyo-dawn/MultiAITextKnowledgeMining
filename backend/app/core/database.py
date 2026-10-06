"""
Database configuration using SQLAlchemy async with SQLite.

Phase A: SQLite for development. Can be swapped to PostgreSQL
for production by changing DATABASE_URL.

Architecture:
    - async engine: manages the connection pool
    - async_session: factory that produces database sessions
    - Base: declarative base class for ORM models
"""

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# SQLite database file stored in backend/data/
_DB_DIR = Path(__file__).parent.parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{_DB_DIR / 'knowledge_mining.db'}"

# Create async engine
# echo=False in production; set True for SQL debugging
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # SQLite needs this for write concurrency
    connect_args={"check_same_thread": False},
)

# Session factory — each call produces a new AsyncSession
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def init_db() -> None:
    """
    Create all database tables.

    Called once during application startup (lifespan).
    Uses Base.metadata.create_all which is safe to call
    multiple times — it only creates tables that don't exist.
    """
    import app.models.db_models  # noqa: F401 - registers tables with Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Database initialized at {DATABASE_URL}")


async def shutdown_db() -> None:
    """Dispose of the engine connection pool on shutdown."""
    await engine.dispose()
    logger.info("Database connection pool closed")
