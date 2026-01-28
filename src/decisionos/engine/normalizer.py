from typing import Any, Dict, Protocol
from decisionos.domain.inputs import CustomerTicketInput, MetricInput, MarketSignalInput
from decisionos.domain.schemas import DataPoint

class NormalizedData(DataPoint):
    """
    Canonical internal representation of any input data.
    
    Why Schema Normalization Matters:
    1.  **Comparability**: Can't rank "server load" vs "customer anger" unless they share a common structure.
    2.  **Decoupling**: The Ranking Engine shouldn't know about Salesforce or Datadog APIs. It only knows 'features'.
    3.  **Data Quality**: Garbage-In-Garbage-Out (GIGO) is prevented by forcing all inputs into a strict, validated type
        on entry. If it doesn't fit the schema, it's rejected before polluting the decision logic.
    """
    canonical_type: str  # e.g. "urgent_event", "context_signal"
    normalized_priority: float = 0.0 # 0.0 to 1.0 scale
    feature_vector: Dict[str, float] # Ready for ML/Ranking

def normalize_ticket(input_data: CustomerTicketInput) -> NormalizedData:
    """
    Transforms a raw ticket into a normalized decision input.
    """
    # Map qualitative labels to quantitative scores
    priority_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
    tier_boost = {"standard": 0.0, "premium": 0.1, "enterprise": 0.2}
    
    base_score = priority_map[input_data.priority_label]
    final_score = min(1.0, base_score + tier_boost[input_data.customer_tier])
    
    return NormalizedData(
        source=f"ticket:{input_data.source_system}",
        timestamp=input_data.timestamp,
        data=input_data.model_dump(), # Keep raw data for explainability
        canonical_type="urgent_event",
        normalized_priority=final_score,
        feature_vector={
            "urgency": base_score,
            "commercial_value": tier_boost[input_data.customer_tier] * 5.0
        }
    )

def normalize_metric(input_data: MetricInput) -> NormalizedData:
    """
    Normalizes operational metrics.
    """
    # Example: Normalize CPU usage to 0-1 urgency
    normalized_val = 0.0
    if input_data.metric_name == "cpu_usage_percent":
        normalized_val = min(1.0, input_data.value / 100.0)
        
    return NormalizedData(
        source=f"metric:{input_data.source_system}",
        timestamp=input_data.timestamp,
        data=input_data.model_dump(),
        canonical_type="context_signal",
        normalized_priority=normalized_val,
        feature_vector={
            "system_stress": normalized_val,
            "impact": 0.5 # Default medium impact for infra metrics
        }
    )

def normalize_signal(input_data: MarketSignalInput) -> NormalizedData:
    """
    Normalizes generic market signals.
    """
    return NormalizedData(
        source=f"market:{input_data.source_system}",
        timestamp=input_data.timestamp,
        data=input_data.model_dump(),
        canonical_type="external_signal",
        normalized_priority=input_data.impact_score or 0.5,
        feature_vector={
            "market_volatility": input_data.impact_score or 0.0
        }
    )
