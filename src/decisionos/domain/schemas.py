from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

class DataPoint(BaseModel):
    """
    Represents a single operational data input.
    
    Why:
    - Captures raw data before processing.
    - strict validation ensures downstream quality.
    """
    id: UUID = Field(default_factory=uuid4)
    source: str = Field(..., description="Origin of the data (e.g., 'sensor_1', 'crm_api')")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(..., description="Raw JSON payload")
    
    model_config = ConfigDict(from_attributes=True)

class DecisionRequest(BaseModel):
    """
    Parameters for generating a decision.
    """
    context_id: str = Field(..., description="Identifier for the decision context")
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
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    rank: int
    content: Dict[str, Any]
    explanation: Optional[DecisionExplanation] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
