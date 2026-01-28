from sqlalchemy import Column, String, DateTime, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

from decisionos.core.database import Base

class DataPointModel(Base):
    """
    PostgreSQL model for raw data persistence.
    
    Why:
    - JSONB column allows flexible schema for 'payload' as operational data varies.
    - Indexed on source and timestamp for efficient querying.
    """
    __tablename__ = "data_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # Using JSON for flexibility
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class DecisionModel(Base):
    """
    Persisted decisions with audit trail.
    """
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True) # Link to source input
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
