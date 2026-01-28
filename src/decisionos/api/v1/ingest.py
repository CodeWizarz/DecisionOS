from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from datetime import datetime

from decisionos.core.database import get_db
from decisionos.domain import schemas, models
from decisionos.worker.tasks import process_data_point

router = APIRouter()
logger = structlog.get_logger()

@router.post(
    "", 
    response_model=schemas.DataPoint, 
    status_code=status.HTTP_201_CREATED,
    summary="Ingest single operational data point"
)
async def ingest_data_point(
    data: schemas.DataPoint,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a new data point for processing.
    
    Flow:
    1. Validate input (Pydantic)
    2. Persist raw data to DB (AsyncPG)
    3. Trigger async background processing (Celery)
    """
    # 1. Persist
    db_model = models.DataPointModel(
        id=data.id,
        source=data.source,
        payload=data.data,
        created_at=data.timestamp
    )
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    
    # 2. Enqueue for processing
    process_data_point.delay(str(db_model.id), data.data)
    
    logger.info("data_ingested", id=str(data.id), source=data.source)
    return db_model

@router.post(
    "/batch",
    response_model=List[schemas.DataPoint],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch ingest data points"
)
async def batch_ingest(
    batch: List[schemas.DataPoint],
    db: AsyncSession = Depends(get_db)
):
    """
    High-throughput batch ingestion.
    """
    db_models = []
    
    for item in batch:
        model = models.DataPointModel(
            id=item.id,
            source=item.source,
            payload=item.data,
            created_at=item.timestamp
        )
        db_models.append(model)
        
    db.add_all(db_models)
    await db.commit()
    
    # Trigger tasks in bulk effectively
    for model in db_models:
         process_data_point.delay(str(model.id), model.payload)
         
    return db_models
