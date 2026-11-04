import pytest
from fastapi import HTTPException
from backend.main import register_battery, get_battery, list_batteries
from backend.schemas import BatteryRegistration
from backend.db import test_connection as check_mongo_connection, batteries_collection


def setup_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": {"$in": ["BAT-P3-TEST-01", "BAT-P3-TEST-02"]}})


def teardown_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": {"$in": ["BAT-P3-TEST-01", "BAT-P3-TEST-02"]}})


def test_battery_registration_success():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    payload = BatteryRegistration(
        battery_id="BAT-P3-TEST-01",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        voltage=3.2,
        manufacturer="EVE Energy",
        source_vehicle="Ola S1 Pro"
    )

    result = register_battery(payload)
    assert result["message"] == "Battery registered successfully"
    assert result["battery_id"] == "BAT-P3-TEST-01"
    assert result["status"] == "REGISTERED"
    assert "created_at" in result


def test_battery_registration_duplicate_conflict():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    payload = BatteryRegistration(
        battery_id="BAT-P3-TEST-01",
        chemistry="LFP",
        rated_capacity_ah=2.5
    )

    with pytest.raises(HTTPException) as exc_info:
        register_battery(payload)
    assert exc_info.value.status_code == 409
    assert "already registered" in exc_info.value.detail


def test_get_battery_success():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    doc = get_battery("BAT-P3-TEST-01")
    assert doc["battery_id"] == "BAT-P3-TEST-01"
    assert doc["chemistry"] == "LFP"
    assert doc["rated_capacity_ah"] == 2.5
    assert doc["status"] == "REGISTERED"


def test_get_battery_not_found():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    with pytest.raises(HTTPException) as exc_info:
        get_battery("BAT-NON-EXISTENT-999")
    assert exc_info.value.status_code == 404
    assert "not found in registry" in exc_info.value.detail


def test_list_batteries():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    batteries = list_batteries()
    assert isinstance(batteries, list)
    battery_ids = [b["battery_id"] for b in batteries]
    assert "BAT-P3-TEST-01" in battery_ids

