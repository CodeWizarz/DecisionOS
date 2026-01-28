import pytest
from decisionos.engine.scoring import ScoringEngine
from decisionos.engine.signals import SignalEngine, NormalizedData
from datetime import datetime

@pytest.mark.asyncio
async def test_scoring_engine_calibration(mock_feature_vector):
    """
    Verify that high urgency + commercial value leads to a high score,
    and that volatility correctly widens the confidence interval.
    """
    engine = ScoringEngine()
    
    # Case 1: High confidence scenario
    score = engine.calculate_score(mock_feature_vector, agent_confidence=0.9)
    
    assert score.total_score > 50  # Should be reasonably high
    assert score.confidence_interval[1] - score.confidence_interval[0] < 20 # Narrow interval
    assert "High Market Volatility Detected" not in score.uncertainty_sources

    # Case 2: High volatility scenario
    volatile_features = mock_feature_vector.copy()
    volatile_features["market_volatility"] = 0.9
    
    risky_score = engine.calculate_score(volatile_features, agent_confidence=0.9)
    
    assert "High Market Volatility Detected" in risky_score.uncertainty_sources
    # Volatility should widen the interval (lower confidence)
    interval_width = risky_score.confidence_interval[1] - risky_score.confidence_interval[0]
    assert interval_width > 20 

@pytest.mark.asyncio
async def test_signal_clustering():
    """
    Verify that the signal engine groups temporally proximate events.
    """
    engine = SignalEngine(time_window_minutes=10)
    
    now = datetime.utcnow()
    
    data = [
        NormalizedData(
            source="test", timestamp=now, canonical_type="error", 
            normalized_priority=0.5, feature_vector={}, data={}
        ),
        NormalizedData(
            source="test", timestamp=now, canonical_type="error", # Same time, same type -> Cluster
            normalized_priority=0.5, feature_vector={}, data={}
        ),
        NormalizedData(
            source="test", timestamp=now, canonical_type="metric", # Diff type -> Separate
            normalized_priority=0.5, feature_vector={}, data={}
        )
    ]
    
    clusters = engine.cluster_signals(data)
    
    # Should have 2 clusters: one for 'error' (size 2) and one for 'metric' (size 1)
    assert len(clusters) == 2
    
    error_cluster = [c for c in clusters if c[0].canonical_type == "error"][0]
    assert len(error_cluster) == 2
