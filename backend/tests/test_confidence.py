"""Automated tests for Module 3 — Assessment Confidence (backend/ai/confidence.py)."""

import pytest
from backend.ai.assessment import assess_telemetry
from backend.ai.confidence import (
    evaluate_assessment_confidence,
    ConfidenceLevel,
    check_out_of_range_features,
    load_nasa_confidence_metadata,
)


def test_confidence_clean_telemetry():
    readings = [
        {"battery_id": "BAT-101", "sec": 0.0, "v": 3.85, "i": 0.0, "t": 25.0, "event": "REST"},
        {"battery_id": "BAT-101", "sec": 1.0, "v": 3.84, "i": 0.0, "t": 25.1, "event": "REST"},
        {"battery_id": "BAT-101", "sec": 2.0, "v": 3.70, "i": -1.25, "t": 25.3, "event": "0.5C"},
        {"battery_id": "BAT-101", "sec": 3.0, "v": 3.68, "i": -1.25, "t": 25.5, "event": "0.5C"},
        {"battery_id": "BAT-101", "sec": 4.0, "v": 3.50, "i": -2.50, "t": 26.0, "event": "1C"},
        {"battery_id": "BAT-101", "sec": 5.0, "v": 3.48, "i": -2.50, "t": 26.2, "event": "1C"},
        {"battery_id": "BAT-101", "sec": 6.0, "v": 3.80, "i": 0.0, "t": 26.0, "event": "RECOVERY"},
    ]
    assessment = assess_telemetry(readings, chemistry="NMC", rated_capacity_ah=2.5)
    conf = evaluate_assessment_confidence(assessment)

    assert conf["confidence_score"] > 0.50
    assert conf["confidence_level"] in (ConfidenceLevel.HIGH.value, ConfidenceLevel.MEDIUM.value)
    assert len(conf["reasons"]) > 0
    assert len(conf["limitations"]) > 0


def test_confidence_empty_telemetry():
    assessment = assess_telemetry([])
    conf = evaluate_assessment_confidence(assessment)
    assert conf["confidence_score"] == 0.0
    assert conf["confidence_level"] == ConfidenceLevel.VERY_LOW.value
    assert conf["further_testing_required"] is True


def test_confidence_degraded_telemetry():
    # Only 1 reading without pulse
    readings = [
        {"battery_id": "BAT-102", "sec": 0.0, "v": 3.80, "i": 0.0, "t": 25.0, "event": "RUNNING"}
    ]
    assessment = assess_telemetry(readings, chemistry="UNKNOWN", rated_capacity_ah=2.5)
    conf = evaluate_assessment_confidence(assessment)
    assert conf["further_testing_required"] is True
    assert conf["confidence_score"] < 0.50


def test_out_of_range_features():
    metadata = load_nasa_confidence_metadata()
    if metadata:
        # Construct out-of-range features
        feats = {
            "voltage_mean": 5.50,  # Well above 4.2V
            "temperature_max": 75.0,  # Well above 42°C
        }
        out_list, count = check_out_of_range_features(feats, metadata)
        assert count >= 1
        assert any("voltage_mean" in item for item in out_list)


def test_provisional_prediction_interval():
    assessment = assess_telemetry([{"battery_id": "BAT-1", "sec": 0.0, "v": 3.8, "i": 0.0, "t": 25.0}])
    conf = evaluate_assessment_confidence(assessment, soh_prediction=85.0)
    interval = conf["prediction_interval"]
    assert interval is not None
    assert interval["predicted_soh_pct"] == 85.0
    # q90 is ~6.41%
    assert interval["provisional_lower_bound_pct"] == pytest.approx(85.0 - 6.41, abs=0.05)
    assert interval["provisional_upper_bound_pct"] == pytest.approx(85.0 + 6.41, abs=0.05)
