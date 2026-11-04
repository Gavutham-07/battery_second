import pytest
from backend.main import run_evaluation, get_mbco_recommendations
from backend.schemas import AnalysisRequest
from backend.db import test_connection as check_mongo_connection, tests_collection, reports_collection


TEST_ID = "BAT-P6-INT-MBCO-01"


def setup_module(module):
    if check_mongo_connection():
        tests_collection.delete_many({"battery_id": TEST_ID})
        reports_collection.delete_many({"battery_id": TEST_ID})


def teardown_module(module):
    if check_mongo_connection():
        tests_collection.delete_many({"battery_id": TEST_ID})
        reports_collection.delete_many({"battery_id": TEST_ID})


def test_mbco_api_evaluation_and_retrieval():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    # Ingest 25 healthy telemetry readings for 85%+ SOH
    fixtures = []
    for i in range(25):
        fixtures.append({
            "battery_id": TEST_ID,
            "sec": float(i),
            "v": round(3.35 - (i * 0.002), 3),
            "i": 0.50,
            "t": 27.5,
            "event": "DISCHARGE",
            "mode": "LIVE",
            "created_at": "2026-11-05T00:00:00Z"
        })
    tests_collection.insert_many(fixtures)

    # Trigger evaluation
    req = AnalysisRequest(
        battery_id=TEST_ID,
        chemistry="LFP",
        rated_capacity_ah=2.5
    )
    report = run_evaluation(req)

    # Verify report contains MBCO recommendations
    assert "mbco_recommendations" in report
    recs = report["mbco_recommendations"]
    assert len(recs) == 5
    assert recs[0]["suitability_score"] >= recs[1]["suitability_score"]

    # Verify dedicated GET /api/analysis/mbco/{battery_id} endpoint
    mbco_res = get_mbco_recommendations(TEST_ID)
    assert mbco_res["battery_id"] == TEST_ID
    assert mbco_res["safety_status"] == "PASSED"
    assert len(mbco_res["recommendations"]) == 5
    assert mbco_res["recommendations"][0]["route_id"] in ["ROUTE_LIGHT_EV", "ROUTE_SOLAR_BESS"]

