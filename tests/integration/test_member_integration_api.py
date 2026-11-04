import pytest
from backend.main import (
    register_battery_alias,
    list_batteries,
    simulate_stream_endpoint,
    get_live_data,
    analyze_endpoint,
    run_what_if_simulation,
    approve_and_exchange_endpoint,
    verify_battery_endpoint,
    set_owner_preference_endpoint,
    get_recycler_batch_endpoint,
    get_cells_inventory_endpoint,
    group_cells_alias_endpoint,
)
from backend.schemas import (
    RegisterBatteryRequest,
    SimulateStreamRequest,
    AnalyzeRequest,
    FlexibleWhatIfRequest,
    ApproveAndExchangeRequest,
    OwnerPreferenceRequest,
    CellPackGroupRequest,
)
from backend.db import (
    test_connection as check_mongo_connection,
    batteries_collection,
    tests_collection,
    reports_collection,
    exchanges_collection,
    inventory_collection,
)

TEST_BATTERY = "BAT-INTEG-M3M4-01"


def setup_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": TEST_BATTERY})
        tests_collection.delete_many({"battery_id": TEST_BATTERY})
        reports_collection.delete_many({"battery_id": TEST_BATTERY})
        exchanges_collection.delete_many({"battery_id": TEST_BATTERY})
        inventory_collection.delete_many({"battery_id": TEST_BATTERY})


def teardown_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": TEST_BATTERY})
        tests_collection.delete_many({"battery_id": TEST_BATTERY})
        reports_collection.delete_many({"battery_id": TEST_BATTERY})
        exchanges_collection.delete_many({"battery_id": TEST_BATTERY})
        inventory_collection.delete_many({"battery_id": TEST_BATTERY})


def test_member4_battery_registration_and_listing():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    req = RegisterBatteryRequest(
        battery_id=TEST_BATTERY,
        chemistry="LFP",
        rated_capacity_ah=50.0,
        owner_name="Aditya Sharma",
        vehicle_model="Tata Nexon EV Prime"
    )
    res = register_battery_alias(req)
    assert res["status"] == "success"
    assert res["battery"]["battery_id"] == TEST_BATTERY
    assert res["battery"]["status"] == "Awaiting Screening"
    assert res["battery"]["owner_name"] == "Aditya Sharma"

    # Verify listing
    bats = list_batteries()
    found = next((b for b in bats if b["battery_id"] == TEST_BATTERY), None)
    assert found is not None
    assert found["status"] == "Awaiting Screening"


def test_member4_stream_simulation_and_live_data():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    sim_req = SimulateStreamRequest(
        battery_id=TEST_BATTERY,
        data_source="virtual_circuit",
        test_profile="healthy"
    )
    res = simulate_stream_endpoint(sim_req)
    assert res["status"] == "started"
    assert res["battery_id"] == TEST_BATTERY
    assert res["duration_seconds"] == 90

    # Read live telemetry
    live = get_live_data(TEST_BATTERY, limit=100)
    assert live["battery_id"] == TEST_BATTERY
    assert live["count"] == 90
    assert live["is_complete"] is True
    assert "current_reading" in live
    assert live["current_reading"]["voltage"] > 0
    assert len(live["history"]) == 90


def test_member3_member4_ai_analysis_pipeline():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    ana_req = AnalyzeRequest(battery_id=TEST_BATTERY)
    analysis = analyze_endpoint(ana_req)

    assert analysis["battery_id"] == TEST_BATTERY
    assert 50.0 <= analysis["soh_estimate"] <= 100.0
    assert analysis["confidence_level"] in ("High", "Medium", "Low")
    assert analysis["safety_status"] in ("Safe", "Warning", "Critical Danger")
    assert analysis["recommended_action"] in ("Direct Reuse", "Repurpose", "Recycle")
    assert analysis["residual_life_years"] > 0
    assert analysis["exchange_credit_inr"] > 0
    assert len(analysis["second_life_matches"]) >= 3


def test_member4_what_if_simulation():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    req = FlexibleWhatIfRequest(
        battery_id=TEST_BATTERY,
        daily_usage_hours=6.0,
        ambient_temperature_c=30.0,
        depth_of_discharge_pct=70.0
    )
    sim = run_what_if_simulation(req)
    assert sim["battery_id"] == TEST_BATTERY
    assert sim["baseline_residual_life_years"] > 0
    assert sim["simulated_residual_life_years"] > 0
    assert sim["cycle_life_projection"] > 0
    assert "recommendation_note" in sim


def test_technician_approval_and_passport_minting():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    appr_req = ApproveAndExchangeRequest(
        battery_id=TEST_BATTERY,
        technician_id="TECH-04",
        technician_notes="Passed visual and load inspection",
        approved_route="Home Solar Storage",
        exchange_credit_inr=28500.0
    )
    appr = approve_and_exchange_endpoint(appr_req)
    assert appr["status"] == "approved"
    assert appr["battery_id"] == TEST_BATTERY
    assert appr["passport_id"].startswith("PASSPORT-")
    assert len(appr["sha256_hash"]) == 64
    assert "/verify/" in appr["verification_url"]

    # Test public verification
    ver = verify_battery_endpoint(TEST_BATTERY)
    assert ver["verification_status"] == "Valid"
    assert ver["battery_id"] == TEST_BATTERY
    assert ver["hash_integrity_verified"] is True
    assert ver["technician_id"] == "TECH-04"


def test_owner_preference_and_recycler_batch_sorting():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    pref_req = OwnerPreferenceRequest(
        battery_id=TEST_BATTERY,
        owner_preference="Sell / Exchange"
    )
    res = set_owner_preference_endpoint(pref_req)
    assert res["status"] == "updated"
    assert res["owner_preference"] == "Sell / Exchange"

    # Recycler batch
    batches = get_recycler_batch_endpoint()
    assert "summary" in batches
    assert batches["summary"]["total_batteries"] >= 1
    assert "reuse" in batches["batches"]
    assert "repurpose" in batches["batches"]
    assert "recycle" in batches["batches"]


def test_cell_inventory_and_pack_grouping():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    inv = get_cells_inventory_endpoint()
    assert len(inv) >= 4

    grp_req = CellPackGroupRequest(
        target_chemistry="LFP",
        max_soh_delta=3.0,
        pack_size=4
    )
    grp = group_cells_alias_endpoint(grp_req)
    assert "group_id" in grp
    assert len(grp["cells"]) == 4
    assert grp["average_soh"] > 0
    assert grp["soh_spread"] >= 0
    assert grp["compatibility"] in ("Excellent", "Good", "Marginal")
