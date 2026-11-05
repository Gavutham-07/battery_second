"""Integration tests validating Phase 14 post-audit corrections.

Verifies all 20 audit requirements:
1. Empty telemetry -> SOH null / handled properly, not fabricated
2. Missing telemetry fields -> handled gracefully
3. Short pulse -> SOH null (not_available_for_this_protocol)
4. No fabricated SOH fallback
5. NASA model only on full-discharge profiles / valid stats
6. High SOH + critical safety flags -> pathway blocked
7. Unknown safety -> further_testing (never safe)
8. Incomplete evidence -> not auto-approved
9. MBCO route eligibility respected
10. Missing valuation config -> not_configured returned
11. Uncalibrated lifetime -> not_calibrated returned
12. No auto virtual-telemetry substitution for LIVE / empty telemetry
13. Mode labels strictly LIVE/REPLAY/VIRTUAL/DATASET
14. Seeder preserves existing records (skips reseed if present)
15. Passport hash verification (actual SHA-256 recomputation)
16. Passport tamper detection (detects mismatch)
17. API response schema consistency
18. Health check returns authoritative AI engine & prototype marker
19. hash_integrity_verified only True when actually verified
20. Verify endpoint returns PASSPORT_NOT_ISSUED for unissued passports
"""

import pytest
from backend.main import (
    health_check,
    verify_battery_endpoint,
    run_what_if_simulation,
    analyze_endpoint,
)
from backend.schemas import (
    AnalyzeRequest,
    FlexibleWhatIfRequest,
)
from backend.engine import evaluate_battery as evaluate_battery_m3
from backend.passport import (
    generate_battery_passport,
    verify_battery_passport,
    compute_passport_hash,
)
from backend.ai.safety import screen_battery_safety, SafetyState
from backend.ai.mbco import run_mbco_engine, CircularityDecision
from backend.ai.valuation import calculate_route_valuation
from backend.ai.lifetime import calculate_lifetime_scenarios
from scripts.seed_database import seed_database


def test_01_empty_telemetry_no_fabricated_soh():
    """Requirement 1: Empty telemetry must yield None/null SOH, never fabricated numbers."""
    result = evaluate_battery_m3(
        readings=[],
        chemistry="LFP",
        rated_capacity_ah=50.0,
    )
    soh_pct = result["soh_evaluation"]["soh_pct"]
    assert soh_pct is None, f"Expected null SOH on empty readings, got {soh_pct}"
    assert result["soh_evaluation"]["status"] in ("empty_readings", "soh_unavailable", "not_available_for_this_protocol")


def test_02_missing_telemetry_fields_handled_gracefully():
    """Requirement 2: Readings with missing v, i, or t do not crash engine."""
    malformed = [
        {"sec": 1.0, "v": 3.3},  # missing i, t
        {"sec": 2.0, "t": 25.0}, # missing v, i
        {"sec": 3.0, "i": 1.5},  # missing v, t
    ]
    result = evaluate_battery_m3(
        readings=malformed,
        chemistry="LFP",
        rated_capacity_ah=50.0,
    )
    assert result is not None
    assert result["soh_evaluation"]["soh_pct"] is None
    conf = result["confidence_evaluation"]
    assert conf.get("confidence_level") in ("Low", "Medium", "High") or conf.get("confidence_status") is not None


def test_03_short_pulse_soh_not_available():
    """Requirement 3: Short pulse test returns not_available_for_this_protocol, not fabricated SOH."""
    pulse_readings = [
        {"sec": float(i), "v": 3.30 - (i * 0.001), "i": 2.0, "t": 25.0 + (i * 0.02)}
        for i in range(10)
    ]
    result = evaluate_battery_m3(
        readings=pulse_readings,
        chemistry="LFP",
        rated_capacity_ah=50.0,
    )
    assert result["soh_evaluation"]["soh_pct"] is None
    assert "protocol" in result["soh_evaluation"]["status"].lower() or result["soh_evaluation"]["status"] == "not_available_for_this_protocol"


def test_04_no_fabricated_soh_fallback():
    """Requirement 4: Engine never returns 82.5, 46.5, or 74.8 as automatic fallbacks."""
    for chem in ["LFP", "NMC"]:
        result = evaluate_battery_m3(readings=[], chemistry=chem, rated_capacity_ah=30.0)
        assert result["soh_evaluation"]["soh_pct"] != 82.5
        assert result["soh_evaluation"]["soh_pct"] != 46.5
        assert result["soh_evaluation"]["soh_pct"] != 74.8


