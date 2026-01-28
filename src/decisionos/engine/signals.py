import math
from typing import List, Dict, Tuple
from datetime import timedelta
from collections import defaultdict
from decisionos.engine.normalizer import NormalizedData

class SignalEngine:
    """
    Deterministic Signal Extraction Engine.
    
    Why Deterministic Preprocessing?
    1.  **Safety & Reliability**: LLMs can hallucinate patterns. Hard-coded statistical rules (z-scores,
        moving averages) provide a ground-truth baseline that cannot be hallucinated.
    2.  **Cost Efficiency**: Filtering noise and clustering signals *before* calling an LLM reduces
        token usage significantly.
    3.  **Auditability**: When a decision is flagged as an "anomaly", we can point to specific math
        (e.g., "3 sigma deviation") rather than "the AI felt it was weird".
    """

    def __init__(self, time_window_minutes: int = 60):
        self.window = timedelta(minutes=time_window_minutes)

    def detect_anomalies(self, data_points: List[NormalizedData]) -> List[NormalizedData]:
        """
        Flag outliers using statistical deviation (Z-Score) on normalized priority.
        
        Trade-off: Recall vs Precision
        - We prioritize **Precision** here (3-sigma rule).
        - Why? In operational decision systems, false positives (alert fatigue) are deadly.
          We only want to flag true statistical outliers as critical signals to downstream/LLM layers.
          It is better to miss a marginal case than to flood the decision engine with noise.
        """
        if len(data_points) < 5:
            return data_points  # Not enough data for stats

        scores = [d.normalized_priority for d in data_points]
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return data_points

        for point in data_points:
            z_score = (point.normalized_priority - mean) / std_dev
            # Tag metadata if anomalous
            if abs(z_score) > 3:  # 3-sigma rule
                point.feature_vector["is_anomaly"] = 1.0
                point.feature_vector["anomaly_z_score"] = z_score
            else:
                 point.feature_vector["is_anomaly"] = 0.0
        
        return data_points

    def cluster_signals(self, inputs: List[NormalizedData]) -> List[List[NormalizedData]]:
        """
        Group related signals by source type and time proximity.
        
        Algorithm:
        - Bucketing by `canonical_type`
        - Temporal sliding window clustering
        
        Why not Semantic Clustering (Vectors) here?
        - We want clear, explainable grouping logic (e.g., "all server metrics from 10:00-10:15").
        - Semantic clustering is added *later* by the LLM/Embedding layer for vague text correlation.
          This layer handles the hard, obvious logical groupings first.
        """
        clusters: Dict[str, List[NormalizedData]] = defaultdict(list)
        
        # 1. Hard grouping by canonical type (don't mix apples and oranges yet)
        grouped_by_type: Dict[str, List[NormalizedData]] = defaultdict(list)
        for item in inputs:
            grouped_by_type[item.canonical_type].append(item)
            
        final_clusters = []
        
        # 2. Temporal Clustering within types
        for _, items in grouped_by_type.items():
            # Sort by time
            items.sort(key=lambda x: x.timestamp)
            
            current_cluster = []
            if not items:
                continue
                
            current_start = items[0].timestamp
            
            for item in items:
                if item.timestamp - current_start <= self.window:
                    current_cluster.append(item)
                else:
                    # Close cluster and start new one
                    final_clusters.append(current_cluster)
                    current_cluster = [item]
                    current_start = item.timestamp
            
            if current_cluster:
                final_clusters.append(current_cluster)
                
        return final_clusters

    def detect_trends(self, metrics: List[NormalizedData]) -> Dict[str, str]:
        """
        Simple linear trend detection on metric streams.
        
        Returns:
            Dict mapping source to trend direction ('rising', 'falling', 'stable')
        """
        trends = {}
        # Group by source
        by_source: Dict[str, List[float]] = defaultdict(list)
        for m in metrics:
            if "metric:" in m.source:
                by_source[m.source].append(m.normalized_priority)
        
        for source, values in by_source.items():
            if len(values) < 3:
                trends[source] = "insufficient_data"
                continue
                
            # Simple slope calculation (start vs end average)
            # Robust extraction > Complex fitting for this stage
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            last_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            if last_half > first_half * 1.1:
                trends[source] = "rising"
            elif last_half < first_half * 0.9:
                trends[source] = "falling"
            else:
                trends[source] = "stable"
                
        return trends
