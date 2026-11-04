"""Automated tests for Module 4 — MBCO Decision Engine (backend/ai/mbco.py)."""

import pytest
from backend.ai.mbco import run_mbco_engine, CircularityDecision


def test_critical_safety_precedence_overrides_high_soh():
    """Rule: Critical safety indicator overrides all SOH and economic recommendations."""
    assessment = {
        "battery_id": "BAT-CRIT-99",
        "data_quality": {"status": "PASSED", "total_readings": 20, "valid_readings": 20},
        "extracted_features": {
            "pulse_features": {"complete_pulse_sequence": True, "pulse_05c_resistance_est_ohm": 0.15}
        },
        "soh_assessment": {"status": "validated_test", "soh_pct": 98.0},
    }
    safety_result = {
        "safety_state": "QUARANTINE_SPECIALIST_REVIEW",
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
    # Crucial check: Continued EV and solar storage must NOT be eligible despite 98% SOH!
    evals = decision["pathway_evaluations"]
    assert evals["continued_ev"]["eligibility"] is False
    assert evals["solar_storage"]["eligibility"] is False
    assert any("Critical safety" in r for r in evals["continued_ev"]["reasons"])


def test_insufficient_evidence_triggers_further_testing():
    """Rule: Insufficient or unreliable evidence triggers FURTHER_TESTING_REQUIRED."""
    assessment = {
        "battery_id": "BAT-UNCONF-1",
        "data_quality": {"status": "DEGRADED", "total_readings": 5, "valid_readings": 3},
        "extracted_features": {"pulse_features": {"complete_pulse_sequence": False}},
        "soh_assessment": {"status": "not_available_for_this_protocol", "soh_pct": None},
    }
    safety_result = {
        "safety_state": "SCREENING_CLEAR",
        "is_safe_for_second_life": True,
        "critical_violations": [],
        "warnings": [],
    }
    confidence_result = {
        "confidence_score": 0.35,
        "confidence_status": "CONFIDENCE_LIMITED",
        "further_testing_required": True,
        "reasons": ["Pulse protocol incomplete"],
        "limitations": ["Incomplete pulse sequence"],
    }

    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=None,
    )

    assert decision["final_decision"] == CircularityDecision.FURTHER_TESTING_REQUIRED.value
    assert decision["decision_precedence_applied"].startswith("Level 2")


def test_technically_incompatible_pathway():
    """Rule: SOH below requirement marks pathway ineligible."""
    assessment = {
        "battery_id": "BAT-LOW-SOH",
        "data_quality": {"status": "PASSED", "total_readings": 20, "valid_readings": 20},
        "extracted_features": {
            "pulse_features": {"complete_pulse_sequence": True, "pulse_05c_resistance_est_ohm": 0.20}
        },
        "soh_assessment": {"status": "tested", "soh_pct": 65.0},
    }
    safety_result = {
        "safety_state": "SCREENING_CLEAR",
        "is_safe_for_second_life": True,
        "critical_violations": [],
        "warnings": [],
    }
    confidence_result = {
        "confidence_score": 0.85,
        "confidence_status": "CONFIDENCE_SUFFICIENT",
        "further_testing_required": False,
        "reasons": ["High confidence"],
        "limitations": [],
    }

    # SOH = 65% is below continued_ev (80%), light_ev (75%), solar_storage (70%), but meets low_power (60%)
    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=65.0,
    )

    evals = decision["pathway_evaluations"]
    assert evals["continued_ev"]["eligibility"] is False
    assert evals["solar_storage"]["eligibility"] is False
    assert evals["low_power_devices"]["eligibility"] is True
    assert decision["final_decision"] == CircularityDecision.SECOND_LIFE_CANDIDATE.value
    assert decision["recommended_pathway"] == "low_power_devices"


def test_multiple_eligible_pathways_ranking():
    """Rule: Compare and rank eligible applications."""
    assessment = {
        "battery_id": "BAT-PERFECT",
        "data_quality": {"status": "PASSED", "total_readings": 20, "valid_readings": 20},
        "extracted_features": {
            "pulse_features": {"complete_pulse_sequence": True, "pulse_05c_resistance_est_ohm": 0.10}
        },
        "soh_assessment": {"status": "tested", "soh_pct": 92.0},
    }
    safety_result = {
        "safety_state": "SCREENING_CLEAR",
        "is_safe_for_second_life": True,
        "critical_violations": [],
        "warnings": [],
    }
    confidence_result = {
        "confidence_score": 0.90,
        "confidence_status": "CONFIDENCE_SUFFICIENT",
        "further_testing_required": False,
        "reasons": ["Complete sequence"],
        "limitations": [],
    }

    decision = run_mbco_engine(
        assessment_data=assessment,
        safety_result=safety_result,
        confidence_result=confidence_result,
        soh_pct=92.0,
    )

    assert decision["final_decision"] == CircularityDecision.CONTINUED_USE_CANDIDATE.value
    assert len(decision["ranked_pathways"]) > 1
    # Continued EV has high suitability and meets threshold
    top = decision["ranked_pathways"][0]
    assert top["pathway_id"] == "continued_ev"
    # Environmental status check
    evals = decision["pathway_evaluations"]
    assert evals["continued_ev"]["environmental_information_status"] == "not_available_without_primary_lca_data"
