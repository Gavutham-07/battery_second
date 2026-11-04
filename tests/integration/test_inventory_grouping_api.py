import pytest
from fastapi import HTTPException
from backend.main import group_cells, get_inventory
from backend.schemas import CellGroupingRequest
from backend.db import (
    test_connection as check_mongo_connection,
    batteries_collection,
    inventory_collection,
)

PREFIX = "BAT-P9-GRP-"


def setup_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": {"$regex": f"^{PREFIX}"}})
        inventory_collection.delete_many({"battery_id": {"$regex": f"^{PREFIX}"}})


def teardown_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": {"$regex": f"^{PREFIX}"}})
        inventory_collection.delete_many({"battery_id": {"$regex": f"^{PREFIX}"}})


def test_get_inventory_filtering():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    # Insert sample items
    inventory_collection.insert_one({"battery_id": f"{PREFIX}F1", "chemistry": "LFP", "soh": 85.0, "status": "AVAILABLE", "quantity": 1})
    inventory_collection.insert_one({"battery_id": f"{PREFIX}F2", "chemistry": "NMC", "soh": 82.0, "status": "AVAILABLE", "quantity": 1})
    inventory_collection.insert_one({"battery_id": f"{PREFIX}F3", "chemistry": "LFP", "soh": 70.0, "status": "RESERVED_FOR_PACK", "quantity": 1})

    # Test filter by status
    avail = get_inventory(status="AVAILABLE")
    avail_ids = [item["battery_id"] for item in avail]
    assert f"{PREFIX}F1" in avail_ids
    assert f"{PREFIX}F2" in avail_ids
    assert f"{PREFIX}F3" not in avail_ids

    # Test filter by chemistry
    lfp_items = get_inventory(chemistry="LFP")
    lfp_ids = [item["battery_id"] for item in lfp_items]
    assert f"{PREFIX}F1" in lfp_ids
    assert f"{PREFIX}F2" not in lfp_ids


def test_group_cells_api_success_and_reservation():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    CHEM = "LFP_GRP_SUCCESS"
    # Clean up test prefix
    inventory_collection.delete_many({"battery_id": {"$regex": f"^{PREFIX}"}})
    batteries_collection.delete_many({"battery_id": {"$regex": f"^{PREFIX}"}})

    # Insert 5 batteries and inventory items with tight SOH cluster
    test_cells = [
        {"id": f"{PREFIX}01", "soh": 83.0},
        {"id": f"{PREFIX}02", "soh": 83.5},
        {"id": f"{PREFIX}03", "soh": 84.0},
        {"id": f"{PREFIX}04", "soh": 84.2},
        {"id": f"{PREFIX}05", "soh": 94.0},  # Higher outlier, should be excluded
    ]

    for c in test_cells:
        batteries_collection.insert_one({
            "battery_id": c["id"],
            "chemistry": CHEM,
            "rated_capacity_ah": 2.5,
            "status": "REGISTERED"
        })
        inventory_collection.insert_one({
            "battery_id": c["id"],
            "chemistry": CHEM,
            "soh": c["soh"],
            "status": "AVAILABLE",
            "quantity": 1
        })

    req = CellGroupingRequest(
        chemistry=CHEM,
        target_capacity_ah=2.5,
        pack_size=4,
        max_soh_variance=3.0,
        reserve_cells=True
    )
    res = group_cells(req)

    assert res["eligible"] is True
    assert res["cell_count"] == 4
    assert res["suitability"] == "APPROVED_FOR_4S_STORAGE"
    assert res["pack_id"].startswith("PACK-4S-")
    assert res["soh_std_dev"] <= 3.0

    selected = res["selected_battery_ids"]
    assert len(selected) == 4
    assert f"{PREFIX}05" not in selected  # Outlier correctly excluded

    # Verify atomic reservation in inventory_collection
    for bid in selected:
        inv = inventory_collection.find_one({"battery_id": bid})
        assert inv["status"] == "RESERVED_FOR_PACK"
        assert inv["pack_id"] == res["pack_id"]

    # Verify status in batteries_collection
    for bid in selected:
        bat = batteries_collection.find_one({"battery_id": bid})
        assert bat["status"] == "PACKED"

    # Verify outlier cell remains AVAILABLE
    outlier = inventory_collection.find_one({"battery_id": f"{PREFIX}05"})
    assert outlier["status"] == "AVAILABLE"


def test_group_cells_api_insufficient_cells_400():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    CHEM_INSUF = "LFP_GRP_INSUF"
    inventory_collection.delete_many({"chemistry": CHEM_INSUF})

    # Only 2 cells available
    for i in range(2):
        inventory_collection.insert_one({
            "battery_id": f"{PREFIX}INSUF-{i}",
            "chemistry": CHEM_INSUF,
            "soh": 85.0,
            "status": "AVAILABLE"
        })

    req = CellGroupingRequest(chemistry=CHEM_INSUF, pack_size=4)
    with pytest.raises(HTTPException) as exc_info:
        group_cells(req)
    assert exc_info.value.status_code == 400
    assert "Insufficient available cells" in exc_info.value.detail


def test_group_cells_api_high_variance_unsuitable():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    CHEM_HIVAR = "LFP_GRP_HIVAR"
    inventory_collection.delete_many({"chemistry": CHEM_HIVAR})

    # Insert 4 cells with high variance spread
    high_var_cells = [45.0, 65.0, 80.0, 95.0]
    for idx, soh_v in enumerate(high_var_cells):
        inventory_collection.insert_one({
            "battery_id": f"{PREFIX}HIVAR-{idx}",
            "chemistry": CHEM_HIVAR,
            "soh": soh_v,
            "status": "AVAILABLE"
        })

    req = CellGroupingRequest(
        chemistry=CHEM_HIVAR,
        pack_size=4,
        max_soh_variance=3.0,
        reserve_cells=True
    )
    res = group_cells(req)

    assert res["eligible"] is False
    assert res["suitability"] == "UNSUITABLE_FOR_GROUPING"
    assert res["soh_std_dev"] > 3.0

    # Ensure cells are NOT reserved since pack is unsuitable
    for idx in range(4):
        inv = inventory_collection.find_one({"battery_id": f"{PREFIX}HIVAR-{idx}"})
        assert inv["status"] == "AVAILABLE"
