"""Pytest configuration and fixtures."""

import asyncio
import sys
from pathlib import Path

import pytest

# Add backend app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
