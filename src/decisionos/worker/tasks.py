import structlog
import asyncio
from uuid import UUID
from celery import shared_task
from typing import Dict, Any
from sqlalchemy import select

from decisionos.core.logging import configure_logging
from decisionos.core.database import AsyncSessionLocal
from decisionos.domain.models import DecisionModel
from decisionos.engine.agents import SignalAgent, DecisionAgent, CriticAgent, SupervisorAgent

# Ensure logging is configured in worker process
configure_logging()
logger = structlog.get_logger()

async def run_agent_pipeline(decision_id: str, payload: Dict[str, Any]):
    """
    Orchestrates the multi-agent flow and updates the database.
    """
    logger.info("starting_agent_pipeline", decision_id=decision_id)
    
    # 1. Initialize Agents
    signal_agent = SignalAgent()
    decision_agent = DecisionAgent()
    critic_agent = CriticAgent()
    supervisor_agent = SupervisorAgent()
    
    # 2. Construct Context (Simulate Ingestion/Normalization for Demo)
    # in a real system, we'd fetch data_points from DB based on payload context
    logger.info("ingesting_signals", decision_id=decision_id)
    
    # Mock data representing the Ops Scenario
    # This data simulates finding a high latency cluster
    mock_clusters = {
        "web_tier_metrics": [
            {"source": "datadog.latency.p99", "normalized_priority": 0.92, "timestamp": 123456789},
            {"source": "datadog.error_rate", "normalized_priority": 0.4, "timestamp": 123456789}
        ],
        "db_tier_metrics": [
            {"source": "postgres.cpu", "normalized_priority": 0.60, "timestamp": 123456789}
        ]
    }
    
    context = {"clusters": mock_clusters, "request_payload": payload}
    
    # 3. Execution Loop
    try:
        # Step 1: Signal Analysis
        r1 = await signal_agent.run(context)
        logger.info("step_complete", agent="SignalAgent", findings=r1.conclusion)
        context.update(r1.conclusion)
        
        # Step 2: Decision Proposal
        r2 = await decision_agent.run(context)
        logger.info("step_complete", agent="DecisionAgent", proposal=r2.conclusion)
        context.update(r2.conclusion)
        
        # Step 3: Critique
        r3 = await critic_agent.run(context)
        logger.info("step_complete", agent="CriticAgent", critique=r3.conclusion)
        context.update(r3.conclusion)
        
        # Step 4: Final Synthesis
        r4 = await supervisor_agent.run(context)
        logger.info("pipeline_complete", result=r4.conclusion)
        
        # 4. Persistence
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DecisionModel).where(DecisionModel.id == UUID(decision_id)))
            decision = result.scalar_one_or_none()
            
            if decision:
                decision.result = r4.conclusion
                decision.explanation = {
                    "summary": r4.thought_process,
                    "reasoning_trace": [
                        {"agent": "SignalAgent", "thought": r1.thought_process},
                        {"agent": "DecisionAgent", "thought": r2.thought_process},
                        {"agent": "CriticAgent", "thought": r3.thought_process},
                        {"agent": "SupervisorAgent", "thought": r4.thought_process}
                    ],
                    "factor_weights": {"signal_strength": 0.7, "risk_factors": 0.3},
                    "confidence_score": r4.confidence
                }
                decision.confidence = r4.confidence
                await session.commit()
                logger.info("decision_persisted", decision_id=decision_id)
            else:
                logger.error("decision_not_found_in_db", decision_id=decision_id)
                
    except Exception as e:
        logger.error("pipeline_failed", error=str(e))
        # Update DB with error if possible
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DecisionModel).where(DecisionModel.id == UUID(decision_id)))
            decision = result.scalar_one_or_none()
            if decision:
                decision.result = {"status": "failed", "error": str(e)}
                await session.commit()
        raise

@shared_task(
    bind=True, 
    autoretry_for=(Exception,),
    retry_backoff=True, 
    retry_kwargs={'max_retries': 3},
    name="process_data_point"
)
def process_data_point(self, data_point_id: str, payload: Dict[str, Any]) -> str:
    """
    Background task to process ingested data.
    Now connected to the Real Agent Engine.
    """
    logger.info("processing_task_started", id=data_point_id)
    
    try:
        asyncio.run(run_agent_pipeline(data_point_id, payload))
    except Exception as e:
        logger.error("task_execution_failed", error=str(e))
        raise
        
    return f"Processed {data_point_id}"
