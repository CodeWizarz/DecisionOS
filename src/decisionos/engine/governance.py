from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decisionos.engine.scoring import DecisionScore

class ApprovalStatus(str, Enum):
    AUTO_APPROVED = "auto_approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"
    MANUALLY_APPROVED = "manually_approved"

class GovernancePolicy(BaseModel):
    # If score > threshold AND confidence > threshold -> Auto Approve
    auto_approve_min_score: float = 80.0
    auto_approve_min_confidence: float = 0.9
    
    # If any specific flags are present, force review regardless of score
    # e.g. "High Market Volatility Detected"
    force_review_flags: list[str] = Field(default_factory=list)

class ReviewOutcome(BaseModel):
    decision_id: str
    reviewer_id: str
    status: ApprovalStatus
    feedback_notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GovernanceEngine:
    """
    Control layer for 'Human-in-the-loop' decision making.
    
    Why Full Automation is Dangerous:
    1.  **Tail Events**: AI models are trained on historical data. They often fail catastrophically 
        in unprecedented situations (Black Swans) where human intuition is superior.
    2.  **Accountability**: An algorithm cannot be sued or fired. For high-stakes decisions, 
        a human must ultimately sign off to maintain chain of command and responsibility.
        
    Enterprise Alignment:
    - In real enterprises, junior analysts (the AI) prepare recommendations, but senior partners 
      (the Human) approve them. This class models that specific hierarchy.
    """
    
    def __init__(self, policy: GovernancePolicy):
        self.policy = policy

    def evaluate_approval(self, score: DecisionScore) -> ApprovalStatus:
        """
        Determine if a decision can proceed automatically or needs eyes on it.
        """
        
        # 1. Check for 'Kill Switch' flags
        # If the situation is known to be volatile, never auto-approve.
        for flag in score.uncertainty_sources:
            if flag in self.policy.force_review_flags:
                return ApprovalStatus.NEEDS_REVIEW

        # 2. Check thresholds
        # High Score + High Confidence = Safe to Automate
        confidence_mean = sum(score.confidence_interval) / 2.0 / 100.0  # Normalize to 0-1
        
        if (score.total_score >= self.policy.auto_approve_min_score and 
            confidence_mean >= self.policy.auto_approve_min_confidence):
            return ApprovalStatus.AUTO_APPROVED

        # Default to human review for anything mediocre or uncertain
        return ApprovalStatus.NEEDS_REVIEW

    def process_feedback(self, outcome: ReviewOutcome) -> None:
        """
        Ingest human feedback to improve future decisions.
        
        Feedback Loop:
        - If a human REJECTS a 'NEEDS_REVIEW' recommendation, we should log this 
          as a negative signal for the Ranking Agent.
        - If a human REJECTS an 'AUTO_APPROVED' decision (post-hoc), this is a 
          critical failure event that should trigger retraining.
        """
        if outcome.status == ApprovalStatus.REJECTED:
            # TODO: Emit event to 'OptimizationEngine' to penalize similar future patterns
            pass
            
        print(f"Processed feedback for {outcome.decision_id}: {outcome.status}")
