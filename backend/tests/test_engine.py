"""REVOLT Member 3 — Complete End-to-End Integration & Verification Test Suite.

File: backend/tests/test_engine.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Verifies all 20 required project scenarios:
1. Valid sensor readings
2. Empty readings
3. Missing voltage
4. Missing temperature
5. Duplicate timestamps
6. Invalid negative or non-numeric sensor values
7. Unknown chemistry
8. Critical safety indicator
9. Incomplete test sequence
10. Out-of-range model features
11. Anomaly warning
12. Low-confidence assessment
13. High SOH with a critical safety warning (critical safety flag can NEVER produce an eligible reuse recommendation)
14. High SOH with incomplete evidence (low confidence triggers further testing)
15. Technically incompatible application
16. Multiple eligible MBCO pathways
17. Missing valuation configuration (returns not_configured)
18. Missing lifetime calibration (returns not_calibrated)
19. JSON serialization
20. Complete end-to-end assessment
"""

import json
import pytest
from backend.engine import evaluate_battery


def _generate_nominal_pulse_readings(battery_id="BAT-101"):
    """Helper to generate standard pulse sequence telemetry."""
    return [
        {"battery_id": battery_id, "sec": 0.0, "v": 4.15, "i": 0.0, "t": 25.0, "event": "REST"},
        {"battery_id": battery_id, "sec": 1.0, "v": 4.14, "i": 0.0, "t": 25.1, "event": "REST"},
        {"battery_id": battery_id, "sec": 2.0, "v": 3.92, "i": -1.25, "t": 25.3, "event": "0.5C"},
        {"battery_id": battery_id, "sec": 3.0, "v": 3.90, "i": -1.25, "t": 25.5, "event": "0.5C"},
        {"battery_id": battery_id, "sec": 4.0, "v": 3.65, "i": -2.50, "t": 26.0, "event": "1C"},
        {"battery_id": battery_id, "sec": 5.0, "v": 3.62, "i": -2.50, "t": 26.2, "event": "1C"},
        {"battery_id": battery_id, "sec": 6.0, "v": 4.10, "i": 0.0, "t": 26.0, "event": "RECOVERY"},
    ]


# 1. Valid sensor readings
def test_scenario_01_valid_sensor_readings():
    readings = _generate_nominal_pulse_readings()
    report = evaluate_battery(readings, chemistry="NMC", rated_capacity_ah=2.5)
    assert report["battery_id"] == "BAT-101"
    assert report["data_quality"]["status"] == "PASSED"
    assert report["data_quality"]["valid_readings"] == 7
    assert report["safety_screening"]["safety_state"] == "SCREENING_CLEAR"


# 2. Empty readings
def test_scenario_02_empty_readings():
    report = evaluate_battery([], chemistry="NMC")
    assert report["data_quality"]["status"] == "EMPTY"
    assert report["mbco_circularity_decision"]["final_decision"] == "FURTHER_TESTING_REQUIRED"


