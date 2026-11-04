import pytest
from fastapi import HTTPException
from backend.main import run_what_if_simulation, get_battery_valuation
from backend.schemas import WhatIfRequest
from backend.db import test_connection as check_mongo_connection, batteries_collection, reports_collection


TEST_ID = "BAT-P7-INT-VAL-01"


def setup_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": TEST_ID})
        reports_collection.delete_many({"battery_id": TEST_ID})


def teardown_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": TEST_ID})
        reports_collection.delete_many({"battery_id": TEST_ID})


def test_what_if_api_endpoint():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    # Insert battery & report fixtures
    batteries_collection.insert_one({
        "battery_id": TEST_ID,
        "chemistry": "LFP",
        "rated_capacity_ah": 2.5,
        "status": "REGISTERED"
    })
    reports_collection.insert_one({
        "battery_id": TEST_ID,
        "soh": 82.0,
        "available_capacity_ah": 2.05,
        "safety_status": "PASSED",
        "confidence": 90.0,
        "decision": "CONTINUE_EV",
        "created_at": "2026-11-05T01:00:00Z"
    })

    req = WhatIfRequest(
        battery_id=TEST_ID,
        daily_hours=4.0,
        temp_c=30.0,
        dod_pct=75.0
    )
    result = run_what_if_simulation(req)

    assert result["battery_id"] == TEST_ID
    assert result["projected_cycle_life"] > 0
    assert result["projected_months_remaining"] > 0
    assert result["acceleration_factor"] > 0.0
    assert "recommended_dod_limit" in result


def test_valuation_api_endpoint():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    val = get_battery_valuation(TEST_ID)
    assert val["battery_id"] == TEST_ID
    assert val["chemistry"] == "LFP"
    assert val["net_indicative_valuation_inr"] > 0.0
    assert "breakdown" in val
    assert val["breakdown"]["gross_capacity_credit_inr"] > 0.0
    assert "disclaimer" in val


def test_valuation_api_not_found():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    with pytest.raises(HTTPException) as exc_info:
        get_battery_valuation("BAT-NON-EXISTENT-VAL-99")
    assert exc_info.value.status_code == 404