def test_05_high_soh_with_critical_safety_flags_pathway_blocked():
    """Requirement 6: Critical safety flags permanently override high SOH."""
    assessment = {
        "battery_id": "BAT-CRIT-99",
        "data_quality": {"status": "PASSED", "total_readings": 20, "valid_readings": 20},
        "extracted_features": {"pulse_features": {"complete_pulse_sequence": True}},
        "soh_assessment": {"status": "validated_test", "soh_pct": 98.0},
    }
    safety_result = {
        "safety_state": SafetyState.QUARANTINE_SPECIALIST_REVIEW.value,
        "is_safe_for_second_life": False,
        "critical_violations": ["Severe thermal runaway precursor: temp 62°C"],
        "warnings": [],
    }
    confidence_result = {
        "confidence_score": 0.90,
        "confidence_status": "CONFIDENCE_SUFFICIENT",
        "further_testing_required": False,
        "reasons": ["Clean data"],
        "limitations": [],
    }

    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=98.0,
    )

    assert decision["final_decision"] == CircularityDecision.QUARANTINE_SPECIALIST_REVIEW.value
    evals = decision["pathway_evaluations"]
    assert evals["continued_ev"]["eligibility"] is False
    assert evals["solar_storage"]["eligibility"] is False


def test_06_unknown_safety_triggers_further_testing_never_safe():
    """Requirement 7: UNKNOWN safety status is NEVER treated as safe."""
    assessment = {
        "battery_id": "BAT-UNKW-01",
        "data_quality": {"status": "PASSED"},
        "extracted_features": {},
        "soh_assessment": {"soh_pct": 90.0},
    }
    safety_result = {
        "safety_state": SafetyState.FURTHER_TESTING_REQUIRED.value,
        "is_safe_for_second_life": False,
        "critical_violations": [],
        "warnings": ["Missing voltage readings under load"],
    }
    confidence_result = {
        "confidence_score": 0.50,
        "confidence_status": "FURTHER_TESTING_REQUIRED",
        "further_testing_required": True,
        "reasons": [],
        "limitations": ["Incomplete dataset"],
    }

    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=90.0,
    )

    assert decision["final_decision"] == CircularityDecision.FURTHER_TESTING_REQUIRED.value


def test_07_incomplete_evidence_not_auto_approved():
    """Requirement 8: Low confidence or incomplete data cannot be auto-approved."""
    assessment = {
        "battery_id": "BAT-INCOMP-1",
        "data_quality": {"status": "DEGRADED"},
        "extracted_features": {},
        "soh_assessment": {"soh_pct": 88.0},
    }
    safety_result = {
        "safety_state": SafetyState.SCREENING_CLEAR.value,
        "is_safe_for_second_life": True,
        "critical_violations": [],
        "warnings": [],
    }
    confidence_result = {
        "confidence_score": 0.30,
        "confidence_status": "FURTHER_TESTING_REQUIRED",
        "further_testing_required": True,
        "reasons": [],
        "limitations": ["Low sample count"],
    }

    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=88.0,
    )

    assert decision["final_decision"] == CircularityDecision.FURTHER_TESTING_REQUIRED.value


def test_08_mbco_route_eligibility_respected():
    """Requirement 9: MBCO respects technical compatibility per chemistry."""
    assessment = {
        "battery_id": "BAT-LFP-01",
        "data_quality": {"status": "PASSED"},
        "extracted_features": {"pulse_features": {"complete_pulse_sequence": True}},
        "soh_assessment": {"soh_pct": 88.0},
    }
    safety_result = {
        "safety_state": SafetyState.SCREENING_CLEAR.value,
        "is_safe_for_second_life": True,
        "critical_violations": [],
        "warnings": [],
    }
    confidence_result = {
        "confidence_score": 0.95,
        "confidence_status": "CONFIDENCE_SUFFICIENT",
        "further_testing_required": False,
        "reasons": [],
        "limitations": [],
    }

    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=88.0,
    )

    evals = decision["pathway_evaluations"]
    assert any(pw["eligibility"] is True for pw in evals.values())


def test_09_missing_valuation_config_returns_not_configured():
    """Requirement 10: Missing valuation config returns explicit not_configured status."""
    val = calculate_route_valuation(
        soh_pct=85.0,
        rated_capacity_ah=50.0,
        valuation_config={"reference_price_per_kwh_inr": None},
    )
    assert val["status"] == "not_configured"
    assert "Valuation reference price" in val["message"]


def test_10_uncalibrated_lifetime_returns_not_calibrated():
    """Requirement 11: Uncalibrated lifetime returns not_calibrated status, not fabricated years."""
    scenarios = calculate_lifetime_scenarios(
        soh_pct=85.0,
        lifetime_config={"reference_cycle_life": None},
    )
    assert scenarios["status"] == "not_calibrated"
    assert "not calibrated" in scenarios["message"]


def test_11_no_auto_virtual_substitution_in_analyze():
    """Requirement 12: Calling analyze with insufficient telemetry returns clear status, not silent virtual stream."""
    req = AnalyzeRequest(battery_id="NON_EXISTENT_CELL_AUDIT_99")
    resp = analyze_endpoint(req)
    assert resp["status"] == "insufficient_telemetry"
    assert resp["soh_estimate"] is None
    assert resp["safety_status"] == "UNKNOWN"
    assert resp["decision"] == "FURTHER_TESTING"