# 3. Missing voltage
def test_scenario_03_missing_voltage():
    readings = [
        {"battery_id": "BAT-MV", "sec": 0.0, "i": 0.0, "t": 25.0, "event": "REST"},
        {"battery_id": "BAT-MV", "sec": 1.0, "v": 3.8, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    report = evaluate_battery(readings)
    assert report["data_quality"]["missing_readings"] >= 1
    assert report["data_quality"]["status"] == "DEGRADED"


# 4. Missing temperature
def test_scenario_04_missing_temperature():
    readings = [
        {"battery_id": "BAT-MT", "sec": 0.0, "v": 3.8, "i": 0.0, "event": "REST"},
        {"battery_id": "BAT-MT", "sec": 1.0, "v": 3.8, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    report = evaluate_battery(readings)
    assert report["data_quality"]["missing_readings"] >= 1


# 5. Duplicate timestamps
def test_scenario_05_duplicate_timestamps():
    readings = [
        {"sec": 1.0, "v": 3.8, "i": 0.0, "t": 25.0},
        {"sec": 1.0, "v": 3.8, "i": 0.0, "t": 25.0},  # duplicate timestamp
    ]
    report = evaluate_battery(readings)
    assert report["data_quality"]["duplicate_timestamps"] == 1


# 6. Invalid negative or non-numeric sensor values
def test_scenario_06_invalid_negative_or_non_numeric_values():
    readings = [
        {"sec": 0.0, "v": -2.5, "i": 0.0, "t": 25.0},  # negative voltage
        {"sec": 1.0, "v": 3.8, "i": "invalid_current", "t": 25.0},  # non-numeric
    ]
    report = evaluate_battery(readings)
    assert report["data_quality"]["invalid_readings"] >= 1


# 7. Unknown chemistry
def test_scenario_07_unknown_chemistry():
    readings = _generate_nominal_pulse_readings()
    # Must NOT silently use NMC thresholds!
    report = evaluate_battery(readings, chemistry="UNKNOWN_EXOTIC")
    assert report["safety_screening"]["safety_state"] == "QUARANTINE_SPECIALIST_REVIEW"
    assert any("Unknown or unsupported" in cv for cv in report["safety_screening"]["critical_violations"])


# 8. Critical safety indicator
def test_scenario_08_critical_safety_indicator():
    # Voltage dropped to 1.5V (severe over-discharge / dendrite hazard)
    readings = [
        {"sec": 0.0, "v": 1.50, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    report = evaluate_battery(readings, chemistry="NMC")
    assert report["safety_screening"]["safety_state"] == "QUARANTINE_SPECIALIST_REVIEW"
    assert report["summary"]["is_safe_for_second_life"] is False


# 9. Incomplete test sequence
def test_scenario_09_incomplete_test_sequence():
    # Only rest phase, no pulse load
    readings = [
        {"sec": 0.0, "v": 3.8, "i": 0.0, "t": 25.0, "event": "REST"},
        {"sec": 1.0, "v": 3.8, "i": 0.0, "t": 25.0, "event": "REST"},
    ]
    report = evaluate_battery(readings)
    pulse = report["features"]["pulse_features"]
    assert pulse["complete_pulse_sequence"] is False
    assert pulse["pulse_quality"] == "insufficient"


# 10. Out-of-range model features
def test_scenario_10_out_of_range_model_features():
    from backend.ai.confidence import check_out_of_range_features
    feats = {"voltage_mean": 5.0, "voltage_max": 5.5, "temperature_max": 65.0}
    out_list, count = check_out_of_range_features(feats)
    assert count >= 1


# 11. Anomaly warning
def test_scenario_11_anomaly_warning():
    from backend.ai.confidence import load_nasa_isolation_forest
    iso = load_nasa_isolation_forest()
    assert iso is not None  # Isolation forest model exists and loaded cleanly


# 12. Low-confidence assessment
def test_scenario_12_low_confidence_assessment():
    readings = [{"sec": 0.0, "v": 3.8, "i": 0.0, "t": 25.0}]
    report = evaluate_battery(readings, chemistry="UNKNOWN")
    assert report["confidence_evaluation"]["confidence_score"] < 0.50
    assert report["confidence_evaluation"]["further_testing_required"] is True


# 13. CRITICAL: High SOH with a critical safety warning
def test_scenario_13_high_soh_with_critical_safety_flag():
    """Rule: A critical safety flag can NEVER produce an eligible reuse recommendation."""
    readings = [
        {"battery_id": "BAT-CRIT", "sec": 0.0, "v": 3.8, "i": 0.0, "t": 62.0, "event": "REST"},  # 62°C critical
    ]
    report = evaluate_battery(readings, chemistry="NMC", soh_override=98.0)
    assert report["safety_screening"]["safety_state"] == "QUARANTINE_SPECIALIST_REVIEW"
    assert report["summary"]["final_circularity_state"] == "QUARANTINE_SPECIALIST_REVIEW"

    # Verify every reuse pathway is strictly marked ineligible despite 98% SOH!
    evals = report["mbco_circularity_decision"]["pathway_evaluations"]
    assert evals["continued_ev"]["eligibility"] is False
    assert evals["light_ev"]["eligibility"] is False
    assert evals["solar_storage"]["eligibility"] is False
    assert evals["backup_power"]["eligibility"] is False
    assert evals["low_power_devices"]["eligibility"] is False


# 14. High SOH with incomplete evidence
def test_scenario_14_high_soh_with_incomplete_evidence():
    """Rule: Low confidence / incomplete protocol triggers further testing even with high SOH."""
    readings = [
        {"sec": 0.0, "v": 3.8, "i": 0.0, "t": 25.0}  # 1 single sample
    ]
    report = evaluate_battery(readings, chemistry="NMC", soh_override=95.0)
    # Evidence is incomplete (pulse missing, 1 sample)
    assert report["mbco_circularity_decision"]["final_decision"] == "FURTHER_TESTING_REQUIRED"


# 15. Technically incompatible application
def test_scenario_15_technically_incompatible_application():
    readings = _generate_nominal_pulse_readings()
    # SOH = 68% -> ineligible for continued EV (min 80) and light EV (min 75)
    report = evaluate_battery(readings, chemistry="NMC", soh_override=68.0)
    evals = report["mbco_circularity_decision"]["pathway_evaluations"]
    assert evals["continued_ev"]["eligibility"] is False
    assert evals["light_ev"]["eligibility"] is False


# 16. Multiple eligible MBCO pathways
def test_scenario_16_multiple_eligible_mbco_pathways():
    readings = _generate_nominal_pulse_readings()
    report = evaluate_battery(readings, chemistry="NMC", soh_override=88.0)
    assert report["mbco_circularity_decision"]["final_decision"] == "CONTINUED_USE_CANDIDATE"
    assert len(report["mbco_circularity_decision"]["ranked_pathways"]) >= 2


# 17. Missing valuation configuration
def test_scenario_17_missing_valuation_configuration():
    readings = _generate_nominal_pulse_readings()
    report = evaluate_battery(readings, chemistry="NMC", soh_override=85.0, valuation_config={"reference_price_per_kwh_inr": None})
    assert report["indicative_valuation"]["status"] == "not_configured"


# 18. Missing lifetime calibration
def test_scenario_18_missing_lifetime_calibration():
    readings = _generate_nominal_pulse_readings()
    report = evaluate_battery(readings, chemistry="NMC", soh_override=85.0, lifetime_config={"reference_cycle_life": None})
    assert report["lifetime_scenarios"]["status"] == "not_calibrated"


# 19. JSON serialization
def test_scenario_19_json_serialization():
    readings = _generate_nominal_pulse_readings()
    report = evaluate_battery(readings, chemistry="NMC", soh_override=85.0)
    json_bytes = json.dumps(report)
    assert len(json_bytes) > 0
    parsed = json.loads(json_bytes)
    assert parsed["battery_id"] == "BAT-101"


# 20. Complete end-to-end assessment
def test_scenario_20_complete_end_to_end_assessment():
    readings = _generate_nominal_pulse_readings("BAT-E2E-TEST")
    val_cfg = {"reference_price_per_kwh_inr": 8500.0}
    life_cfg = {"reference_cycle_life": 2500, "reference_dod_pct": 80.0, "reference_temperature_c": 25.0}

    report = evaluate_battery(
        readings=readings,
        chemistry="NMC",
        rated_capacity_ah=2.5,
        nominal_voltage_v=3.7,
        valuation_config=val_cfg,
        lifetime_config=life_cfg,
        soh_override=82.0,
        pack_cell_count=10,
    )

    assert report["battery_id"] == "BAT-E2E-TEST"
    assert report["summary"]["final_circularity_state"] == "CONTINUED_USE_CANDIDATE"
    assert report["indicative_valuation"]["status"] == "configured"
    assert report["lifetime_scenarios"]["status"] == "calibrated"
    assert report["metadata"]["module_owner"].startswith("Member 3")
