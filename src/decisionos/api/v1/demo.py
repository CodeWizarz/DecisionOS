from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from typing import Dict, Any

from decisionos.core.database import get_db
from decisionos.domain import schemas, models
from decisionos.core.queue import queue
from decisionos.core.config import settings

router = APIRouter()

@router.get("/status", summary="Check demo system status")
async def check_status():
    """
    Validation endpoint for the Web UI.
    """
    return {
        "status": "online",
        "mode": "demo" if settings.DEMO_MODE else "mixed",
        "llm_enabled": settings.USE_LLM
    }

@router.post(
    "/run-decision",
    response_model=schemas.Decision,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger deterministic demo decision"
)
async def trigger_demo_decision(
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers the constrained "Ops Incident" scenario.
    Input data is ignored in favor of hardcoded synthetic signals.
    """
    decision_id = uuid4()
    
    # 1. Create Placeholder
    new_decision = models.DecisionModel(
        id=decision_id,
        request_id=uuid4(),
        result={"status": "processing", "stage": "ingestion"},
        explanation=None,
        confidence=0.0
    )
    
    db.add(new_decision)
    await db.commit()
    await db.refresh(new_decision)
    
    # 2. Enqueue with explicit DEMO flag in payload
    # This instructs the worker to ignore inputs and load synthetic data
    payload = {
        "is_demo": True,
        "scenario": "ops_incident_latency_spike"
    }
    
    queue.enqueue_data_processing(str(decision_id), payload)
    
    return new_decision

@router.get(
    "/decision/{decision_id}",
    response_model=schemas.Decision,
    summary="Get demo decision details"
)
async def get_demo_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Standard retrieval, mapped for consistency.
    """
    result = await db.execute(select(models.DecisionModel).where(models.DecisionModel.id == decision_id))
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    return decision
