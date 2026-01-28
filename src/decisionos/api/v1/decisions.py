from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from decisionos.core.database import get_db
from decisionos.domain import schemas, models
from decisionos.worker.tasks import process_data_point # Placeholder for decision task

router = APIRouter()

@router.post(
    "/generate",
    response_model=schemas.Decision,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger decision generation"
)
async def generate_decision(
    request: schemas.DecisionRequest,
    background_tasks: BackgroundTasks = None # Example of non-celery background if needed
):
    """
    Request a new decision generation.
    Returns 202 Accepted as this is an async operation.
    """
    pass # TODO: Implement decision request tracking
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.get(
    "/{decision_id}",
    response_model=schemas.Decision,
    summary="Get decision by ID"
)
async def get_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.DecisionModel).where(models.DecisionModel.id == decision_id))
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    return decision
