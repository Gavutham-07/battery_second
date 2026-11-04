"""Automated tests for Module 2 — Safety Screening (backend/ai/safety.py)."""

import pytest
from backend.ai.safety import screen_battery_safety, SafetyState


def test_safety_clear_nominal():
    readings = [
        {"battery_id": "BAT-SAFE-1", "sec": 0.0, "v": 3.85, "i": 0.0, "t": 25.0, "event": "REST"},
        {"battery_id": "BAT-SAFE-1", "sec": 1.0, "v": 3.75, "i": -1.25, "t": 25.5, "event": "0.5C"},
        {"battery_id": "BAT-SAFE-1", "sec": 2.0, "v": 3.82, "i": 0.0, "t": 25.6, "event": "RECOVERY"},
    ]
    res = screen_battery_safety(readings, chemistry="NMC")
    assert res["safety_state"] == SafetyState.SCREENING_CLEAR.value
    assert res["is_safe_for_second_life"] is True
    assert len(res["critical_violations"]) == 0
    assert "disclaimer" in res


def test_critical_under_voltage():
    # Reading drops to 1.7V (deep discharge < 2.0V for NMC)
    readings = [
        {"battery_id": "BAT-DANG-1", "sec": 0.0, "v": 1.70, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    res = screen_battery_safety(readings, chemistry="NMC")
    assert res["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert res["is_safe_for_second_life"] is False
    assert any("under-voltage" in cv.lower() for cv in res["critical_violations"])


def test_critical_over_voltage():
    # Reading reaches 4.45V (> 4.35V critical ceiling)
    readings = [
        {"battery_id": "BAT-DANG-2", "sec": 0.0, "v": 4.45, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    res = screen_battery_safety(readings, chemistry="NMC")
    assert res["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert res["is_safe_for_second_life"] is False
    assert any("over-voltage" in cv.lower() for cv in res["critical_violations"])


def test_critical_over_temperature():
    # Reading reaches 58°C (>= 55°C critical limit)
    readings = [
        {"battery_id": "BAT-DANG-3", "sec": 0.0, "v": 3.80, "i": 0.0, "t": 58.0, "event": "REST"},
    ]
    res = screen_battery_safety(readings, chemistry="NMC")
    assert res["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert res["is_safe_for_second_life"] is False
    assert any("high temperature" in cv.lower() for cv in res["critical_violations"])


def test_critical_bms_warning():
    readings = [
        {"battery_id": "BAT-DANG-4", "sec": 0.0, "v": 3.80, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    res = screen_battery_safety(readings, chemistry="NMC", bms_warnings=["CELL_INTERNAL_SHORT_DETECTED"])
    assert res["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert res["is_safe_for_second_life"] is False
    assert any("BMS alarm" in cv for cv in res["critical_violations"])


def test_unknown_chemistry_no_silent_fallback():
    readings = [
        {"battery_id": "BAT-UNK", "sec": 0.0, "v": 3.80, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    res = screen_battery_safety(readings, chemistry="SUPER_EXOTIC_CHEM")
    assert res["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert res["is_safe_for_second_life"] is False
    assert any("Unknown or unsupported" in cv for cv in res["critical_violations"])


def test_custom_thresholds_configuration():
    # Set conservative max voltage = 4.10 V
    custom = {
        "min_voltage_critical": 2.5,
        "max_voltage_critical": 4.10,
        "max_temp_critical": 50.0,
    }
    readings = [
        {"battery_id": "BAT-CUST", "sec": 0.0, "v": 4.15, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    res = screen_battery_safety(readings, chemistry="NMC", custom_thresholds=custom)
    assert res["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert res["applied_thresholds"]["max_voltage_critical"] == 4.10
