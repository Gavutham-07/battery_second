import pytest
from fastapi import HTTPException
from backend.main import get_analysis_report, get_exchanges, get_inventory
from backend.db import test_connection as check_mongo_connection, reports_collection, inventory_collection


def test_get_analysis_report_not_found():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    with pytest.raises(HTTPException) as exc_info:
        get_analysis_report("BAT-UNKNOWN-P3")
    assert exc_info.value.status_code == 404
    assert "No analysis report found" in exc_info.value.detail


def test_get_analysis_report_found():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    # Insert a fixture report
    test_id = "BAT-P3-REP-01"
    reports_collection.delete_many({"battery_id": test_id})
    reports_collection.insert_one({
        "battery_id": test_id,
        "soh": 85.0,
        "available_capacity_ah": 2.1,
        "safety_status": "PASSED",
        "confidence": 92.0,
        "decision": "SECOND_LIFE_STORAGE",
        "mode": "LIVE",
        "created_at": "2026-11-04T23:00:00Z"
    })

    report = get_analysis_report(test_id)
    assert report["battery_id"] == test_id
    assert report["soh"] == 85.0
    assert report["safety_status"] == "PASSED"
    assert report["decision"] == "SECOND_LIFE_STORAGE"

    # Cleanup
    reports_collection.delete_many({"battery_id": test_id})


def test_get_exchanges_empty():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    data = get_exchanges("BAT-NO-TXN-01")
    assert data["battery_id"] == "BAT-NO-TXN-01"
    assert isinstance(data["exchanges"], list)


def test_get_inventory():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    inventory = get_inventory()
    assert isinstance(inventory, list)

