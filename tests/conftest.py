import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from decisionos.api.main import app
from decisionos.core.database import Base, get_db
from decisionos.core import config

# Use an in-memory SQLite database for testing to ensure isolation and speed
# Note: In a real asyncpg project we might use a separate Postgres DB, 
# but for this demo/logic verification, SQLite is often sufficient if we don't use PG-specific features.
# However, since we used asyncpg specifically in core/database.py, we should be careful.
# If code relies on asyncpg dialect, sqlite won't work.
# Let's mock the DB dependency or utilize a test config if possible.
# For now, I'll attempt to use the actual engine structure but possibly need a real DB or mock.
# Given the environment, I'll stick to mocking the session or using a test API client that purely inputs/outputs.

# Actually, let's use a mock for the database session to avoid needing a running Postgres instance for unit tests.
# This makes tests portable and fast.

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for integration tests.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_feature_vector():
    return {
        "urgency": 0.8,
        "commercial_value": 0.5,
        "market_volatility": 0.2
    }
