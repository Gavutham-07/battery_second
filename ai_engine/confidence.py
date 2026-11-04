from typing import Dict, Any, Tuple


def evaluate_confidence_and_quality(
    features: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Computes an explainable assessment confidence score (0.0 to 100.0%)
    and diagnostic data quality indicators.
    """
    if not features or features.get("sample_count", 0) < 2:
        return 0.0, {
            "sample_count": 0,
            "missing_values": 0,
            "thermal_variance": 0.0,
            "data_sufficiency": "INSUFFICIENT"
        }

    sample_count = features.get("sample_count", 0)
    duration_sec = features.get("duration_sec", 0.0)
    missing_intervals = features.get("missing_intervals", 0)
    thermal_variance = features.get("thermal_variance", 0.0)

    # 1. Density Score (up to 40 pts)
    # Target: at least 20 samples for high confidence
    density_score = min(40.0, (sample_count / 20.0) * 40.0)

    # 2. Duration Score (up to 40 pts)
    # Target: at least 20 seconds of continuous measurement
    duration_score = min(40.0, (duration_sec / 20.0) * 40.0)

    # 3. Continuity Penalty (deduct up to 30 pts for missing timestamp intervals)
    continuity_penalty = min(30.0, missing_intervals * 10.0)

    # 4. Thermal Stability Score (up to 20 pts)
    # Excessive thermal variance (> 5.0) indicates noisy/failing sensor
    thermal_penalty = min(20.0, thermal_variance * 2.0)
    thermal_score = max(0.0, 20.0 - thermal_penalty)

    # Composite Confidence Calculation
    raw_confidence = (density_score + duration_score + thermal_score) - continuity_penalty
    confidence = round(max(5.0, min(100.0, raw_confidence)), 1)

    data_quality = {
        "sample_count": sample_count,
        "missing_values": missing_intervals,
        "thermal_variance": thermal_variance,
        "data_sufficiency": "SATISFACTORY" if confidence >= 60.0 else "SPARSE"
    }

    return confidence, data_quality

