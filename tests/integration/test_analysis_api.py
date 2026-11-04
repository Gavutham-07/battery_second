import pytest
from backend.main import run_evaluation, get_analysis_report
from backend.schemas import AnalysisRequest
from backend.db import test_connection as check_mongo_connection, tests_collection, reports_collection


TEST_ID = "BAT-P5-INT-EVAL-01"


def setup_module(module):
    if check_mongo_connection():
        tests_collection.delete_many({"battery_id": TEST_ID})
        reports_collection.delete_many({"battery_id": TEST_ID})


def teardown_module(module):
    if check_mongo_connection():
        tests_collection.delete_many({"battery_id": TEST_ID})
        reports_collection.delete_many({"battery_id": TEST_ID})


def test_evaluate_analysis_endpoint_integration():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    # 1. Populate test bench telemetry in tests_collection
    telemetry_fixtures = []
    for i in range(25):
        telemetry_fixtures.append({
            "battery_id": TEST_ID,
            "sec": float(i),
            "v": round(4.15 - (i * 0.015), 3),
            "i": 0.50,
            "t": round(27.0 + (i * 0.08), 2),
            "event": "DISCHARGE",
            "mode": "REPLAY",
            "created_at": "2026-11-05T00:00:00Z"
        })
    tests_collection.insert_many(telemetry_fixtures)

    # 2. Trigger evaluation endpoint
    request = AnalysisRequest(
        battery_id=TEST_ID,
        chemistry="LFP",
        rated_capacity_ah=2.5
    )

    report = run_evaluation(request)

    # 3. Verify decoupled fields and bounds
    assert report["battery_id"] == TEST_ID
    assert report["soh"] is not None
    assert 0.0 <= report["soh"] <= 100.0
    assert report["available_capacity_ah"] is not None
    assert report["available_capacity_ah"] > 0.0
    assert report["safety_status"] in ["PASSED", "WARNING", "FAILED", "UNKNOWN"]
    assert report["confidence"] is not None
    assert 0.0 <= report["confidence"] <= 100.0
    assert report["decision"] in ["CONTINUE_EV", "SECOND_LIFE_STORAGE", "FURTHER_TESTING", "QUARANTINE", "RECYCLE"]
    assert report["mode"] == "REPLAY"
    assert "data_quality" in report
    assert report["data_quality"]["sample_count"] == 25

    # 4. Verify report persistence in reports_collection
    saved_doc = reports_collection.find_one({"battery_id": TEST_ID})
    assert saved_doc is not None
    assert saved_doc["battery_id"] == TEST_ID
    assert saved_doc["soh"] == report["soh"]

    # 5. Verify retrieval endpoint
    retrieved = get_analysis_report(TEST_ID)
    assert retrieved["battery_id"] == TEST_ID
    assert retrieved["soh"] == report["soh"]
    assert retrieved["decision"] == report["decision"]

