"""REVOLT Member 3 — Assessment Confidence Module.

Module: backend/ai/confidence.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Evaluate evidence-based confidence of telemetry, extracted features, and model applicability.
- Incorporate NASA LOBO validation metadata (q90 absolute residual ~6.4053 SOH percentage points).
- Detect out-of-training-range inputs against NASA feature distributions.
- Integrate Isolation Forest distribution shift detection (clearly explaining it is not a safety certification tool).
- Produce transparent confidence scores, levels, reasons, limitations, and further testing recommendations.
- Ensure all outputs are strictly JSON-serializable (native Python types).
"""

from __future__ import annotations

import math
import os
import pickle
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib

from backend.ai.assessment import _to_python_type


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class ConfidenceStatus(str, Enum):
    CONFIDENCE_SUFFICIENT = "CONFIDENCE_SUFFICIENT"
    CONFIDENCE_LIMITED = "CONFIDENCE_LIMITED"
    CONFIDENCE_INSUFFICIENT = "CONFIDENCE_INSUFFICIENT"


_METADATA_CACHE: Optional[Dict[str, Any]] = None
_ISO_FOREST_CACHE: Optional[Any] = None


def _get_artifacts_dir() -> Path:
    """Find research artifacts directory safely across execution environments."""
    current_file = Path(__file__).resolve()
    # Typical path: backend/ai/confidence.py -> backend/models/research_artifacts
    target = current_file.parent.parent / "models" / "research_artifacts"
    if target.exists():
        return target
    # Fallback to current working directory
    cwd_target = Path.cwd() / "backend" / "models" / "research_artifacts"
    if cwd_target.exists():
        return cwd_target
    return target


def load_nasa_confidence_metadata() -> Optional[Dict[str, Any]]:
    """Load provisional LOBO uncertainty and feature bounds metadata."""
    global _METADATA_CACHE
    if _METADATA_CACHE is not None:
        return _METADATA_CACHE

    meta_path = _get_artifacts_dir() / "nasa_confidence_metadata.pkl"
    if meta_path.exists():
        try:
            with open(meta_path, "rb") as f:
                _METADATA_CACHE = pickle.load(f)
            return _METADATA_CACHE
        except Exception:
            return None
    return None


def load_nasa_isolation_forest() -> Optional[Any]:
    """Load Isolation Forest distribution-shift detector."""
    global _ISO_FOREST_CACHE
    if _ISO_FOREST_CACHE is not None:
        return _ISO_FOREST_CACHE

    iso_path = _get_artifacts_dir() / "nasa_isolation_forest.pkl"
    if iso_path.exists():
        try:
            _ISO_FOREST_CACHE = joblib.load(iso_path)
            return _ISO_FOREST_CACHE
        except Exception:
            return None
    return None


def check_out_of_range_features(
    features: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], int]:
    """Identify features outside NASA training distribution bounds."""
    if metadata is None:
        metadata = load_nasa_confidence_metadata()
    if not metadata or "feature_min" not in metadata or "feature_max" not in metadata:
        return [], 0

    f_min = metadata["feature_min"]
    f_max = metadata["feature_max"]
    out_of_range: List[str] = []

    for feat_name, val in features.items():
        if val is None or not isinstance(val, (int, float)):
            continue
        if feat_name in f_min and feat_name in f_max:
            low = f_min[feat_name]
            high = f_max[feat_name]
            if val < low or val > high:
                out_of_range.append(f"{feat_name} ({val:.3f} outside [{low:.3f}, {high:.3f}])")

    return out_of_range, len(out_of_range)


