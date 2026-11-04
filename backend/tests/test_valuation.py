"""Automated tests for Module 5 — Valuation (backend/ai/valuation.py)."""

import json
import pytest
from backend.ai.valuation import calculate_route_valuation


def test_unconfigured_valuation_returns_not_configured():
    # When config is empty or None
    res = calculate_route_valuation(soh_pct=85.0, rated_capacity_ah=2.5, valuation_config={"reference_price_per_kwh_inr": None})
    assert res["status"] == "not_configured"
    assert "not configured" in res["message"].lower()
    assert res["reference_price_per_kwh_inr"] is None
    assert "disclaimer" in res


def test_soh_unavailable_valuation():
    res = calculate_route_valuation(soh_pct=None, rated_capacity_ah=2.5, valuation_config={"reference_price_per_kwh_inr": 8000.0})
    assert res["status"] == "soh_unavailable"


def test_configured_valuation_calculation():
    # 2.5 Ah, 3.7 V cell pack (100 cells) -> 0.925 kWh nominal
    cfg = {"reference_price_per_kwh_inr": 10000.0}
    res = calculate_route_valuation(
        soh_pct=80.0,
        rated_capacity_ah=2.5,
        nominal_voltage_v=3.7,
        valuation_config=cfg,
        pack_cell_count=100,
    )

    assert res["status"] == "configured"
    assert res["reference_price_per_kwh_inr"] == 10000.0
    assert "route_valuations" in res
    routes = res["route_valuations"]
    assert "continued_ev" in routes
    assert "solar_storage" in routes
    assert "recycling" in routes

    ev_route = routes["continued_ev"]
    assert ev_route["gross_value_inr"] > 0
    assert "cost_breakdown" in ev_route
    assert "testing_cost_inr" in ev_route["cost_breakdown"]
    assert "refurbishment_cost_inr" in ev_route["cost_breakdown"]
    assert ev_route["indicative_net_value_inr"] >= 0
    assert len(ev_route["assumptions"]) > 0


def test_valuation_json_serializability():
    res = calculate_route_valuation(soh_pct=85.0, rated_capacity_ah=2.5)
    json_str = json.dumps(res)
    assert json_str is not None
