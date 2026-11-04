"""REVOLT Member 3 — Integration Engine.

File: backend/engine.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Main Member 3 integration pipeline.
- Coordinates:
    1. Telemetry validation & feature extraction (assessment.py)
    2. Deterministic safety screening (safety.py)
    3. Evidence-based confidence evaluation (confidence.py)
    4. SOH model applicability & offline research benchmark (NASA XGBoost)
    5. Multi-Objective Battery Circularity Optimisation (mbco.py)
    6. Indicative route-wise valuation (valuation.py)
    7. Scenario-based lifetime projections (lifetime.py)
- Strictly enforces research constraints and decision precedence.
- Returns clean, fully structured, and JSON-serializable assessment reports.
"""

from __future__ import annotations

import json
import math
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.ai.assessment import assess_telemetry, _to_python_type
from backend.ai.safety import screen_battery_safety
from backend.ai.confidence import evaluate_assessment_confidence
from backend.ai.mbco import run_mbco_engine
from backend.ai.valuation import calculate_route_valuation
from backend.ai.lifetime import calculate_lifetime_scenarios

_NASA_MODEL_CACHE: Optional[Any] = None
_NASA_COLS_CACHE: Optional[List[str]] = None


def _get_artifacts_dir() -> Path:
    """Resolve research artifacts path safely."""
    current_file = Path(__file__).resolve()
    target = current_file.parent / "models" / "research_artifacts"
    if target.exists():
        return target
    cwd_target = Path.cwd() / "backend" / "models" / "research_artifacts"
    if cwd_target.exists():
        return cwd_target
    return target


def load_nasa_xgboost_model() -> Optional[Any]:
    """Load the NASA XGBoost SOH benchmark model if available."""
    global _NASA_MODEL_CACHE
    if _NASA_MODEL_CACHE is not None:
        return _NASA_MODEL_CACHE

    model_path = _get_artifacts_dir() / "soh_xgboost_nasa.pkl"
    if model_path.exists():
        try:
            with open(model_path, "rb") as f:
                _NASA_MODEL_CACHE = pickle.load(f)
            return _NASA_MODEL_CACHE
        except Exception:
            return None
    return None


def load_nasa_feature_columns() -> List[str]:
    """Load the feature column names expected by the NASA XGBoost model."""
    global _NASA_COLS_CACHE
    if _NASA_COLS_CACHE is not None:
        return _NASA_COLS_CACHE

    cols_path = _get_artifacts_dir() / "soh_feature_columns.pkl"
    if cols_path.exists():
        try:
            with open(cols_path, "rb") as f:
                _NASA_COLS_CACHE = pickle.load(f)
            return _NASA_COLS_CACHE
        except Exception:
            pass

    # Default fallback list based on research schema
    _NASA_COLS_CACHE = [
        "voltage_mean", "voltage_min", "voltage_max", "voltage_std",
        "current_mean", "current_min", "current_max", "current_std",
        "temperature_mean", "temperature_max", "temperature_std",
        "discharge_duration_s"
    ]
    return _NASA_COLS_CACHE


def predict_nasa_offline_soh(basic_stats: Dict[str, Any]) -> Optional[float]:
    """Offline research benchmark inference.

    CRITICAL: Only invoked when telemetry contains a full constant-current
    discharge cycle matching NASA test protocols (~3000s, ~2A CC).
    Never invoked for short-duration pulse readings.
    """
    model = load_nasa_xgboost_model()
    if model is None:
        return None

    cols = load_nasa_feature_columns()
    # Map basic stats to NASA feature columns
    stats_map = dict(basic_stats)
    if "duration_s" in stats_map and "discharge_duration_s" not in stats_map:
        stats_map["discharge_duration_s"] = stats_map["duration_s"]

    # Verify all required features exist
    if not all(c in stats_map and stats_map[c] is not None for c in cols):
        return None

    try:
        import pandas as pd
        feat_df = pd.DataFrame([[stats_map[c] for c in cols]], columns=cols)
        pred_soh = model.predict(feat_df)[0]
        return float(pred_soh)
    except Exception:
        return None


