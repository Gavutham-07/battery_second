from typing import List, Dict, Any
from ai_engine.features import extract_features
from ai_engine.safety_screener import screen_battery_safety
from ai_engine.soh_estimator import estimate_soh_and_capacity
from ai_engine.confidence import evaluate_confidence_and_quality
from ai_engine.mbco_solver import solve_mbco


def evaluate_battery(
    telemetry_records: List[Dict[str, Any]],
    battery_metadata: Dict[str, Any],
    mode: str = "LIVE"
) -> Dict[str, Any]:
    """
    Main evaluation entrypoint coordinating feature extraction, safety screening,
    decoupled SOH/capacity estimation, confidence calculation, safety precedence gating,
    and Multi-Objective Battery Circularity Optimisation (MBCO).
    """
    battery_id = battery_metadata.get("battery_id", "UNKNOWN-BATTERY")
    chemistry = battery_metadata.get("chemistry", "LFP")
    rated_capacity_ah = float(battery_metadata.get("rated_capacity_ah", 2.5))

    # 1. Feature Extraction
    features = extract_features(telemetry_records)

    # 2. Safety Screening (Safety Precedence)
    safety_status, safety_flags = screen_battery_safety(features, chemistry)

    # 3. Decoupled SOH & Available Capacity
    soh, available_capacity_ah = estimate_soh_and_capacity(features, rated_capacity_ah, chemistry)

    # 4. Confidence & Data Quality Evaluation
    confidence, data_quality = evaluate_confidence_and_quality(features)

    # 5. Enforce Safety Precedence Rule for Decision State
    if safety_status == "FAILED":
        decision = "RECYCLE"
    elif safety_status == "WARNING":
        decision = "QUARANTINE"
    elif safety_status == "UNKNOWN" or confidence < 60.0:
        decision = "FURTHER_TESTING"
    else:  # safety_status == "PASSED" and confidence >= 60.0
        if soh is not None and soh >= 80.0:
            decision = "CONTINUE_EV"
        elif soh is not None and soh >= 60.0:
            decision = "SECOND_LIFE_STORAGE"
        else:
            decision = "RECYCLE"

    # 6. Multi-Objective Battery Circularity Optimisation (MBCO)
    mbco_recommendations = solve_mbco(
        soh=soh if soh is not None else 0.0,
        available_capacity_ah=available_capacity_ah if available_capacity_ah is not None else 0.0,
        safety_status=safety_status,
        confidence=confidence,
        estimated_ir_ohm=features.get("estimated_ir_ohm", 0.040)
    )

    return {
        "battery_id": battery_id,
        "soh": soh,
        "available_capacity_ah": available_capacity_ah,
        "safety_status": safety_status,
        "confidence": confidence,
        "decision": decision,
        "mode": mode,
        "data_quality": data_quality,
        "safety_flags": safety_flags,
        "mbco_recommendations": mbco_recommendations
    }
