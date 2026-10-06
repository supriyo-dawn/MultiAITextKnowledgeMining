"""Pytest configuration and fixtures."""

import asyncio
import sys
from pathlib import Path

import pytest

# Add backend directory and project root to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_db(event_loop):
    """Ensure database tables exist and clear test data before and after each test."""
    from app.core.database import init_db, async_session_factory
    from sqlalchemy import text

    async def _clean():
        await init_db()
        async with async_session_factory() as session:
            await session.execute(text("DELETE FROM chunks"))
            await session.execute(text("DELETE FROM documents"))
            await session.commit()

    event_loop.run_until_complete(_clean())
    yield
    event_loop.run_until_complete(_clean())


