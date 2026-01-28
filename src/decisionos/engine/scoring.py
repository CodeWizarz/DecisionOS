from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ScoreComponent(BaseModel):
    name: str # e.g. "Revenue Impact", "Customer Sentiment", "Operational Risk"
    value: float # 0.0 to 1.0 (Normalized)
    weight: float # Importance of this component
    uncertainty_flag: bool = False # If true, value is low-confidence

class DecisionScore(BaseModel):
    """
    Final calibrated score for a decision.

    Why Confidence is a First-Class Output:
    - AI is probabilistic, not deterministic. Hiding this reality creates false certainty.
    - Executives behave differently when "80% confident" vs "99% confident".
    - Low confidence triggers "Human-in-the-loop" review, preventing automated disasters.

    Why Executives Need Calibrated Decisions:
    - "Calibration" means 80% confidence -> correct 8 out of 10 times.
    - Uncalibrated "high confidence" (overconfidence) leads to catastrophic bets.
    - Honest uncertainty flags allow executives to hedge risks appropriately.
    """
    total_score: float = Field(..., description="Weighted sum of impact components (0-100)")
    confidence_interval: List[float] = Field(..., description="[Low, High] estimate of impact")
    uncertainty_sources: List[str] = Field(default_factory=list, description="Why are we unsure?")
    components: List[ScoreComponent]


class ScoringEngine:
    def calculate_score(self, features: Dict[str, float], agent_confidence: float) -> DecisionScore:
        """
        Derive a calibrated decision score from feature vectors and agent reasoning.
        """
        
        # 1. Component Extraction (Impact Estimation)
        # In a real system, these would be sophisticated regression models or value functions.
        # Here we use heuristic weights based on normalized feature vectors.
        
        revenue_impact = features.get("commercial_value", 0.0)
        urchin_impact = features.get("urgency", 0.0)
        risk_level = features.get("market_volatility", 0.0)

        components = [
            ScoreComponent(name="Commercial Value", value=revenue_impact, weight=0.4),
            ScoreComponent(name="Urgency", value=urchin_impact, weight=0.4),
            ScoreComponent(name="Stability", value=1.0 - risk_level, weight=0.2, uncertainty_flag=risk_level > 0.7)
        ]

        # 2. Weighted Score Calculation
        raw_score = sum(c.value * c.weight for c in components)
        
        # 3. Confidence Calibration
        # We start with the Agent's reasoning confidence (semantic confidence).
        # We penalize it based on data uncertainty (risk_level).
        
        calibrated_confidence = agent_confidence * (1.0 - (risk_level * 0.5))
        
        # 4. Uncertainty Intervals
        # Lower confidence = Wider interval
        # If perfect confidence (1.0), interval width is 0.
        # If 0.5 confidence, interval is +/- 25% of score.
        margin = (1.0 - calibrated_confidence) * 0.5 # Arbitrary calibration factor
        interval_low = max(0.0, raw_score - margin)
        interval_high = min(1.0, raw_score + margin)

        # 5. Uncertainty Flags
        flags = []
        if risk_level > 0.6:
            flags.append("High Market Volatility Detected")
        if agent_confidence < 0.7:
            flags.append("Agent Reasoning Low Confidence")
        if revenue_impact == 0 and urchin_impact == 0:
            flags.append("Unknown Impact Magnitude")

        return DecisionScore(
            total_score=raw_score * 100, # Scale to 0-100 for display
            confidence_interval=[interval_low * 100, interval_high * 100],
            uncertainty_sources=flags,
            components=components
        )
