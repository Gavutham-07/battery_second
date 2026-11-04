import pytest
from backend.db import (
    db,
    test_connection as check_mongo_connection,
    batteries_collection,
    tests_collection as t_collection,
    reports_collection,
    exchanges_collection,
    inventory_collection,
)


def test_collections_handles_initialized():
    assert db.name == "revolt_db"
    assert batteries_collection.name == "batteries"
    assert t_collection.name == "tests"
    assert reports_collection.name == "reports"
    assert exchanges_collection.name == "exchanges"
    assert inventory_collection.name == "inventory"


def test_database_crud_operations():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    test_id = "BAT-TEST-PHASE2"
    # Ensure clean state
    batteries_collection.delete_one({"battery_id": test_id})

    # Create / Insert
    insert_result = batteries_collection.insert_one({
        "battery_id": test_id,
        "chemistry": "LFP",
        "rated_capacity_ah": 2.5,
        "status": "PHASE2_VERIFICATION"
    })
    assert insert_result.inserted_id is not None

    # Read / Query
    doc = batteries_collection.find_one({"battery_id": test_id})
    assert doc is not None
    assert doc["battery_id"] == test_id
    assert doc["chemistry"] == "LFP"
    assert doc["status"] == "PHASE2_VERIFICATION"

    # Delete / Cleanup
    delete_result = batteries_collection.delete_one({"battery_id": test_id})
    assert delete_result.deleted_count == 1