def evaluate_battery(
    readings: Any,
    chemistry: str = "NMC",
    rated_capacity_ah: float = 2.5,
    nominal_voltage_v: float = 3.7,
    bms_warnings: Optional[List[str]] = None,
    custom_safety_thresholds: Optional[Dict[str, float]] = None,
    valuation_config: Optional[Dict[str, Any]] = None,
    lifetime_config: Optional[Dict[str, Any]] = None,
    application_policies: Optional[Dict[str, Dict[str, Any]]] = None,
    objective_weights: Optional[Dict[str, float]] = None,
    operating_temperature_c: Optional[float] = None,
    depth_of_discharge_pct: Optional[float] = None,
    daily_operating_hours: Optional[float] = None,
    soh_override: Optional[float] = None,
    pack_cell_count: int = 1,
) -> Dict[str, Any]:
    """Execute end-to-end Member 3 assessment and circularity evaluation.

    Pipeline:
    1. Validate readings and extract features.
    2. Run deterministic safety screening.
    3. Run evidence-based confidence evaluation.
    4. Determine SOH applicability (offline NASA model or protocol status).
    5. Run MBCO circularity decision engine.
    6. Calculate indicative route-wise valuation.
    7. Calculate scenario-based lifetime projections.
    8. Return comprehensive JSON-serializable assessment report.
    """
    # 1. Telemetry Assessment & Feature Extraction
    assessment_data = assess_telemetry(
        readings=readings,
        chemistry=chemistry,
        rated_capacity_ah=rated_capacity_ah,
        nominal_voltage_v=nominal_voltage_v,
    )

    # 2. Safety Screening
    safety_result = screen_battery_safety(
        readings_or_assessment=assessment_data,
        chemistry=chemistry,
        custom_thresholds=custom_safety_thresholds,
        bms_warnings=bms_warnings,
    )

    # 3. SOH Evaluation & Protocol Applicability
    # Research rule: Short pulse readings return 'not_available_for_this_protocol'.
    extracted = assessment_data.get("extracted_features", {})
    basic_stats = extracted.get("basic_stats")
    soh_info = assessment_data.get("soh_assessment", {})

    effective_soh: Optional[float] = None
    if soh_override is not None:
        effective_soh = float(soh_override)
        soh_info["status"] = "soh_override_provided"
        soh_info["soh_pct"] = effective_soh
        soh_info["message"] = f"SOH provided explicitly via override ({effective_soh:.1f}%)."
    elif soh_info.get("status") == "model_compatible_full_discharge" and basic_stats:
        pred_soh = predict_nasa_offline_soh(basic_stats)
        if pred_soh is not None:
            effective_soh = round(pred_soh, 2)
            soh_info["status"] = "predicted_offline_nasa_benchmark"
            soh_info["soh_pct"] = effective_soh
            soh_info["message"] = (
                "Predicted using offline NASA XGBoost research benchmark model "
                "(full constant-current discharge profile)."
            )
        else:
            soh_info["status"] = "model_inference_failed"
            soh_info["message"] = "Full discharge detected but model inference could not be completed."
    else:
        # Default for ESP32 pulse protocol:
        soh_info["status"] = "not_available_for_this_protocol"
        soh_info["soh_pct"] = None
        effective_soh = None

    if effective_soh is not None and effective_soh > 0:
        soh_info["remaining_capacity_ah"] = round(rated_capacity_ah * (effective_soh / 100.0), 3)

    # 4. Confidence Assessment
    confidence_result = evaluate_assessment_confidence(
        assessment_data=assessment_data,
        soh_prediction=effective_soh,
    )

    # 5. Indicative Valuation
    valuation_result = calculate_route_valuation(
        soh_pct=effective_soh,
        rated_capacity_ah=rated_capacity_ah,
        nominal_voltage_v=nominal_voltage_v,
        valuation_config=valuation_config,
        pack_cell_count=pack_cell_count,
    )

    # Extract economic valuations for MBCO if configured
    econ_for_mbco = None
    if valuation_result.get("status") == "configured":
        econ_for_mbco = valuation_result.get("route_valuations")

    # 6. MBCO Decision Engine
    mbco_result = run_mbco_engine(
        assessment_data=assessment_data,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=effective_soh,
        economic_valuations=econ_for_mbco,
        application_policies=application_policies,
        objective_weights=objective_weights,
    )

    # 7. Scenario-Based Lifetime Projection
    target_profile = mbco_result.get("recommended_pathway") or "solar_storage"
    lifetime_result = calculate_lifetime_scenarios(
        soh_pct=effective_soh,
        daily_operating_hours=daily_operating_hours,
        operating_temperature_c=operating_temperature_c,
        depth_of_discharge_pct=depth_of_discharge_pct,
        application_profile=target_profile,
        lifetime_config=lifetime_config,
    )

    # 8. Assemble Master Assessment Report
    report = {
        "assessment_id": f"REV-{assessment_data.get('battery_id', 'BAT')}-{int(math.floor(1000 * (basic_stats.get('duration_s', 0) if basic_stats else 0)))}",
        "battery_id": assessment_data.get("battery_id", "UNKNOWN"),
        "chemistry": assessment_data.get("chemistry", "UNKNOWN"),
        "rated_capacity_ah": rated_capacity_ah,
        "nominal_voltage_v": nominal_voltage_v,
        "pack_cell_count": pack_cell_count,
        "data_quality": assessment_data.get("data_quality"),
        "features": assessment_data.get("extracted_features"),
        "safety_screening": safety_result,
        "confidence_evaluation": confidence_result,
        "soh_evaluation": soh_info,
        "mbco_circularity_decision": mbco_result,
        "indicative_valuation": valuation_result,
        "lifetime_scenarios": lifetime_result,
        "summary": {
            "final_circularity_state": mbco_result.get("final_decision"),
            "recommended_pathway": mbco_result.get("recommended_pathway"),
            "is_safe_for_second_life": safety_result.get("is_safe_for_second_life"),
            "confidence_level": confidence_result.get("confidence_level"),
            "effective_soh_pct": effective_soh,
            "decision_precedence_applied": mbco_result.get("decision_precedence_applied"),
        },
        "metadata": {
            "module_owner": "Member 3 (AI, Assessment, Confidence, Safety and MBCO)",
            "integration_status": "PROVISIONAL_INTERFACE_READY_FOR_MEMBER_2_REVIEW",
            "disclaimer": (
                "REVOLT Member 3 Decision Engine output is provisional decision-support information. "
                "Hardware sensor data, physical cell teardowns, and certified electrical safety standards "
                "must be validated before deployment."
            ),
        },
    }

    return _to_python_type(report)
