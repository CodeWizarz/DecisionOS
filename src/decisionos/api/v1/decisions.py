from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from decisionos.core.database import get_db
from decisionos.domain import schemas, models
from decisionos.core.queue import queue
# In a real app, we would inject the engine service. 
# For this demo, we mock the engine triggering.

router = APIRouter()

@router.post(
    "/generate",
    response_model=schemas.Decision,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger decision generation"
)
async def generate_decision(
    request: schemas.DecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger the full multi-agent decision pipeline.
    
    Process:
    1. Validate request (Pydantic)
    2. Enqueue 'generate_decision' task (Async)
    3. Return 'Accepted' immediately with decision placeholder ID
    """
    # Create placeholder decision record
    decision_id = uuid4()
    
    # In a real impl, we would persist the request first.
    # Logic simplified for demo duration.
    
    # Enqueue pipeline task
    queue.enqueue_data_processing(str(decision_id), request.model_dump())
    
    # Return provisional response 
    # (Client polls /decisions/{id} for result)
    return schemas.Decision(
        id=decision_id,
        request_id=uuid4(), 
        rank=0,
        content={"status": "processing"},
        created_at=datetime.utcnow() 
    )

@router.get(
    "/{decision_id}",
    response_model=schemas.Decision,
    summary="Get decision details",
    description="Retrieve a decision by ID, including its score, confidence, and explanation."
)
async def get_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch a specific decision.
    """
    result = await db.execute(select(models.DecisionModel).where(models.DecisionModel.id == decision_id))
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    return decision

@router.get(
    "",
    response_model=List[schemas.Decision],
    summary="List recent decisions",
    description="Fetch a paginated list of recent decisions."
)
async def list_decisions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.DecisionModel)
        .order_by(models.DecisionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
