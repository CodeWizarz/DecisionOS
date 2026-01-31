from datetime import datetime
from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

# ... existing schemas ...

class DecisionRequest(BaseModel):
    """
    Parameters for generating a decision.
    """
    context_id: str = Field(..., description="Identifier for the decision context (e.g. incident_ID)")
    criteria: List[str] = Field(default_factory=list, description="Specific criteria to prioritize")

class ImpactMetrics(BaseModel):
    """
    Measurable impact estimates for the decision.
    
    Why Directional ROI?
    - Heuristics (e.g. "Saved 2 hours") are sufficient for prioritization. 
    - Precise accounting is too expensive/impossible in real-time.
    - Visibility into "Value" matters more than accounting precision at this stage.
    """
    estimated_time_saved_minutes: float = Field(..., description="Estimated engineering time saved")
    estimated_risk_reduction_score: float = Field(..., ge=0.0, le=10.0, description="Heuristic score of risk avoided (0-10)")

class DecisionExplanation(BaseModel):
    """
    Explanation for a generated decision.
    """
    summary: str
    factor_weights: Dict[str, float]
    confidence_score: float = Field(ge=0.0, le=1.0)
    impact: Optional[ImpactMetrics] = None

class Decision(BaseModel):
    """
    The output decision entity.
    """
    id: UUID
    request_id: Optional[UUID] = None
    rank: int = 0
    content: Dict[str, Any]
    explanation: Optional[DecisionExplanation] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
