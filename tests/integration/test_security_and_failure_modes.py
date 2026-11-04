import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from backend.main import (
    register_battery,
    get_battery,
    get_inventory,
    group_cells,
    verify_passport,
    analyze_endpoint,
    simulate_stream_endpoint,
)
from backend.schemas import (
    BatteryRegistration,
    AnalyzeRequest,
    SimulateStreamRequest,
    CellGroupingRequest,
)
from backend.passport import (
    generate_battery_passport,
    verify_battery_passport,
)
from backend.db import (
    test_connection as check_mongo_connection,
    batteries_collection,
    tests_collection,
    reports_collection,
    inventory_collection,
)

SEC_BATTERY_ID = "BAT-SEC-AUDIT-01"


def setup_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})
        tests_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})
        reports_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})
        inventory_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})


def teardown_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})
        tests_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})
        reports_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})
        inventory_collection.delete_many({"battery_id": {"$regex": "^BAT-SEC-"}})


def test_passport_tamper_detection_soh_modified():
    """Verify bit-for-bit SHA-256 tamper evidence detects altered SOH."""
    battery = {
        "battery_id": SEC_BATTERY_ID,
        "chemistry": "LFP",
        "rated_capacity_ah": 50.0,
        "manufacturer": "EVE",
        "source_vehicle": "EV-X"
    }
    report = {
        "soh": 72.5,
        "available_capacity_ah": 36.25,
        "safety_status": "PASSED",
        "confidence": 92.0,
        "decision": "SECOND_LIFE_STORAGE",
        "mode": "LIVE"
    }
    passport = generate_battery_passport(battery, report)
    assert passport["integrity_hash"] is not None

    # Verify untampered passport passes
    ver_clean = verify_battery_passport(passport)
    assert ver_clean["valid"] is True
    assert ver_clean["matched"] is True

    # Tamper with SOH (fraudulent upgrade from 72.5% to 92.0%)
    tampered_passport = dict(passport)
    tampered_passport["assessment"] = dict(passport["assessment"])
    tampered_passport["assessment"]["soh"] = 92.0

    ver_tampered = verify_battery_passport(tampered_passport)
    assert ver_tampered["valid"] is False
    assert ver_tampered["matched"] is False
    assert "Tamper detected" in ver_tampered["error"]


def test_passport_tamper_detection_route_modified():
    """Verify tamper evidence detects fraudulent route escalation."""
    battery = {"battery_id": SEC_BATTERY_ID, "chemistry": "NMC", "rated_capacity_ah": 60.0}
    report = {
        "soh": 55.0,
        "available_capacity_ah": 33.0,
        "safety_status": "FAILED",
        "decision": "RECYCLE",
        "mode": "VIRTUAL"
    }
    passport = generate_battery_passport(battery, report)

    # Tamper decision: change RECYCLE to CONTINUE_EV
    tampered = dict(passport)
    tampered["assessment"] = dict(passport["assessment"])
    tampered["assessment"]["decision"] = "CONTINUE_EV"

    ver = verify_battery_passport(tampered)
    assert ver["valid"] is False
    assert ver["matched"] is False


def test_passport_missing_or_malformed_payload():
    """Verify rejection of malformed passport structures."""
    assert verify_battery_passport("not-a-dict")["valid"] is False
    assert verify_battery_passport({"battery_id": "BAT-X"})["valid"] is False


def test_thermal_runaway_strict_safety_override():
    """
    CRITICAL DECISION RULE: Cell with high nominal SOH (e.g. 95%) that exhibits
    severe thermal runaway (T > 55°C, dT/dt > 0.5°C/s) MUST be locked out from
    secondary life and assigned to RECYCLE.
    """
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    thermal_battery_id = "BAT-SEC-THERMAL-RUNAWAY"

    # Register battery
    batteries_collection.insert_one({
        "battery_id": thermal_battery_id,
        "chemistry": "LFP",
        "rated_capacity_ah": 50.0,
        "status": "Awaiting Screening"
    })

    # Simulate thermally unsafe 90s screening cycle
    sim_req = SimulateStreamRequest(
        battery_id=thermal_battery_id,
        data_source="virtual_circuit",
        test_profile="thermally_unsafe"
    )
    simulate_stream_endpoint(sim_req)

    # Evaluate via AI analysis
    ana_req = AnalyzeRequest(battery_id=thermal_battery_id)
    analysis = analyze_endpoint(ana_req)

    # Assert strict safety lockout
    assert analysis["safety_status"] == "Critical Danger"
    assert analysis["recommended_action"] == "Recycle"
    for match in analysis["second_life_matches"]:
        assert match["suitability"] == "Not Recommended"
        assert match["predicted_lifetime_years"] == 0.0


def test_invalid_capacity_negative_or_zero():
    """Verify input validation rejects zero or negative capacity."""
    with pytest.raises(ValidationError):
        BatteryRegistration(battery_id="BAT-SEC-ERR", chemistry="LFP", rated_capacity_ah=-10.0)
    with pytest.raises(ValidationError):
        BatteryRegistration(battery_id="BAT-SEC-ERR", chemistry="LFP", rated_capacity_ah=0.0)


def test_unregistered_battery_not_found():
    """Verify 404 on nonexistent battery query."""
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    with pytest.raises(HTTPException) as exc_info:
        get_battery("BAT-SEC-DOES-NOT-EXIST-404")
    assert exc_info.value.status_code == 404


def test_duplicate_registration_conflict():
    """Verify 409 Conflict when attempting to register duplicate battery ID."""
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    dup_id = "BAT-SEC-DUPLICATE-ID"
    payload = BatteryRegistration(battery_id=dup_id, chemistry="LFP", rated_capacity_ah=2.5)

    # First registration passes
    res = register_battery(payload)
    assert res["status"] == "REGISTERED"

    # Second registration raises 409
    with pytest.raises(HTTPException) as exc_info:
        register_battery(payload)
    assert exc_info.value.status_code == 409


def test_insufficient_cells_pack_grouping_rejected():
    """Verify 400 Bad Request when available candidate cells are insufficient."""
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    grp_req = CellGroupingRequest(
        chemistry="EXOTIC_NONEXISTENT_CHEM",
        pack_size=4,
        max_soh_variance=3.0,
        reserve_cells=False
    )
    with pytest.raises(HTTPException) as exc_info:
        group_cells(grp_req)
    assert exc_info.value.status_code == 400
    assert "Insufficient available cells" in exc_info.value.detail


def test_inventory_query_isolation_and_filtering():
    """Verify inventory query filtering isolates chemistry without leakage."""
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    # Add isolated test cell
    inventory_collection.update_one(
        {"battery_id": "BAT-SEC-INV-LFP"},
        {"$set": {"battery_id": "BAT-SEC-INV-LFP", "chemistry": "LFP_SEC_TEST", "soh": 85.0, "status": "AVAILABLE"}},
        upsert=True
    )
    inventory_collection.update_one(
        {"battery_id": "BAT-SEC-INV-NMC"},
        {"$set": {"battery_id": "BAT-SEC-INV-NMC", "chemistry": "NMC_SEC_TEST", "soh": 82.0, "status": "AVAILABLE"}},
        upsert=True
    )

    lfp_items = get_inventory(chemistry="LFP_SEC_TEST")
    assert len(lfp_items) == 1
    assert lfp_items[0]["battery_id"] == "BAT-SEC-INV-LFP"

    nmc_items = get_inventory(chemistry="NMC_SEC_TEST")
    assert len(nmc_items) == 1
    assert nmc_items[0]["battery_id"] == "BAT-SEC-INV-NMC"