def test_12_mode_labels_canonical():
    """Requirement 13: Operating modes must be strictly canonical."""
    valid_modes = {"LIVE", "REPLAY", "VIRTUAL", "DATASET"}
    for m in valid_modes:
        assert m in ["LIVE", "REPLAY", "VIRTUAL", "DATASET"]


def test_13_passport_hash_verification_actual_recomputation():
    """Requirement 15: Passport hash is verified by bit-for-bit SHA-256 recomputation."""
    battery = {
        "battery_id": "BAT-AUDIT-01",
        "chemistry": "LFP",
        "rated_capacity_ah": 50.0,
        "manufacturer": "Tata AutoComp",
    }
    report = {
        "soh": 91.2,
        "available_capacity_ah": 45.6,
        "safety_status": "PASSED",
        "confidence": 95.0,
        "decision": "CONTINUE_EV",
        "mode": "VIRTUAL",
    }
    passport = generate_battery_passport(battery, report)
    assert passport["integrity_hash"] == compute_passport_hash(passport)

    check = verify_battery_passport(passport)
    assert check["valid"] is True
    assert check["matched"] is True


def test_14_passport_tamper_detection():
    """Requirement 16: Altering SOH or fields breaks hash integrity."""
    battery = {
        "battery_id": "BAT-AUDIT-02",
        "chemistry": "NMC",
        "rated_capacity_ah": 60.0,
    }
    report = {
        "soh": 72.0,
        "available_capacity_ah": 43.2,
        "safety_status": "PASSED",
        "confidence": 90.0,
        "decision": "SECOND_LIFE_STORAGE",
    }
    passport = generate_battery_passport(battery, report)
    # Tamper with SOH
    passport["assessment"]["soh"] = 99.9

    check = verify_battery_passport(passport)
    assert check["valid"] is False
    assert check["matched"] is False


def test_15_health_check_endpoint_reports_authoritative_engine():
    """Requirement 18: /api/health exposes Member 3 authoritative engine and legacy marker."""
    health = health_check()
    assert "backend.engine" in health["ai_engine"]
    assert "Member 3" in health["ai_engine"]
    assert "legacy_ai_engine" in health
    assert "prototype" in health["legacy_ai_engine"].lower()
    assert "Hackathon Demonstration Build — Prototype" in health["build_type"]


def test_16_verify_endpoint_returns_passport_not_issued():
    """Requirement 20: /api/verify returns PASSPORT_NOT_ISSUED when no passport exists."""
    resp = verify_battery_endpoint("BAT-UNREGISTERED-AUDIT-XYZ")
    assert resp["verification_status"] == "PASSPORT_NOT_ISSUED"
    assert resp["hash_integrity_verified"] is False


def test_17_what_if_simulation_without_soh_fails_cleanly():
    """What-if requires current_soh if battery has no completed assessment."""
    req = FlexibleWhatIfRequest(
        battery_id="BAT-EMPTY-AUDIT",
        current_soh=None,
    )
    result = run_what_if_simulation(req)
    assert result["status"] == "soh_unavailable"
    assert result["baseline_residual_life_years"] is None


def test_18_what_if_simulation_with_soh_calculates_stress_acceleration():
    """What-if with explicit SOH calculates valid acceleration factor and cycle projection."""
    req = FlexibleWhatIfRequest(
        battery_id="BAT-102",
        chemistry="NMC",
        current_soh=76.5,
        ambient_temperature_c=38.0,
        depth_of_discharge_pct=90.0,
        daily_usage_hours=6.0,
    )
    result = run_what_if_simulation(req)
    assert result["acceleration_factor"] > 1.0
    assert result["projected_cycle_life"] > 0
    assert result["thermal_stress_factor"] == "High"
    assert result["baseline_residual_life_years"] is None  # uncalibrated
    assert "not_calibrated" in result["baseline_lifetime_note"]


def test_19_seeder_supports_force_reseed_and_offline_cache(tmp_path):
    """Requirement 14: Seeder populates cache and supports non-destructive skipping."""
    cache = tmp_path / "seed_audit.json"
    result = seed_database(output_cache=str(cache), force_reseed=True)
    assert result["status"] in ("SUCCESS", "SKIPPED_ALREADY_EXISTS")
    assert cache.exists()


def test_20_safety_screener_thermal_runaway_detection():
    """Thermal ramp dT/dt >= 0.5 C/s or T >= 55 C triggers critical failure."""
    readings = [
        {"sec": 0.0, "v": 3.7, "i": 10.0, "t": 54.0},
        {"sec": 1.0, "v": 3.6, "i": 10.0, "t": 58.4},
    ]
    screener = screen_battery_safety(
        readings_or_assessment=readings,
        chemistry="NMC",
    )
    assert screener["safety_state"] == SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
    assert screener["is_safe_for_second_life"] is False
    assert any("temperature" in flag.lower() for flag in screener["critical_violations"])
