"""Automated tests for Module 1 — Assessment Engine (backend/ai/assessment.py)."""

import json
import pytest
from backend.ai.assessment import (
    validate_readings,
    compute_basic_statistics,
    extract_pulse_features,
    assess_telemetry,
    evaluate_battery,
)


def test_valid_sensor_readings():
    readings = [
        {"battery_id": "BAT-101", "sec": 0.0, "v": 3.85, "i": 0.0, "t": 25.0, "event": "REST"},
        {"battery_id": "BAT-101", "sec": 1.0, "v": 3.84, "i": 0.0, "t": 25.1, "event": "REST"},
        {"battery_id": "BAT-101", "sec": 2.0, "v": 3.70, "i": -1.25, "t": 25.3, "event": "0.5C"},
        {"battery_id": "BAT-101", "sec": 3.0, "v": 3.68, "i": -1.25, "t": 25.5, "event": "0.5C"},
        {"battery_id": "BAT-101", "sec": 4.0, "v": 3.50, "i": -2.50, "t": 26.0, "event": "1C"},
        {"battery_id": "BAT-101", "sec": 5.0, "v": 3.48, "i": -2.50, "t": 26.2, "event": "1C"},
        {"battery_id": "BAT-101", "sec": 6.0, "v": 3.80, "i": 0.0, "t": 26.0, "event": "RECOVERY"},
    ]

    result = evaluate_battery(readings, chemistry="NMC", rated_capacity_ah=2.5)
    assert result["battery_id"] == "BAT-101"
    assert result["chemistry"] == "NMC"
    assert result["data_quality"]["status"] == "PASSED"
    assert result["data_quality"]["valid_readings"] == 7
    assert result["data_quality"]["invalid_readings"] == 0
    assert result["extracted_features"]["basic_stats"] is not None
    assert result["extracted_features"]["basic_stats"]["sample_count"] == 7
    assert result["extracted_features"]["pulse_features"]["complete_pulse_sequence"] is True
    assert result["extracted_features"]["pulse_features"]["pulse_quality"] == "complete"
    assert result["soh_assessment"]["status"] == "not_available_for_this_protocol"


def test_empty_readings():
    result_empty_list = assess_telemetry([])
    assert result_empty_list["data_quality"]["status"] == "EMPTY"
    assert result_empty_list["extracted_features"]["basic_stats"] is None

    result_none = assess_telemetry(None)
    assert result_none["data_quality"]["status"] == "EMPTY"
    assert result_none["extracted_features"]["basic_stats"] is None


def test_missing_voltage_and_temperature():
    readings = [
        {"battery_id": "BAT-102", "sec": 0.0, "i": 0.0, "t": 25.0},  # missing v
        {"battery_id": "BAT-102", "sec": 1.0, "v": 3.80, "i": 0.0},  # missing t
        {"battery_id": "BAT-102", "sec": 2.0, "v": 3.75, "i": 0.0, "t": 25.0},  # valid
    ]
    valid, quality = validate_readings(readings)
    assert len(valid) == 1
    assert quality["missing_readings"] == 2
    assert quality["status"] == "DEGRADED"


def test_duplicate_and_non_monotonic_timestamps():
    readings = [
        {"battery_id": "BAT-103", "sec": 1.0, "v": 3.80, "i": 0.0, "t": 25.0},
        {"battery_id": "BAT-103", "sec": 1.0, "v": 3.80, "i": 0.0, "t": 25.0},  # duplicate
        {"battery_id": "BAT-103", "sec": 0.5, "v": 3.80, "i": 0.0, "t": 25.0},  # non-monotonic
    ]
    valid, quality = validate_readings(readings)
    assert quality["duplicate_timestamps"] == 1
    assert quality["non_monotonic_timestamps"] == 1
    assert quality["status"] == "DEGRADED"


def test_invalid_negative_or_extreme_values():
    readings = [
        {"sec": 0.0, "v": -1.0, "i": 0.0, "t": 25.0},   # negative voltage
        {"sec": 1.0, "v": 7.5, "i": 0.0, "t": 25.0},    # voltage > 6V
        {"sec": 2.0, "v": 3.8, "i": float("nan"), "t": 25.0},  # nan current
        {"sec": 3.0, "v": 3.8, "i": 0.0, "t": 150.0},  # extreme temp > 100
        {"sec": 4.0, "v": 3.8, "i": 0.0, "t": -60.0},  # extreme temp < -40
    ]
    valid, quality = validate_readings(readings)
    assert len(valid) == 0
    assert quality["invalid_readings"] == 5
    assert quality["status"] == "INVALID"


def test_incomplete_pulse_sequence():
    # Only rest and 0.5C, no 1C
    readings = [
        {"battery_id": "BAT-104", "sec": 0.0, "v": 4.10, "i": 0.0, "t": 25.0, "event": "REST"},
        {"battery_id": "BAT-104", "sec": 1.0, "v": 3.90, "i": -1.25, "t": 25.2, "event": "0.5C"},
    ]
    result = assess_telemetry(readings, rated_capacity_ah=2.5)
    pulse = result["extracted_features"]["pulse_features"]
    assert pulse["complete_pulse_sequence"] is False
    assert pulse["pulse_quality"] == "partial"
    assert pulse["rest_voltage_v"] == 4.10
    assert pulse["pulse_05c_voltage_mean_v"] == 3.90
    assert pulse["pulse_1c_voltage_mean_v"] is None  # Missing must remain missing
    assert pulse["pulse_1c_resistance_est_ohm"] is None


def test_apparent_resistance_calculation():
    readings = [
        {"sec": 0.0, "v": 4.00, "i": 0.0, "t": 25.0, "event": "REST"},
        {"sec": 1.0, "v": 3.80, "i": -1.0, "t": 25.0, "event": "0.5C"},
    ]
    result = assess_telemetry(readings, rated_capacity_ah=2.0)
    pulse = result["extracted_features"]["pulse_features"]
    # Drop = 4.00 - 3.80 = 0.20 V; Resistance = 0.20 / 1.0 = 0.20 Ohm
    assert pulse["pulse_05c_voltage_drop_v"] == pytest.approx(0.20, abs=1e-4)
    assert pulse["pulse_05c_resistance_est_ohm"] == pytest.approx(0.20, abs=1e-4)


def test_json_serializability():
    readings = [
        {"battery_id": "BAT-105", "sec": 0.0, "v": 3.842, "i": 0.405, "t": 29.10, "event": "RUNNING"}
    ]
    result = assess_telemetry(readings)
    json_str = json.dumps(result)
    assert json_str is not None
    loaded = json.loads(json_str)
    assert loaded["battery_id"] == "BAT-105"
