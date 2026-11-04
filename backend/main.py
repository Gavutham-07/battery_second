import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

try:
    from backend.db import (
        test_connection,
        init_indexes,
        MONGO_DB_NAME,
        batteries_collection,
        tests_collection,
        reports_collection,
        exchanges_collection,
        inventory_collection,
    )
    from backend.schemas import (
        BatteryRegistration,
        TelemetryPacket,
        AnalysisRequest,
        AnalysisReport,
        WhatIfRequest,
        InventoryItem,
        ExchangeApproval,
        PassportGenerateRequest,
        CellGroupingRequest,
    )
    from backend.passport import (
        generate_battery_passport,
        verify_battery_passport,
        compute_passport_hash,
    )
    from backend.pack_grouper import find_optimal_cell_pack
    from ai_engine import evaluate_battery, calculate_valuation, simulate_what_if
except ImportError:
    from db import (
        test_connection,
        init_indexes,
        MONGO_DB_NAME,
        batteries_collection,
        tests_collection,
        reports_collection,
        exchanges_collection,
        inventory_collection,
    )
    from schemas import (
        BatteryRegistration,
        TelemetryPacket,
        AnalysisRequest,
        AnalysisReport,
        WhatIfRequest,
        InventoryItem,
        ExchangeApproval,
        PassportGenerateRequest,
        CellGroupingRequest,
    )
    from passport import (
        generate_battery_passport,
        verify_battery_passport,
        compute_passport_hash,
    )
    from pack_grouper import find_optimal_cell_pack
    from ai_engine import evaluate_battery, calculate_valuation, simulate_what_if


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database indexes on startup
    init_indexes()
    yield


