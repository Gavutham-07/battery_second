import pytest
import copy
from fastapi import HTTPException
from backend.main import (
    create_passport,
    verify_passport,
    get_passport,
    approve_exchange,
    get_exchanges,
)
from backend.schemas import PassportGenerateRequest, ExchangeApproval
from backend.db import (
    test_connection as check_mongo_connection,
    batteries_collection,
    reports_collection,
    exchanges_collection,
    inventory_collection,
)

TEST_BAT_ID = "BAT-P8-INT-TEST-01"


def setup_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": TEST_BAT_ID})
        reports_collection.delete_many({"battery_id": TEST_BAT_ID})
        exchanges_collection.delete_many({"battery_id": TEST_BAT_ID})
        inventory_collection.delete_many({"battery_id": TEST_BAT_ID})


def teardown_module(module):
    if check_mongo_connection():
        batteries_collection.delete_many({"battery_id": TEST_BAT_ID})
        reports_collection.delete_many({"battery_id": TEST_BAT_ID})
        exchanges_collection.delete_many({"battery_id": TEST_BAT_ID})
        inventory_collection.delete_many({"battery_id": TEST_BAT_ID})


def test_passport_generation_and_retrieval_flow():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    # 1. Register battery
    batteries_collection.insert_one({
        "battery_id": TEST_BAT_ID,
        "chemistry": "LFP",
        "rated_capacity_ah": 2.5,
        "manufacturer": "EVE Energy",
        "source_vehicle": "Ola S1 Pro",
        "status": "REGISTERED"
    })

    # 2. Insert analytical report
    reports_collection.insert_one({
        "battery_id": TEST_BAT_ID,
        "soh": 85.0,
        "available_capacity_ah": 2.125,
        "safety_status": "PASSED",
        "confidence": 91.0,
        "decision": "SECOND_LIFE_STORAGE",
        "mode": "LIVE",
        "created_at": "2026-11-05T02:00:00Z"
    })

    # 3. Generate passport
    req = PassportGenerateRequest(battery_id=TEST_BAT_ID)
    passport = create_passport(req)

    assert passport["battery_id"] == TEST_BAT_ID
    assert passport["chemistry"] == "LFP"
    assert passport["assessment"]["soh"] == 85.0
    assert "integrity_hash" in passport
    assert len(passport["integrity_hash"]) == 64
    assert "qr_code" in passport

    # 4. Verify battery status updated in database
    bat = batteries_collection.find_one({"battery_id": TEST_BAT_ID})
    assert bat["status"] == "PASSPORT_ISSUED"

    # 5. Verify retrieval via GET /api/passport/{battery_id}
    retrieved = get_passport(TEST_BAT_ID)
    assert retrieved["battery_id"] == TEST_BAT_ID
    assert retrieved["integrity_hash"] == passport["integrity_hash"]


def test_passport_verification_endpoint():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    # Retrieve valid passport
    passport = get_passport(TEST_BAT_ID)

    # Verify genuine passport
    verif_res = verify_passport(passport)
    assert verif_res["valid"] is True
    assert verif_res["matched"] is True
    assert verif_res["error"] is None

    # Verify tampered passport (fraudulent SOH increase)
    tampered = copy.deepcopy(passport)
    tampered["assessment"]["soh"] = 99.0
    tamper_res = verify_passport(tampered)
    assert tamper_res["valid"] is False
    assert tamper_res["matched"] is False
    assert "Tamper detected" in tamper_res["error"]


def test_passport_not_found():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    with pytest.raises(HTTPException) as exc_info:
        get_passport("BAT-DOES-NOT-EXIST-404")
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info2:
        create_passport(PassportGenerateRequest(battery_id="BAT-DOES-NOT-EXIST-404"))
    assert exc_info2.value.status_code == 404


def test_exchange_approval_and_inventory_dispatch():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    # Submit technician approval
    approval_req = ExchangeApproval(
        battery_id=TEST_BAT_ID,
        technician_id="TECH-P8-101",
        approved=True,
        notes="Cells tested on bench. Terminals intact, zero swelling."
    )
    res = approve_exchange(approval_req)

    assert res["battery_id"] == TEST_BAT_ID
    assert res["status"] == "APPROVED"
    assert res["indicative_credit_inr"] > 0.0
    assert res["transaction_id"].startswith("TXN-")
    assert "timestamp" in res

    # Verify persistence in exchanges collection
    txn = exchanges_collection.find_one({"transaction_id": res["transaction_id"]})
    assert txn is not None
    assert txn["technician_id"] == "TECH-P8-101"
    assert "signature_hash" in txn

    # Verify battery status updated to EXCHANGE_APPROVED
    bat = batteries_collection.find_one({"battery_id": TEST_BAT_ID})
    assert bat["status"] == "EXCHANGE_APPROVED"

    # Verify cell added to recycler inventory collection as AVAILABLE
    inv = inventory_collection.find_one({"battery_id": TEST_BAT_ID})
    assert inv is not None
    assert inv["status"] == "AVAILABLE"
    assert inv["soh"] == 85.0


def test_exchange_rejection_flow():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    REJECT_BAT_ID = "BAT-P8-REJECT-01"
    batteries_collection.insert_one({
        "battery_id": REJECT_BAT_ID,
        "chemistry": "LFP",
        "rated_capacity_ah": 2.5,
        "status": "REGISTERED"
    })

    approval_req = ExchangeApproval(
        battery_id=REJECT_BAT_ID,
        technician_id="TECH-P8-102",
        approved=False,
        notes="Physical case dented and terminal rusted. Rejected."
    )
    res = approve_exchange(approval_req)

    assert res["battery_id"] == REJECT_BAT_ID
    assert res["status"] == "REJECTED"
    assert res["indicative_credit_inr"] == 0.0

    # Verify battery status updated to EXCHANGE_REJECTED
    bat = batteries_collection.find_one({"battery_id": REJECT_BAT_ID})
    assert bat["status"] == "EXCHANGE_REJECTED"

    # Cleanup
    batteries_collection.delete_one({"battery_id": REJECT_BAT_ID})
    exchanges_collection.delete_many({"battery_id": REJECT_BAT_ID})


def test_get_exchanges_history():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable")

    hist = get_exchanges(TEST_BAT_ID)
    assert hist["battery_id"] == TEST_BAT_ID
    assert len(hist["exchanges"]) >= 1
    assert hist["exchanges"][0]["technician_id"] == "TECH-P8-101"

