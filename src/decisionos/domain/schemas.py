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

class DecisionExplanation(BaseModel):
    """
    Explanation for a generated decision.
    """
    summary: str
    factor_weights: Dict[str, float]
    confidence_score: float = Field(ge=0.0, le=1.0)

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