def evaluate_assessment_confidence(
    assessment_data: Dict[str, Any],
    soh_prediction: Optional[float] = None,
    protocol_type: str = "auto",
) -> Dict[str, Any]:
    """Evaluate evidence-based confidence across telemetry, features, and model applicability.

    Rules:
    - High confidence cannot override critical safety flags.
    - Confidence score is an evidence index [0.0 - 1.0], not a calibrated probability.
    - Anomaly detection checks distribution shift; never classifies battery as unsafe.
    """
    reasons: List[str] = []
    limitations: List[str] = [
        "Provisional uncertainty estimate from only three independent training batteries (B0005, B0006, B0007). "
        "Not guaranteed statistical coverage for arbitrary operational profiles."
    ]

    metadata = load_nasa_confidence_metadata()
    q90_error = metadata.get("q90_absolute_error", 6.4053) if metadata else 6.4053

    # 1. Inspect Data Quality
    quality = assessment_data.get("data_quality", {})
    q_status = quality.get("status", "UNKNOWN")
    valid_readings = quality.get("valid_readings", 0)
    total_readings = quality.get("total_readings", 0)
    invalid_count = quality.get("invalid_readings", 0)
    missing_count = quality.get("missing_readings", 0)

    score_components: List[float] = []

    if q_status == "EMPTY" or total_readings == 0:
        return _to_python_type({
            "confidence_score": 0.0,
            "confidence_level": ConfidenceLevel.VERY_LOW.value,
            "confidence_status": ConfidenceStatus.CONFIDENCE_INSUFFICIENT.value,
            "further_testing_required": True,
            "reasons": ["Telemetry data is empty."],
            "limitations": limitations,
            "distribution_shift_detected": False,
            "out_of_range_features": [],
            "out_of_range_feature_count": 0,
            "prediction_interval": None,
        })

    # Completeness sub-score (0.0 to 0.30)
    # Complete pulse sequence guarantees protocol stage adequacy
    extracted_early = assessment_data.get("extracted_features", {})
    pulse_early = extracted_early.get("pulse_features", {}) if extracted_early else {}

    if pulse_early and pulse_early.get("complete_pulse_sequence"):
        sample_adequacy = 1.0
    else:
        sample_adequacy = min(1.0, valid_readings / 10.0)

    valid_ratio = valid_readings / max(1, total_readings)
    completeness_score = 0.30 * valid_ratio * sample_adequacy

    if invalid_count > 0 or missing_count > 0:
        completeness_score *= 0.7
        reasons.append(f"Data quality degraded: {missing_count} missing, {invalid_count} invalid records.")
    elif valid_readings < 5:
        reasons.append(f"Very limited telemetry: only {valid_readings} sample(s) observed.")
        limitations.append("Insufficient temporal samples to evaluate dynamic stability.")
    else:
        reasons.append("Sensor data completeness is high with zero missing or invalid records.")
    score_components.append(completeness_score)

    # Feature availability sub-score (0.0 to 0.30)
    extracted = assessment_data.get("extracted_features", {})
    pulse_feats = extracted.get("pulse_features", {})
    basic_stats = extracted.get("basic_stats")

    feature_score = 0.0
    if basic_stats:
        feature_score += 0.10
    if pulse_feats and pulse_feats.get("complete_pulse_sequence"):
        feature_score += 0.20
        reasons.append("Complete pulse sequence (rest, 0.5C, 1C) successfully extracted.")
    elif pulse_feats and pulse_feats.get("pulse_quality") == "partial":
        feature_score += 0.10
        reasons.append("Partial pulse sequence extracted. Higher-current steps missing.")
        limitations.append("Incomplete pulse protocol reduces resistance estimation fidelity.")
    else:
        reasons.append("Pulse response features unavailable or insufficient.")
        limitations.append("Pulse-based apparent resistance could not be extracted.")
    score_components.append(feature_score)

    # Protocol & Model Applicability sub-score (0.0 to 0.25)
    soh_info = assessment_data.get("soh_assessment", {})
    soh_status = soh_info.get("status", "not_available_for_this_protocol")

    protocol_score = 0.0
    distribution_shift = False
    out_of_range_list: List[str] = []

    if soh_status == "model_compatible_full_discharge":
        protocol_score += 0.25
        reasons.append("Measurement protocol matches NASA full-discharge benchmark.")

        # Check out-of-range features if basic stats exist
        if basic_stats:
            out_of_range_list, _ = check_out_of_range_features(basic_stats, metadata)
            if out_of_range_list:
                protocol_score -= min(0.15, len(out_of_range_list) * 0.03)
                reasons.append(f"{len(out_of_range_list)} feature(s) fall outside NASA training bounds.")

        # Check anomaly detector (Isolation Forest)
        iso_model = load_nasa_isolation_forest()
        if iso_model is not None and basic_stats:
            try:
                # Features matching NASA schema
                feat_cols = metadata.get("features", []) if metadata else []
                if feat_cols and all(col in basic_stats for col in feat_cols):
                    sample_vals = [[basic_stats[col] for col in feat_cols]]
                    pred = iso_model.predict(sample_vals)[0]
                    if pred == -1:
                        distribution_shift = True
                        reasons.append("Isolation Forest detected distribution shift relative to training baseline.")
                        limitations.append(
                            "Anomaly detected: distribution shift observed. "
                            "Note: Isolation Forest is an anomaly detection tool, not a battery safety certification tool."
                        )
            except Exception:
                pass
    else:
        protocol_score += 0.05
        reasons.append(
            "Short-duration ESP32 pulse protocol is incompatible with NASA full-discharge XGBoost model. "
            "Offline benchmark model inapplicable."
        )
        limitations.append("Direct full-cycle SOH inference unavailable for pulse protocol.")
    score_components.append(max(0.0, protocol_score))

    # Battery Metadata Completeness (0.0 to 0.15)
    meta_score = 0.0
    b_id = assessment_data.get("battery_id")
    chem = assessment_data.get("chemistry")
    rated_cap = assessment_data.get("rated_capacity_ah")

    if b_id and b_id != "UNKNOWN":
        meta_score += 0.05
    if chem and chem != "UNKNOWN":
        meta_score += 0.05
        reasons.append(f"Chemistry identified as {chem}.")
    else:
        reasons.append("Battery chemistry is UNKNOWN; limits cannot be verified.")
        limitations.append("Unknown chemistry prevents validated threshold comparisons.")
    if rated_cap and rated_cap > 0:
        meta_score += 0.05
    score_components.append(meta_score)

    # Final Confidence Score Calculation
    raw_confidence = sum(score_components)
    confidence_score = round(min(1.0, max(0.0, raw_confidence)), 3)

    # Determine Confidence Level & Status
    if confidence_score >= 0.75 and q_status == "PASSED":
        level = ConfidenceLevel.HIGH.value
        status = ConfidenceStatus.CONFIDENCE_SUFFICIENT.value
        further_testing = False
    elif confidence_score >= 0.50:
        level = ConfidenceLevel.MEDIUM.value
        status = ConfidenceStatus.CONFIDENCE_LIMITED.value
        further_testing = False if (pulse_feats and pulse_feats.get("complete_pulse_sequence")) else True
    elif confidence_score >= 0.25:
        level = ConfidenceLevel.LOW.value
        status = ConfidenceStatus.CONFIDENCE_LIMITED.value
        further_testing = True
    else:
        level = ConfidenceLevel.VERY_LOW.value
        status = ConfidenceStatus.CONFIDENCE_INSUFFICIENT.value
        further_testing = True

    # Prediction Interval (Provisional)
    pred_interval = None
    if soh_prediction is not None and not math.isnan(soh_prediction):
        half_w = round(q90_error, 2)
        pred_interval = {
            "predicted_soh_pct": round(float(soh_prediction), 2),
            "provisional_lower_bound_pct": round(max(0.0, float(soh_prediction) - half_w), 2),
            "provisional_upper_bound_pct": round(min(100.0, float(soh_prediction) + half_w), 2),
            "provisional_half_width_pct": half_w,
            "disclaimer": "Provisional 90th-percentile LOBO residual interval (±6.41%). Not a guaranteed prediction interval.",
        }

    out = {
        "confidence_score": confidence_score,
        "confidence_level": level,
        "confidence_status": status,
        "further_testing_required": further_testing,
        "reasons": reasons,
        "limitations": limitations,
        "distribution_shift_detected": distribution_shift,
        "out_of_range_features": out_of_range_list,
        "out_of_range_feature_count": len(out_of_range_list),
        "prediction_interval": pred_interval,
    }

    return _to_python_type(out)
