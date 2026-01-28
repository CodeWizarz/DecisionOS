from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from decisionos.core.config import settings

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

# Create Async Engine
# echo=True in dev for visibility into SQL queries
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    future=True,
    pool_pre_ping=True  # Detect and recover from stale connections
)

# Implementation of Unit of Work pattern
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routers.
    
    Yields a database session and ensures it closes after the request.
    Handles transaction rollback on error automatically via context manager.
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