app = FastAPI(
    title="ReVolt API",
    description="Smart EV Battery Assessment, Valuation and Circularity Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# System & Health
# ---------------------------------------------------------

@app.get("/", tags=["System"])
def root():
    return {
        "name": "ReVolt API",
        "description": "Smart EV Battery Assessment, Valuation and Circularity Platform",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health", tags=["System"])
def health_check():
    db_ok = test_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "database_name": MONGO_DB_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ---------------------------------------------------------
# Battery Registration & Lifecycle
# ---------------------------------------------------------

@app.post("/api/batteries", status_code=status.HTTP_201_CREATED, tags=["Batteries"])
def register_battery(payload: BatteryRegistration):
    # Check for existing battery ID
    existing = batteries_collection.find_one({"battery_id": payload.battery_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Battery ID '{payload.battery_id}' already registered"
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    doc = {
        "battery_id": payload.battery_id,
        "chemistry": payload.chemistry,
        "rated_capacity_ah": payload.rated_capacity_ah,
        "voltage": payload.voltage,
        "manufacturer": payload.manufacturer,
        "manufacture_date": payload.manufacture_date,
        "source_vehicle": payload.source_vehicle,
        "status": "REGISTERED",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        batteries_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Battery ID '{payload.battery_id}' already registered"
        )

    return {
        "message": "Battery registered successfully",
        "battery_id": payload.battery_id,
        "status": "REGISTERED",
        "created_at": now_iso
    }


@app.get("/api/batteries", tags=["Batteries"])
def list_batteries():
    return list(batteries_collection.find({}, {"_id": 0}))


@app.get("/api/batteries/{battery_id}", tags=["Batteries"])
def get_battery(battery_id: str):
    doc = batteries_collection.find_one({"battery_id": battery_id}, {"_id": 0})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery ID '{battery_id}' not found in registry"
        )
    return doc


# ---------------------------------------------------------
# Canonical Telemetry Ingestion & History
# ---------------------------------------------------------

ALLOWED_MODES = {"LIVE", "REPLAY", "VIRTUAL", "DATASET"}

@app.post("/api/live-data", tags=["Telemetry"])
def ingest_live_data(
    packet: TelemetryPacket,
    x_data_mode: Optional[str] = Header(default="LIVE")
):
    mode = x_data_mode.upper() if x_data_mode and x_data_mode.upper() in ALLOWED_MODES else "LIVE"
    now_iso = datetime.now(timezone.utc).isoformat()

    telemetry_doc = {
        "battery_id": packet.battery_id,
        "sec": packet.sec,
        "v": packet.v,
        "i": packet.i,
        "t": packet.t,
        "event": packet.event,
        "mode": mode,
        "created_at": now_iso
    }

    tests_collection.insert_one(telemetry_doc)

    return {
        "status": "acknowledged",
        "battery_id": packet.battery_id,
        "sec": packet.sec,
        "mode": mode
    }


@app.get("/api/live-data/{battery_id}", tags=["Telemetry"])
def get_live_data(
    battery_id: str,
    limit: int = Query(default=100, ge=1, le=1000)
):
    records = list(
        tests_collection.find({"battery_id": battery_id}, {"_id": 0})
        .sort("sec", 1)
        .limit(limit)
    )
    return {
        "battery_id": battery_id,
        "count": len(records),
        "telemetry": records
    }


# ---------------------------------------------------------
# Intelligence, Assessment & Reports
# ---------------------------------------------------------

@app.post("/api/analysis/evaluate", tags=["Analysis"])
def run_evaluation(payload: AnalysisRequest):
    # Retrieve telemetry series for the battery
    telemetry = list(
        tests_collection.find({"battery_id": payload.battery_id}, {"_id": 0})
        .sort("sec", 1)
        .limit(1000)
    )

    latest_mode = telemetry[-1].get("mode", "LIVE") if telemetry else "LIVE"
    metadata = {
        "battery_id": payload.battery_id,
        "chemistry": payload.chemistry,
        "rated_capacity_ah": payload.rated_capacity_ah
    }

    # Execute Member 3's AI intelligence engine (including MBCO optimization)
    evaluation = evaluate_battery(telemetry, metadata, mode=latest_mode)

    # Calculate itemized valuation
    valuation = calculate_valuation(
        battery_id=payload.battery_id,
        chemistry=payload.chemistry,
        rated_capacity_ah=payload.rated_capacity_ah,
        available_capacity_ah=evaluation.get("available_capacity_ah"),
        soh=evaluation.get("soh"),
        safety_status=evaluation.get("safety_status"),
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    report_doc = {
        "battery_id": evaluation["battery_id"],
        "soh": evaluation["soh"],
        "available_capacity_ah": evaluation["available_capacity_ah"],
        "safety_status": evaluation["safety_status"],
        "confidence": evaluation["confidence"],
        "decision": evaluation["decision"],
        "mode": evaluation["mode"],
        "data_quality": evaluation["data_quality"],
        "safety_flags": evaluation["safety_flags"],
        "mbco_recommendations": evaluation["mbco_recommendations"],
        "indicative_valuation": valuation,
        "created_at": now_iso
    }

    reports_collection.insert_one(report_doc)
    report_doc.pop("_id", None)
    return report_doc


@app.get("/api/analysis/reports/{battery_id}", tags=["Analysis"])
def get_analysis_report(battery_id: str):
    report = reports_collection.find_one(
        {"battery_id": battery_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis report found for battery '{battery_id}'"
        )
    return report


@app.get("/api/analysis/mbco/{battery_id}", tags=["Analysis"])
def get_mbco_recommendations(battery_id: str):
    report = reports_collection.find_one(
        {"battery_id": battery_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No MBCO evaluation found for battery '{battery_id}'"
        )
    return {
        "battery_id": battery_id,
        "decision": report.get("decision"),
        "safety_status": report.get("safety_status"),
        "soh": report.get("soh"),
        "recommendations": report.get("mbco_recommendations", [])
    }


# ---------------------------------------------------------
# Valuation & What-If Simulation
# ---------------------------------------------------------

@app.post("/api/analysis/what-if", tags=["Analysis"])
def run_what_if_simulation(payload: WhatIfRequest):
    # Lookup latest assessment report to obtain current SOH
    report = reports_collection.find_one(
        {"battery_id": payload.battery_id},
        sort=[("created_at", -1)]
    )
    current_soh = report.get("soh") if report else 80.0

    # Obtain chemistry if registered
    bat = batteries_collection.find_one({"battery_id": payload.battery_id})
    chemistry = bat.get("chemistry", "LFP") if bat else "LFP"

    result = simulate_what_if(
        battery_id=payload.battery_id,
        current_soh=current_soh,
        daily_hours=payload.daily_hours,
        temp_c=payload.temp_c,
        dod_pct=payload.dod_pct,
        chemistry=chemistry
    )
    return result


@app.get("/api/analysis/valuation/{battery_id}", tags=["Analysis"])
def get_battery_valuation(battery_id: str):
    # Lookup latest report
    report = reports_collection.find_one(
        {"battery_id": battery_id},
        sort=[("created_at", -1)]
    )
    bat = batteries_collection.find_one({"battery_id": battery_id})

    if not report and not bat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery ID '{battery_id}' has not been evaluated or registered"
        )

    chemistry = bat.get("chemistry", "LFP") if bat else "LFP"
    rated_cap = bat.get("rated_capacity_ah", 2.5) if bat else 2.5
    avail_cap = report.get("available_capacity_ah", rated_cap * 0.8) if report else rated_cap * 0.8
    soh = report.get("soh", 80.0) if report else 80.0
    safety_status = report.get("safety_status", "UNKNOWN") if report else "UNKNOWN"

    valuation = calculate_valuation(
        battery_id=battery_id,
        chemistry=chemistry,
        rated_capacity_ah=rated_cap,
        available_capacity_ah=avail_cap,
        soh=soh,
        safety_status=safety_status,
    )

    # Persist latest valuation into reports collection if report exists
    if report:
        reports_collection.update_one(
            {"_id": report["_id"]},
            {"$set": {"indicative_valuation": valuation}}
        )

    return valuation


@app.get("/api/exchanges/{battery_id}", tags=["Exchanges"])
def get_exchanges(battery_id: str):
    txns = list(
        exchanges_collection.find({"battery_id": battery_id}, {"_id": 0})
        .sort("timestamp", -1)
    )
    return {
        "battery_id": battery_id,
        "exchanges": txns
    }


# ---------------------------------------------------------
# Digital Battery Passport & Cryptography
# ---------------------------------------------------------

@app.post("/api/passport/generate", tags=["Passport"], status_code=status.HTTP_201_CREATED)
def create_passport(payload: PassportGenerateRequest):
    battery = batteries_collection.find_one({"battery_id": payload.battery_id})
    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery '{payload.battery_id}' not found in registry"
        )

    report = reports_collection.find_one(
        {"battery_id": payload.battery_id},
        sort=[("created_at", -1)]
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment report found for battery '{payload.battery_id}'. Cell must be evaluated before passport issuance."
        )

    passport = generate_battery_passport(battery, report)

    # Persist passport inside report and update battery status
    reports_collection.update_one(
        {"_id": report["_id"]},
        {"$set": {"passport": passport}}
    )
    batteries_collection.update_one(
        {"battery_id": payload.battery_id},
        {"$set": {"status": "PASSPORT_ISSUED", "updated_at": datetime.now(timezone.utc)}}
    )

    return passport


@app.post("/api/passport/verify", tags=["Passport"])
def verify_passport(passport: dict):
    result = verify_battery_passport(passport)
    return result


@app.get("/api/passport/{battery_id}", tags=["Passport"])
def get_passport(battery_id: str):
    # Lookup latest report with passport
    report = reports_collection.find_one(
        {"battery_id": battery_id, "passport": {"$exists": True}},
        sort=[("created_at", -1)]
    )
    if report and "passport" in report:
        return report["passport"]

    # Fallback: if battery and report exist, generate on the fly
    battery = batteries_collection.find_one({"battery_id": battery_id})
    latest_report = reports_collection.find_one(
        {"battery_id": battery_id},
        sort=[("created_at", -1)]
    )
    if not battery or not latest_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Passport not found for battery '{battery_id}'"
        )

    passport = generate_battery_passport(battery, latest_report)
    reports_collection.update_one(
        {"_id": latest_report["_id"]},
        {"$set": {"passport": passport}}
    )
    return passport


# ---------------------------------------------------------
# Technician Approval & Exchange Transactions
# ---------------------------------------------------------

@app.post("/api/exchanges/approve", tags=["Exchanges"])
def approve_exchange(payload: ExchangeApproval):
    battery = batteries_collection.find_one({"battery_id": payload.battery_id})
    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery '{payload.battery_id}' not found in registry"
        )

    report = reports_collection.find_one(
        {"battery_id": payload.battery_id},
        sort=[("created_at", -1)]
    )

    credit = 0.0
    if payload.approved:
        if report and "indicative_valuation" in report:
            credit = float(report["indicative_valuation"].get("net_indicative_valuation_inr", 0.0))
        else:
            chemistry = battery.get("chemistry", "LFP")
            rated_cap = float(battery.get("rated_capacity_ah", 2.5))
            avail_cap = float(report.get("available_capacity_ah") or (rated_cap * 0.8)) if report else rated_cap * 0.8
            soh = float(report.get("soh") or 80.0) if report else 80.0
            safety_status = report.get("safety_status", "UNKNOWN") if report else "UNKNOWN"
            val = calculate_valuation(
                battery_id=payload.battery_id,
                chemistry=chemistry,
                rated_capacity_ah=rated_cap,
                available_capacity_ah=avail_cap,
                soh=soh,
                safety_status=safety_status
            )
            credit = float(val.get("net_indicative_valuation_inr", 0.0))

    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()

    sig_content = f"{payload.battery_id}:{payload.technician_id}:{payload.approved}:{ts}"
    signature_hash = hashlib.sha256(sig_content.encode("utf-8")).hexdigest()

    txn_record = {
        "transaction_id": txn_id,
        "battery_id": payload.battery_id,
        "technician_id": payload.technician_id,
        "approved": payload.approved,
        "notes": payload.notes,
        "indicative_credit_inr": credit,
        "signature_hash": signature_hash,
        "timestamp": ts
    }
    exchanges_collection.insert_one(txn_record)

    new_status = "EXCHANGE_APPROVED" if payload.approved else "EXCHANGE_REJECTED"
    batteries_collection.update_one(
        {"battery_id": payload.battery_id},
        {"$set": {"status": new_status, "updated_at": ts}}
    )

    if payload.approved:
        soh_val = float(report.get("soh") or 80.0) if report else 80.0
        inventory_collection.update_one(
            {"battery_id": payload.battery_id},
            {
                "$set": {
                    "battery_id": payload.battery_id,
                    "chemistry": battery.get("chemistry", "LFP"),
                    "soh": soh_val,
                    "status": "AVAILABLE",
                    "quantity": 1,
                    "updated_at": ts
                }
            },
            upsert=True
        )

    return {
        "transaction_id": txn_id,
        "battery_id": payload.battery_id,
        "status": "APPROVED" if payload.approved else "REJECTED",
        "indicative_credit_inr": credit,
        "timestamp": ts
    }


# ---------------------------------------------------------
# Recycler Inventory & Pack Grouping
# ---------------------------------------------------------

@app.get("/api/inventory", tags=["Inventory"])
def get_inventory(
    status: Optional[str] = None,
    chemistry: Optional[str] = None
):
    query = {}
    if status is not None and not hasattr(status, "default"):
        query["status"] = str(status)
    if chemistry is not None and not hasattr(chemistry, "default"):
        query["chemistry"] = str(chemistry)
    return list(inventory_collection.find(query, {"_id": 0}))


@app.post("/api/inventory/group-cells", tags=["Inventory"])
def group_cells(payload: CellGroupingRequest):
    # Query candidate cells from inventory with status AVAILABLE
    query = {"status": "AVAILABLE"}
    if payload.chemistry:
        query["chemistry"] = payload.chemistry

    candidates = list(inventory_collection.find(query, {"_id": 0}))

    result = find_optimal_cell_pack(
        cells=candidates,
        chemistry=payload.chemistry,
        pack_size=payload.pack_size,
        max_std_dev=payload.max_soh_variance,
        target_capacity_ah=payload.target_capacity_ah
    )

    if not result.get("eligible") and result.get("suitability") == "INSUFFICIENT_CELLS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Insufficient available cells for pack grouping")
        )

    # If suitable and reserve_cells is True, update inventory and batteries status
    if result.get("eligible") and payload.reserve_cells:
        selected_ids = result.get("selected_battery_ids", [])
        pack_id = result.get("pack_id")
        ts = datetime.now(timezone.utc).isoformat()

        inventory_collection.update_many(
            {"battery_id": {"$in": selected_ids}},
            {"$set": {"status": "RESERVED_FOR_PACK", "pack_id": pack_id, "updated_at": ts}}
        )
        batteries_collection.update_many(
            {"battery_id": {"$in": selected_ids}},
            {"$set": {"status": "PACKED", "updated_at": ts}}
        )

    return result


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
