import pytest
from ai_engine.valuation import calculate_valuation
from ai_engine.what_if import simulate_what_if


def test_calculate_valuation_lfp_nominal():
    val = calculate_valuation(
        battery_id="BAT-VAL-01",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        available_capacity_ah=2.1,
        soh=84.0,
        safety_status="PASSED"
    )
    assert val["battery_id"] == "BAT-VAL-01"
    assert val["chemistry"] == "LFP"
    assert val["net_indicative_valuation_inr"] > val["breakdown"]["material_scrap_floor_inr"]
    assert val["breakdown"]["safety_risk_penalty_inr"] == 0.0
    assert "disclaimer" in val


def test_calculate_valuation_nmc_higher_base():
    val_lfp = calculate_valuation(
        battery_id="BAT-LFP",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        available_capacity_ah=2.1,
        soh=84.0,
        safety_status="PASSED"
    )
    val_nmc = calculate_valuation(
        battery_id="BAT-NMC",
        chemistry="NMC",
        rated_capacity_ah=2.5,
        available_capacity_ah=2.1,
        soh=84.0,
        safety_status="PASSED"
    )
    # NMC has higher energy density & material value than LFP
    assert val_nmc["breakdown"]["chemistry_base_rate_per_ah"] > val_lfp["breakdown"]["chemistry_base_rate_per_ah"]
    assert val_nmc["net_indicative_valuation_inr"] > val_lfp["net_indicative_valuation_inr"]


def test_calculate_valuation_safety_failure_drops_to_scrap():
    val = calculate_valuation(
        battery_id="BAT-FAIL",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        available_capacity_ah=2.4,  # High capacity, but safety failed
        soh=96.0,
        safety_status="FAILED"
    )
    # Value must drop down to scrap floor
    assert val["net_indicative_valuation_inr"] == val["breakdown"]["material_scrap_floor_inr"]
    assert val["breakdown"]["safety_risk_penalty_inr"] > 0.0


def test_calculate_valuation_safety_warning_penalty():
    val_safe = calculate_valuation(
        battery_id="BAT-S",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        available_capacity_ah=2.2,
        soh=88.0,
        safety_status="PASSED"
    )
    val_warn = calculate_valuation(
        battery_id="BAT-W",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        available_capacity_ah=2.2,
        soh=88.0,
        safety_status="WARNING"
    )
    assert val_warn["net_indicative_valuation_inr"] < val_safe["net_indicative_valuation_inr"]
    assert val_warn["breakdown"]["safety_risk_penalty_inr"] > 0.0


def test_simulate_what_if_thermal_stress():
    # Cold / baseline vs Hot
    sim_base = simulate_what_if(
        battery_id="BAT-W1",
        current_soh=85.0,
        daily_hours=4.0,
        temp_c=25.0,
        dod_pct=60.0
    )
    sim_hot = simulate_what_if(
        battery_id="BAT-W1",
        current_soh=85.0,
        daily_hours=4.0,
        temp_c=42.0,  # Hot operation accelerates degradation
        dod_pct=60.0
    )
    assert sim_hot["acceleration_factor"] > sim_base["acceleration_factor"]
    assert sim_hot["projected_cycle_life"] < sim_base["projected_cycle_life"]
    assert sim_hot["projected_months_remaining"] < sim_base["projected_months_remaining"]
    assert sim_hot["recommended_dod_limit"] <= 70.0


def test_simulate_what_if_dod_impact():
    # Shallow DoD vs Deep DoD
    sim_shallow = simulate_what_if(
        battery_id="BAT-W2",
        current_soh=85.0,
        daily_hours=4.0,
        temp_c=25.0,
        dod_pct=40.0
    )
    sim_deep = simulate_what_if(
        battery_id="BAT-W2",
        current_soh=85.0,
        daily_hours=4.0,
        temp_c=25.0,
        dod_pct=95.0
    )
    assert sim_deep["acceleration_factor"] > sim_shallow["acceleration_factor"]
    assert sim_deep["projected_cycle_life"] < sim_shallow["projected_cycle_life"]


def test_simulate_what_if_daily_hours():
    # Light use (2 hrs/day) vs Intensive use (8 hrs/day)
    sim_light = simulate_what_if(
        battery_id="BAT-W3",
        current_soh=85.0,
        daily_hours=2.0,
        temp_c=25.0,
        dod_pct=70.0
    )
    sim_heavy = simulate_what_if(
        battery_id="BAT-W3",
        current_soh=85.0,
        daily_hours=8.0,
        temp_c=25.0,
        dod_pct=70.0
    )
    assert sim_heavy["projected_months_remaining"] < sim_light["projected_months_remaining"]

