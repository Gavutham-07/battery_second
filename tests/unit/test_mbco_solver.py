import pytest
from ai_engine.mbco_solver import solve_mbco, CIRCULARITY_ROUTES


def test_mbco_high_soh_safe_battery():
    # 88% SOH, Safe, High Confidence
    recs = solve_mbco(
        soh=88.0,
        available_capacity_ah=2.2,
        safety_status="PASSED",
        confidence=95.0,
        estimated_ir_ohm=0.040
    )
    assert len(recs) == len(CIRCULARITY_ROUTES)
    # Highest ranked should be high-value reuse (e.g. Light EV or Solar BESS)
    top_route = recs[0]
    assert top_route["route_id"] in ["ROUTE_LIGHT_EV", "ROUTE_SOLAR_BESS"]
    assert top_route["suitability_score"] >= 0.80
    assert top_route["technical_fit"] is True
    assert top_route["safety_eligible"] is True
    assert "safety_score" in top_route["explainability"]


def test_mbco_second_life_storage_battery():
    # 72% SOH, Safe -> Too low for Light EV (min 80%), ideal for Solar BESS (min 65%)
    recs = solve_mbco(
        soh=72.0,
        available_capacity_ah=1.8,
        safety_status="PASSED",
        confidence=90.0,
        estimated_ir_ohm=0.055
    )
    top_route = recs[0]
    assert top_route["route_id"] == "ROUTE_SOLAR_BESS"
    assert top_route["technical_fit"] is True
    assert top_route["safety_eligible"] is True

    # Verify Light EV is technically unfit
    ev_route = next(r for r in recs if r["route_id"] == "ROUTE_LIGHT_EV")
    assert ev_route["technical_fit"] is False
    assert "SOH_BELOW_MINIMUM" in ev_route["explainability"]["status_note"]


def test_mbco_degraded_battery_recycling():
    # 48% SOH, Safe -> Below second life threshold (60%), ideal for direct recycling
    recs = solve_mbco(
        soh=48.0,
        available_capacity_ah=1.2,
        safety_status="PASSED",
        confidence=85.0
    )
    top_route = recs[0]
    assert top_route["route_id"] == "ROUTE_DIRECT_RECYCLE"
    assert top_route["suitability_score"] > 0.0


def test_mbco_safety_precedence_failed_safety():
    # 95% SOH but FAILED safety status
    recs = solve_mbco(
        soh=95.0,
        available_capacity_ah=2.4,
        safety_status="FAILED",
        confidence=90.0
    )
    # Direct recycling MUST be the only eligible route
    recycle_route = next(r for r in recs if r["route_id"] == "ROUTE_DIRECT_RECYCLE")
    assert recycle_route["safety_eligible"] is True

    # ALL reuse routes must be ineligible with score 0.0
    for r in recs:
        if r["route_id"] != "ROUTE_DIRECT_RECYCLE":
            assert r["safety_eligible"] is False
            assert r["suitability_score"] == 0.0
            assert "SAFETY_OVERRIDE_INELIGIBLE" in r["explainability"]["status_note"]


def test_mbco_safety_precedence_warning_safety():
    # 90% SOH with WARNING safety status
    recs = solve_mbco(
        soh=90.0,
        available_capacity_ah=2.25,
        safety_status="WARNING",
        confidence=85.0
    )
    # All reuse routes blocked under warning
    for r in recs:
        if r["route_id"] != "ROUTE_DIRECT_RECYCLE":
            assert r["safety_eligible"] is False
            assert r["suitability_score"] == 0.0


def test_mbco_custom_weights():
    # Emphasize environmental impact heavily
    custom_weights = {
        "safety": 0.20,
        "technical": 0.20,
        "economic": 0.10,
        "confidence": 0.10,
        "environmental": 0.40,
    }
    recs = solve_mbco(
        soh=82.0,
        available_capacity_ah=2.05,
        safety_status="PASSED",
        confidence=90.0,
        weights=custom_weights
    )
    assert len(recs) == len(CIRCULARITY_ROUTES)
    assert recs[0]["suitability_score"] > 0.0

