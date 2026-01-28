from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from decisionos.core.config import settings

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

# Create Async Engine
# 
# Why Async IO (asyncpg)?
# 1. Non-blocking I/O: In a high-throughput ingestion system, waiting for DB
#    queries synchronously would block the event loop, starving other requests.
#    AsyncPG allows handling thousands of concurrent connections/requests efficiently.
# 2. Performance: asyncpg is significantly faster than psycopg2.
#
# Why Engine Configuration?
# - pool_pre_ping=True: Handles "database gone away" errors gracefully by checking connections.
# - future=True: Enables SQLAlchemy 2.0 style usage.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    future=True,
    pool_pre_ping=True
)

# Implementation of Unit of Work pattern via AsyncSession
# 
# Why SessionMaker?
# - Factory for creating new database sessions for each request.
# - Ensures thread/task safety (each request gets its own session).
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False, # Critical for async: prevents implicit IO when accessing attributes after commit
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routers.
    
    Why Generator?
    - Integration with FastAPI's Depends() system for dependency injection.
    - Lifecycle management: automatically closes session after request finishes.
    
    Flow:
    1. Create session
    2. Yield to route handler
    3. Commit if successful (Unit of Work)
    4. Rollback if exception occurs
    5. Close connection guarantees cleanup
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
