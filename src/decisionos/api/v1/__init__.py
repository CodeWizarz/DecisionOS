from fastapi import APIRouter
from decisionos.api.v1 import ingest, decisions

router = APIRouter()

router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
router.include_router(decisions.router, prefix="/decisions", tags=["Decisions"])
