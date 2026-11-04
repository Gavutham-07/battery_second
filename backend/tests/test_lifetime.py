"""Automated tests for Module 6 — Lifetime Scenarios (backend/ai/lifetime.py)."""

import json
import pytest
from backend.ai.lifetime import calculate_lifetime_scenarios


def test_uncalibrated_lifetime_returns_not_calibrated():
    # When reference_cycle_life is None or not provided
    res = calculate_lifetime_scenarios(
        soh_pct=85.0,
        lifetime_config={"reference_cycle_life": None}
    )
    assert res["status"] == "not_calibrated"
    assert "not calibrated" in res["message"].lower()
    assert "disclaimer" in res


def test_soh_unavailable_lifetime():
    cfg = {"reference_cycle_life": 2500, "reference_dod_pct": 80.0, "reference_temperature_c": 25.0}
    res = calculate_lifetime_scenarios(soh_pct=None, lifetime_config=cfg)
    assert res["status"] == "soh_unavailable"


def test_calibrated_lifetime_scenario_calculation():
    cfg = {
        "reference_cycle_life": 3000,
        "reference_dod_pct": 80.0,
        "reference_temperature_c": 25.0,
    }
    # Test high temp scenario (35°C should increase degradation acceleration)
    res = calculate_lifetime_scenarios(
        soh_pct=90.0,
        operating_temperature_c=35.0,
        depth_of_discharge_pct=80.0,
        application_profile="solar_storage",
        lifetime_config=cfg,
    )

    assert res["status"] == "calibrated"
    assert res["current_soh_pct"] == 90.0
    scenarios = res["scenarios"]
    assert "operating_scenario" in scenarios
    op = scenarios["operating_scenario"]
    assert op["thermal_stress_factor"] == pytest.approx(2.0, abs=0.1)  # 10C delta = ~2x acceleration
    assert op["projected_remaining_cycles"] > 0
    assert op["projected_remaining_years"] > 0
    assert len(res["assumptions"]) > 0
    assert "disclaimer" in res


def test_lifetime_json_serializability():
    res = calculate_lifetime_scenarios(soh_pct=85.0)
    json_str = json.dumps(res)
    assert json_str is not None
