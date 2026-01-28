from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from decisionos.domain.schemas import DecisionExplanation
from decisionos.engine.agents import AgentReasoning
from decisionos.engine.scoring import DecisionScore

class InputTrace(BaseModel):
    input_id: str
    source: str
    canonical_type: str

class AuditLog(BaseModel):
    """
    Full audit trail for a single decision.
    
    Why Explainability is Mandatory in Production AI:
    1.  **Regulatory Compliance**: Laws like EU AI Act and GDPR (Article 22) grant users the 
        "right to explanation" for automated decisions. Black boxes are illegal in high-stakes contexts.
    2.  **Trust & Adoption**: Users (and executives) will not adopt a system they don't trust. 
        Seeing the *evidence* and *reasoning* bridges the gap between "computer says no" and "expert advice".
    3.  **Debugging & Safety**: When the AI fails (and it will), we need to know *exactly* which input 
        or agent step caused the error to prevent recurrence.
    """
    decision_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # 1. Traceability: Exactly what data fed this decision?
    inputs_used: List[InputTrace]
    
    # 2. Transparency: What steps did the AI take?
    agent_chain: List[AgentReasoning]
    
    # 3. Calibration: How confident are we?
    score_details: DecisionScore
    
    # 4. Human-Readable Summary
    final_narrative: str

class ExplainerEngine:
    def create_audit_trail(
        self, 
        decision_id: UUID,
        inputs: List[Any], # Should be NormalizedData
        agent_steps: List[AgentReasoning],
        score: DecisionScore
    ) -> AuditLog:
        """
        Synthesize interactions into a persisted audit object.
        """
        
        # 1. Trace Inputs
        traces = []
        for i in inputs:
            # Assuming NormalizedData structure or similar
            traces.append(InputTrace(
                input_id=str(getattr(i, 'id', 'unknown')),
                source=getattr(i, 'source', 'unknown'),
                canonical_type=getattr(i, 'canonical_type', 'unknown')
            ))
            
        # 2. Construct Narrative
        # In a full system, this might use a lighter LLM to summarize the chain.
        # Here we structure it deterministically.
        supervisor_step = agent_steps[-1]
        narrative = (
            f"Decision reached with {score.total_score:.1f} score (Confidence: {score.confidence_interval}). "
            f"Primary reason: {supervisor_step.conclusion.get('final_decision', 'See details')}. "
            f"Key evidence: {', '.join(supervisor_step.evidence_used)}."
        )

        return AuditLog(
            decision_id=decision_id,
            inputs_used=traces,
            agent_chain=agent_steps,
            score_details=score,
            final_narrative=narrative
        )

    def generate_explanation(self, audit: AuditLog) -> DecisionExplanation:
        """
        Convert full audit log into the user-facing lightweight explanation schema.
        """
        weights = {c.name: c.value for c in audit.score_details.components}
        
        # Mean confidence from interval
        conf_mean = sum(audit.score_details.confidence_interval) / 2.0 / 100.0
        
        return DecisionExplanation(
            summary=audit.final_narrative,
            factor_weights=weights,
            confidence_score=conf_mean
        )
