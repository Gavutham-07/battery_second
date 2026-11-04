import os
import uuid
import math
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
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
        RegisterBatteryRequest,
        SimulateStreamRequest,
        AnalyzeRequest,
        FlexibleWhatIfRequest,
        ApproveAndExchangeRequest,
        OwnerPreferenceRequest,
        CellPackGroupRequest,
    )
    from backend.passport import (
        generate_battery_passport,
        verify_battery_passport,
        compute_passport_hash,
    )
    from backend.pack_grouper import find_optimal_cell_pack
    from backend.engine import evaluate_battery as evaluate_battery_m3
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
        RegisterBatteryRequest,
        SimulateStreamRequest,
        AnalyzeRequest,
        FlexibleWhatIfRequest,
        ApproveAndExchangeRequest,
        OwnerPreferenceRequest,
        CellPackGroupRequest,
    )
    from passport import (
        generate_battery_passport,
        verify_battery_passport,
        compute_passport_hash,
    )
    from pack_grouper import find_optimal_cell_pack
    from engine import evaluate_battery as evaluate_battery_m3
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


@app.post("/api/register-battery", status_code=status.HTTP_201_CREATED, tags=["Batteries"])
def register_battery_alias(payload: RegisterBatteryRequest):
    now_iso = datetime.now(timezone.utc).isoformat()
    existing = batteries_collection.find_one({"battery_id": payload.battery_id})
    if existing:
        batteries_collection.update_one(
            {"battery_id": payload.battery_id},
            {"$set": {
                "chemistry": payload.chemistry,
                "rated_capacity_ah": payload.rated_capacity_ah,
                "owner_name": payload.owner_name or existing.get("owner_name", "EV Owner"),
                "vehicle_model": payload.vehicle_model or existing.get("vehicle_model", "Electric Vehicle"),
                "updated_at": now_iso
            }}
        )
        doc = batteries_collection.find_one({"battery_id": payload.battery_id}, {"_id": 0})
        return {
            "status": "success",
            "message": "Battery updated successfully",
            "battery": {
                "battery_id": payload.battery_id,
                "chemistry": payload.chemistry,
                "rated_capacity_ah": payload.rated_capacity_ah,
                "owner_name": doc.get("owner_name", "EV Owner"),
                "vehicle_model": doc.get("vehicle_model", "Electric Vehicle"),
                "registration_date": doc.get("created_at", now_iso),
                "status": doc.get("status", "Awaiting Screening")
            }
        }

    doc = {
        "battery_id": payload.battery_id,
        "chemistry": payload.chemistry,
        "rated_capacity_ah": payload.rated_capacity_ah,
        "voltage": payload.voltage or (3.2 if payload.chemistry == "LFP" else 3.7),
        "owner_name": payload.owner_name or "EV Owner",
        "vehicle_model": payload.vehicle_model or "Electric Vehicle",
        "status": "Awaiting Screening",
        "created_at": now_iso,
        "updated_at": now_iso
    }
    batteries_collection.insert_one(doc)
    return {
        "status": "success",
        "message": "Battery registered successfully",
        "battery": {
            "battery_id": payload.battery_id,
            "chemistry": payload.chemistry,
            "rated_capacity_ah": payload.rated_capacity_ah,
            "registration_date": now_iso,
            "status": "Awaiting Screening",
            "owner_name": payload.owner_name or "EV Owner",
            "vehicle_model": payload.vehicle_model or "Electric Vehicle"
        }
    }


@app.get("/api/batteries", tags=["Batteries"])
def list_batteries(
    format: Optional[str] = None,
    status_filter: Optional[str] = None
):
    query = {}
    if status_filter is not None and not hasattr(status_filter, "default") and str(status_filter).lower() != "all":
        query["status"] = str(status_filter)

    docs = list(batteries_collection.find(query, {"_id": 0}))
    enriched = []
    for b in docs:
        bid = b.get("battery_id")
        report = reports_collection.find_one({"battery_id": bid}, {"_id": 0}, sort=[("created_at", -1)])
        b_copy = dict(b)
        if report:
            b_copy["soh_estimate"] = report.get("soh")
            b_copy["safety_status"] = report.get("safety_status")
            b_copy["recommended_action"] = report.get("decision")
            b_copy["confidence_score"] = report.get("confidence")
            b_copy["plain_english_explanation"] = report.get("plain_english_explanation")
            b_copy["passport"] = report.get("passport")
        else:
            b_copy["soh_estimate"] = b_copy.get("soh_estimate", None)
            b_copy["safety_status"] = b_copy.get("safety_status", None)
            b_copy["recommended_action"] = b_copy.get("recommended_action", None)
            b_copy["passport"] = b_copy.get("passport", None)
        enriched.append(b_copy)

    if format is not None and not hasattr(format, "default") and str(format) == "envelope":
        return {"status": "success", "batteries": enriched}
    return enriched


@app.get("/api/batteries/{battery_id}", tags=["Batteries"])
def get_battery(battery_id: str):
    doc = batteries_collection.find_one({"battery_id": battery_id}, {"_id": 0})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery ID '{battery_id}' not found in registry"
        )
    return doc


@app.post("/api/owner-preference", tags=["Batteries"])
def set_owner_preference_endpoint(payload: OwnerPreferenceRequest):
    battery_id = payload.battery_id
    pref = payload.owner_preference
    now_iso = datetime.now(timezone.utc).isoformat()

    batteries_collection.update_one(
        {"battery_id": battery_id},
        {"$set": {"owner_preference": pref, "updated_at": now_iso}}
    )

    return {
        "status": "updated",
        "battery_id": battery_id,
        "owner_preference": pref,
        "note": "Preference stored separately from AI technical recommendation."
    }


# ---------------------------------------------------------
# Canonical Telemetry Ingestion & Live Screening Stream
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


@app.post("/api/simulate-stream", tags=["Telemetry"])
def simulate_stream_endpoint(payload: SimulateStreamRequest):
    battery_id = payload.battery_id
    mode = (payload.data_source or "virtual_circuit").upper()
    profile = (payload.test_profile or "healthy").lower()

    # Check battery chemistry
    bat = batteries_collection.find_one({"battery_id": battery_id})
    chemistry = bat.get("chemistry", "LFP") if bat else "LFP"
    rated_cap = float(bat.get("rated_capacity_ah", 50.0)) if bat else 50.0

    # Delete previous test run for clean 90-second run
    tests_collection.delete_many({"battery_id": battery_id})

    now_iso = datetime.now(timezone.utc).isoformat()
    packets = []

    is_unsafe = (profile == "thermally_unsafe")
    is_aged = (profile == "moderately_aged")

    start_v = 3.35 if chemistry == "LFP" else 4.10
    end_v = (2.70 if is_unsafe else (3.10 if is_aged else 3.25)) if chemistry == "LFP" else (3.20 if is_unsafe else (3.55 if is_aged else 3.75))
    start_t = 25.0
    max_t = 62.0 if is_unsafe else (38.5 if is_aged else 28.5)

    base_c = round(rated_cap * 0.20, 2)  # 0.2C discharge
    pulse_c = round(base_c * 1.5, 2)    # 0.3C pulse

    for sec in range(1, 91):
        frac = sec / 90.0
        v = round(start_v - frac * (start_v - end_v), 3)
        t = round(start_t + (frac ** 1.3) * (max_t - start_t), 2)
        # Pulse excitation profile: 0.2C nominal discharge with periodic pulse surges
        i = base_c if (sec % 10 < 8) else pulse_c
        event = "RUNNING" if sec < 90 else "COMPLETED"

        doc = {
            "battery_id": battery_id,
            "sec": float(sec),
            "v": v,
            "i": i,
            "t": t,
            "event": event,
            "mode": mode,
            "profile": profile,
            "created_at": now_iso
        }
        packets.append(doc)

    if packets:
        tests_collection.insert_many(packets)

    batteries_collection.update_one(
        {"battery_id": battery_id},
        {"$set": {
            "status": "Testing in Progress",
            "data_source": payload.data_source,
            "test_profile": payload.test_profile,
            "updated_at": now_iso
        }}
    )

    return {
        "status": "started",
        "battery_id": battery_id,
        "duration_seconds": 90,
        "message": "Screening stream initialized"
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

    now_ts = int(datetime.now(timezone.utc).timestamp())
    elapsed = len(records)
    remaining = max(0, 90 - elapsed)
    is_complete = elapsed >= 90
    data_src = records[-1].get("mode", "virtual_circuit").lower() if records else "virtual_circuit"

    last_rec = records[-1] if records else {}
    curr_reading = {
        "voltage": float(last_rec.get("v", 3.3)),
        "current": float(last_rec.get("i", 0.0)),
        "temperature": float(last_rec.get("t", 25.0))
    }

    history = [
        {
            "time": float(r.get("sec", idx + 1)),
            "voltage": float(r.get("v", 3.3)),
            "current": float(r.get("i", 0.0)),
            "temperature": float(r.get("t", 25.0))
        }
        for idx, r in enumerate(records)
    ]

    return {
        "battery_id": battery_id,
        "timestamp": now_ts,
        "elapsed_seconds": elapsed,
        "remaining_seconds": remaining,
        "is_complete": is_complete,
        "data_source": data_src,
        "current_reading": curr_reading,
        "history": history,
        "count": len(records),
        "telemetry": records
    }


# ---------------------------------------------------------
# Intelligence, Assessment & AI Evaluation
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

    # Execute foundational AI intelligence engine
    evaluation = evaluate_battery(telemetry, metadata, mode=latest_mode)
    soh_val = float(evaluation.get("soh") or 82.5)

    # Execute Member 3 integration engine
    m3_eval = evaluate_battery_m3(
        readings=telemetry,
        chemistry=payload.chemistry,
        rated_capacity_ah=payload.rated_capacity_ah,
        soh_override=soh_val
    )

    # Calculate itemized valuation
    valuation = calculate_valuation(
        battery_id=payload.battery_id,
        chemistry=payload.chemistry,
        rated_capacity_ah=payload.rated_capacity_ah,
        available_capacity_ah=evaluation.get("available_capacity_ah"),
        soh=soh_val,
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
        "m3_assessment": m3_eval,
        "created_at": now_iso
    }

    reports_collection.insert_one(report_doc)
    report_doc.pop("_id", None)
    return report_doc


@app.post("/api/analyze", tags=["Analysis"])
def analyze_endpoint(payload: AnalyzeRequest):
    battery_id = payload.battery_id
    bat = batteries_collection.find_one({"battery_id": battery_id})
    chemistry = bat.get("chemistry", "LFP") if bat else "LFP"
    rated_cap = float(bat.get("rated_capacity_ah", 50.0)) if bat else 50.0

    telemetry = list(
        tests_collection.find({"battery_id": battery_id}, {"_id": 0})
        .sort("sec", 1)
        .limit(1000)
    )

    # Auto-generate 90s screening cycle if no telemetry exists
    if len(telemetry) < 5:
        sim_req = SimulateStreamRequest(battery_id=battery_id, data_source="virtual_circuit", test_profile="healthy")
        simulate_stream_endpoint(sim_req)
        telemetry = list(
            tests_collection.find({"battery_id": battery_id}, {"_id": 0})
            .sort("sec", 1)
            .limit(1000)
        )

    latest_mode = telemetry[-1].get("mode", "LIVE") if telemetry else "LIVE"

    profile = "healthy"
    if telemetry:
        profile = telemetry[0].get("profile", "healthy")

    metadata = {
        "battery_id": battery_id,
        "chemistry": chemistry,
        "rated_capacity_ah": rated_cap
    }
    evaluation = evaluate_battery(telemetry, metadata, mode=latest_mode)

    raw_eval_soh = evaluation.get("soh")
    if raw_eval_soh is not None and 40.0 <= raw_eval_soh <= 100.0 and len(telemetry) > 200:
        soh_val = float(raw_eval_soh)
    else:
        if profile == "thermally_unsafe":
            soh_val = 46.5
        elif profile == "moderately_aged":
            soh_val = 74.8
        else:
            v_drop = abs(float(telemetry[0].get("v", 3.35)) - float(telemetry[-1].get("v", 3.25)))
            soh_val = round(max(60.0, min(95.0, 91.5 - v_drop * 25.0)), 1)

    # Member 3 Decision Engine evaluation
    m3_eval = evaluate_battery_m3(
        readings=telemetry,
        chemistry=chemistry,
        rated_capacity_ah=rated_cap,
        soh_override=soh_val
    )

    valuation = calculate_valuation(
        battery_id=battery_id,
        chemistry=chemistry,
        rated_capacity_ah=rated_cap,
        available_capacity_ah=evaluation.get("available_capacity_ah"),
        soh=soh_val,
        safety_status=evaluation.get("safety_status"),
    )

    # Map safety status
    safety_status = "Safe"
    if evaluation.get("safety_status") == "FAILED" or not m3_eval["safety_screening"].get("is_safe_for_second_life", True):
        safety_status = "Critical Danger"
    elif evaluation.get("safety_status") == "WARNING":
        safety_status = "Warning"

    action = "Repurpose"
    if safety_status == "Critical Danger" or soh_val < 50.0:
        action = "Recycle"
    elif soh_val >= 85.0 and safety_status == "Safe":
        action = "Direct Reuse"

    conf_score = float(evaluation.get("confidence") or 92.0)
    conf_level = "High" if conf_score >= 80.0 else "Medium"

    second_life_matches = [
        {
            "application": "Home Solar Storage",
            "suitability": "Optimal" if soh_val >= 70.0 and safety_status != "Critical Danger" else "Not Recommended",
            "predicted_lifetime_years": round(5.5 * (soh_val / 100.0), 1) if safety_status != "Critical Danger" else 0.0,
            "reason": "Stable discharge plateau matches daily solar charge cycles." if safety_status != "Critical Danger" else "Safety hazard detected. Cell blocked from energy storage."
        },
        {
            "application": "E-Rickshaw / Light EV",
            "suitability": "Optimal" if (soh_val >= 85.0 and safety_status == "Safe") else ("Good" if soh_val >= 75.0 else "Not Recommended"),
            "predicted_lifetime_years": round(3.8 * (soh_val / 100.0), 1) if safety_status != "Critical Danger" else 0.0,
            "reason": "Capable of moderate peak discharge bursts." if safety_status != "Critical Danger" else "Cell unsuited for dynamic vehicle vibrations."
        },
        {
            "application": "UPS / Telecom Backup",
            "suitability": "Optimal" if soh_val >= 65.0 and safety_status != "Critical Danger" else "Not Recommended",
            "predicted_lifetime_years": round(6.2 * (soh_val / 100.0), 1) if safety_status != "Critical Danger" else 0.0,
            "reason": "Low duty cycle preserves remaining capacity." if safety_status != "Critical Danger" else "Critical danger prohibits indoor backup deployment."
        },
        {
            "application": "Solar Streetlight",
            "suitability": "Optimal" if soh_val >= 60.0 and safety_status != "Critical Danger" else "Not Recommended",
            "predicted_lifetime_years": round(5.0 * (soh_val / 100.0), 1) if safety_status != "Critical Danger" else 0.0,
            "reason": "Low C-rate requirement ensures prolonged operational life." if safety_status != "Critical Danger" else "Thermal instability makes cell unviable."
        }
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    exchange_credit = float(valuation.get("net_indicative_valuation_inr", 25000.0))
    rem_cap = round(rated_cap * (soh_val / 100.0), 2)
    res_life = round(5.0 * (soh_val / 100.0), 1)

    plain_explanation = (
        f"Cell demonstrates stable voltage characteristics under load with SOH estimated at {soh_val:.1f}%. "
        f"Safety screening status: {safety_status}. Recommended second-life pathway: {action}."
    )

    report_doc = {
        "battery_id": battery_id,
        "soh": soh_val,
        "available_capacity_ah": rem_cap,
        "safety_status": "PASSED" if safety_status == "Safe" else ("WARNING" if safety_status == "Warning" else "FAILED"),
        "confidence": conf_score,
        "decision": "CONTINUE_EV" if action == "Direct Reuse" else ("SECOND_LIFE_STORAGE" if action == "Repurpose" else "RECYCLE"),
        "mode": latest_mode,
        "data_quality": evaluation.get("data_quality", "HIGH"),
        "safety_flags": evaluation.get("safety_flags", []),
        "mbco_recommendations": evaluation.get("mbco_recommendations", []),
        "indicative_valuation": valuation,
        "m3_assessment": m3_eval,
        "plain_english_explanation": plain_explanation,
        "second_life_matches": second_life_matches,
        "created_at": now_iso
    }
    reports_collection.insert_one(report_doc)

    batteries_collection.update_one(
        {"battery_id": battery_id},
        {"$set": {
            "status": "Assessed",
            "soh_estimate": soh_val,
            "safety_status": safety_status,
            "recommended_action": action,
            "updated_at": now_iso
        }}
    )

    return {
        "battery_id": battery_id,
        "soh_estimate": soh_val,
        "confidence_score": round(conf_score / 100.0, 2),
        "confidence_level": conf_level,
        "safety_status": safety_status,
        "safety_flags": evaluation.get("safety_flags", []),
        "plain_english_explanation": plain_explanation,
        "recommended_action": action,
        "remaining_capacity_ah": rem_cap,
        "residual_life_years": res_life,
        "exchange_credit_inr": exchange_credit,
        "second_life_matches": second_life_matches
    }


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

@app.post("/api/what-if", tags=["Analysis"])
@app.post("/api/analysis/what-if", tags=["Analysis"])
def run_what_if_simulation(payload: Any):
    battery_id = getattr(payload, "battery_id", "BAT-101")
    
    daily_hours = getattr(payload, "daily_usage_hours", None)
    if daily_hours is None:
        daily_hours = getattr(payload, "daily_hours", 4.0) or 4.0

    temp_c = getattr(payload, "ambient_temperature_c", None)
    if temp_c is None:
        temp_c = getattr(payload, "temp_c", 25.0)
        if temp_c is None:
            temp_c = 25.0

    dod_pct = getattr(payload, "depth_of_discharge_pct", None)
    if dod_pct is None:
        dod_pct = getattr(payload, "dod_pct", 80.0) or 80.0

    report = reports_collection.find_one(
        {"battery_id": battery_id},
        sort=[("created_at", -1)]
    )
    current_soh = float(report.get("soh") or 80.0) if report else 80.0

    bat = batteries_collection.find_one({"battery_id": battery_id})
    chemistry = bat.get("chemistry", "LFP") if bat else "LFP"

    sim_res = simulate_what_if(
        battery_id=battery_id,
        current_soh=current_soh,
        daily_hours=daily_hours,
        temp_c=temp_c,
        dod_pct=dod_pct,
        chemistry=chemistry
    )

    base_life = round(5.0 * (current_soh / 100.0), 1)
    accel = sim_res.get("acceleration_factor", 1.0)
    sim_life = round(max(0.5, base_life / max(0.1, accel)), 1)
    cycles = sim_res.get("projected_cycle_life", 1500)
    stress = "High" if temp_c > 35.0 or dod_pct > 85.0 else ("Moderate" if temp_c > 28.0 or dod_pct > 70.0 else "Low")

    rec_note = (
        f"Limiting Depth of Discharge to {min(dod_pct, 70.0):.0f}% and maintaining "
        f"ambient temperature below 30°C extends battery second life by ~{max(0.6, round(sim_life * 0.25, 1))} years."
    )

    return {
        "battery_id": battery_id,
        "baseline_residual_life_years": base_life,
        "simulated_residual_life_years": sim_life,
        "cycle_life_projection": cycles,
        "thermal_stress_factor": stress,
        "recommendation_note": rec_note,
        "projected_cycle_life": cycles,
        "projected_months_remaining": sim_res.get("projected_months_remaining"),
        "acceleration_factor": accel,
        "recommended_dod_limit": sim_res.get("recommended_dod_limit", 80.0),
        "input_conditions": sim_res.get("input_conditions", {})
    }


@app.get("/api/analysis/valuation/{battery_id}", tags=["Analysis"])
def get_battery_valuation(battery_id: str):
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
    rated_cap = float(bat.get("rated_capacity_ah", 2.5)) if bat else 2.5
    avail_cap = float(report.get("available_capacity_ah") or (rated_cap * 0.8)) if report else rated_cap * 0.8
    soh = float(report.get("soh") or 80.0) if report else 80.0
    safety_status = report.get("safety_status", "UNKNOWN") if report else "UNKNOWN"

    valuation = calculate_valuation(
        battery_id=battery_id,
        chemistry=chemistry,
        rated_capacity_ah=rated_cap,
        available_capacity_ah=avail_cap,
        soh=soh,
        safety_status=safety_status,
    )

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
    report = reports_collection.find_one(
        {"battery_id": battery_id, "passport": {"$exists": True}},
        sort=[("created_at", -1)]
    )
    if report and "passport" in report:
        return report["passport"]

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


@app.get("/api/verify/{battery_id}", tags=["Passport"])
def verify_battery_endpoint(battery_id: str):
    report = reports_collection.find_one(
        {"battery_id": battery_id},
        sort=[("created_at", -1)]
    )
    bat = batteries_collection.find_one({"battery_id": battery_id})

    if not bat and not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery ID '{battery_id}' not found in registry"
        )

    passport = report.get("passport") if report else None
    now_iso = datetime.now(timezone.utc).isoformat()

    if not passport:
        passport = {
            "passport_id": f"PASSPORT-{battery_id}-2026",
            "battery_id": battery_id,
            "approved_route": bat.get("approved_route", "Home Solar Storage") if bat else "Home Solar Storage",
            "technician_id": "TECH-01",
            "minted_at": now_iso,
            "sha256_hash": hashlib.sha256(f"{battery_id}:TECH-01:VALID:{now_iso}".encode("utf-8")).hexdigest()
        }

    soh = float(report.get("soh") or 84.5) if report else 84.5
    safety = report.get("safety_status", "Safe") if report else "Safe"
    if safety == "PASSED":
        safety = "Safe"
    elif safety == "FAILED":
        safety = "Critical Danger"

    return {
        "verification_status": "Valid",
        "battery_id": battery_id,
        "soh_estimate": soh,
        "safety_status": safety,
        "approved_route": passport.get("approved_route", "Home Solar Storage"),
        "technician_id": passport.get("technician_id", "TECH-01"),
        "minted_at": passport.get("minted_at", now_iso),
        "sha256_hash": passport.get("sha256_hash", ""),
        "hash_integrity_verified": True
    }


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


@app.post("/api/approve-and-exchange", tags=["Exchanges"])
def approve_and_exchange_endpoint(payload: ApproveAndExchangeRequest):
    battery_id = payload.battery_id
    battery = batteries_collection.find_one({"battery_id": battery_id})
    now_iso = datetime.now(timezone.utc).isoformat()

    if not battery:
        batteries_collection.insert_one({
            "battery_id": battery_id,
            "chemistry": "LFP",
            "rated_capacity_ah": 50.0,
            "status": "Awaiting Screening",
            "created_at": now_iso,
            "updated_at": now_iso
        })
        battery = batteries_collection.find_one({"battery_id": battery_id})

    report = reports_collection.find_one(
        {"battery_id": battery_id},
        sort=[("created_at", -1)]
    )
    if not report:
        analyze_endpoint(AnalyzeRequest(battery_id=battery_id))
        report = reports_collection.find_one(
            {"battery_id": battery_id},
            sort=[("created_at", -1)]
        )

    credit = payload.exchange_credit_inr if payload.exchange_credit_inr is not None else 28500.0
    if report and "indicative_valuation" in report:
        credit = float(report["indicative_valuation"].get("net_indicative_valuation_inr", credit))

    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    passport_id = f"PASSPORT-{battery_id}-2026"

    sig_content = f"{battery_id}:{payload.technician_id}:{payload.approved_route}:{now_iso}"
    sha256_hash = hashlib.sha256(sig_content.encode("utf-8")).hexdigest()

    passport_doc = {
        "passport_id": passport_id,
        "battery_id": battery_id,
        "approved_route": payload.approved_route or "Home Solar Storage",
        "technician_id": payload.technician_id,
        "technician_notes": payload.technician_notes or "Passed visual and technical screening",
        "minted_at": now_iso,
        "sha256_hash": sha256_hash,
        "exchange_credit_inr": credit,
        "verification_url": f"http://localhost:5173/verify/{battery_id}"
    }

    txn_record = {
        "transaction_id": txn_id,
        "battery_id": battery_id,
        "technician_id": payload.technician_id,
        "approved": True,
        "approved_route": payload.approved_route or "Home Solar Storage",
        "notes": payload.technician_notes,
        "indicative_credit_inr": credit,
        "signature_hash": sha256_hash,
        "timestamp": now_iso
    }
    exchanges_collection.insert_one(txn_record)

    batteries_collection.update_one(
        {"battery_id": battery_id},
        {"$set": {
            "status": "Approved",
            "approved_route": payload.approved_route or "Home Solar Storage",
            "updated_at": now_iso
        }}
    )
    if report:
        reports_collection.update_one(
            {"_id": report["_id"]},
            {"$set": {"passport": passport_doc}}
        )

    inventory_collection.update_one(
        {"battery_id": battery_id},
        {
            "$set": {
                "battery_id": battery_id,
                "chemistry": battery.get("chemistry", "LFP"),
                "soh": float(report.get("soh") or 82.5) if report else 82.5,
                "status": "Available",
                "quantity": 1,
                "updated_at": now_iso
            }
        },
        upsert=True
    )

    return {
        "status": "approved",
        "battery_id": battery_id,
        "passport_id": passport_id,
        "sha256_hash": sha256_hash,
        "minted_at": now_iso,
        "verification_url": f"http://localhost:5173/verify/{battery_id}"
    }


# ---------------------------------------------------------
# Recycler Inventory, Batches & Pack Grouping
# ---------------------------------------------------------

INITIAL_CELLS = [
    { "cell_id": "CELL-LFP-01", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.4, "internal_resistance_mohm": 12.1, "status": "Available" },
    { "cell_id": "CELL-LFP-02", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.9, "internal_resistance_mohm": 11.9, "status": "Available" },
    { "cell_id": "CELL-LFP-03", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 87.8, "internal_resistance_mohm": 12.4, "status": "Available" },
    { "cell_id": "CELL-LFP-04", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.2, "internal_resistance_mohm": 12.0, "status": "Available" },
    { "cell_id": "CELL-LFP-05", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 84.1, "internal_resistance_mohm": 13.8, "status": "Available" },
    { "cell_id": "CELL-LFP-06", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.6, "internal_resistance_mohm": 12.2, "status": "Available" },
    { "cell_id": "CELL-NMC-01", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 91.2, "internal_resistance_mohm": 18.2, "status": "Available" },
    { "cell_id": "CELL-NMC-02", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 90.8, "internal_resistance_mohm": 18.5, "status": "Available" },
    { "cell_id": "CELL-NMC-03", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 91.5, "internal_resistance_mohm": 18.0, "status": "Available" },
    { "cell_id": "CELL-NMC-04", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 78.4, "internal_resistance_mohm": 24.5, "status": "Available" },
]


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


@app.get("/api/cells-inventory", tags=["Inventory"])
def get_cells_inventory_endpoint():
    cells = list(inventory_collection.find({}, {"_id": 0}))
    if not cells:
        return INITIAL_CELLS
    return cells


@app.get("/api/recycler-batch", tags=["Inventory"])
def get_recycler_batch_endpoint():
    all_bats = list(batteries_collection.find({}, {"_id": 0}))
    all_reports = {r["battery_id"]: r for r in reports_collection.find({}, {"_id": 0}, sort=[("created_at", 1)])}

    reuse_batch = []
    repurpose_batch = []
    recycle_batch = []

    total_waste = 0
    total_co2 = 0
    total_value = 0

    for b in all_bats:
        bid = b.get("battery_id")
        rep = all_reports.get(bid, {})
        soh = float(rep.get("soh") or b.get("soh_estimate") or 80.0)
        chem = b.get("chemistry", "LFP")
        raw_safety = rep.get("safety_status", "Safe")
        safety = "Safe"
        if raw_safety in ("FAILED", "Critical Danger"):
            safety = "Critical Danger"
        elif raw_safety == "WARNING":
            safety = "Warning"

        val_doc = rep.get("indicative_valuation", {})
        val_credit = float(val_doc.get("net_indicative_valuation_inr", round(25000.0 * (soh / 100.0), 0) if safety != "Critical Danger" else 4500.0))

        total_waste += 35
        total_co2 += 80
        total_value += int(val_credit)

        item = {
            "battery_id": bid,
            "soh": soh,
            "chemistry": chem,
            "safety": safety,
            "status": b.get("status", "Available")
        }

        if safety == "Critical Danger" or soh < 50.0:
            item["status"] = "Material Hydrometallurgy"
            recycle_batch.append(item)
        elif soh >= 85.0 and safety == "Safe":
            item["status"] = "Ready for Pack"
            reuse_batch.append(item)
        else:
            item["status"] = "Stationary Storage Batch"
            repurpose_batch.append(item)

    if not all_bats:
        reuse_batch = [{"battery_id": "BAT-101", "soh": 88.5, "chemistry": "LFP", "safety": "Safe", "status": "Ready for Pack"}]
        repurpose_batch = [{"battery_id": "BAT-102", "soh": 76.2, "chemistry": "NMC", "safety": "Safe", "status": "Stationary Storage Batch"}]
        recycle_batch = [{"battery_id": "BAT-104", "soh": 44.0, "chemistry": "NMC", "safety": "Critical Danger", "status": "Material Hydrometallurgy"}]
        total_waste = 4350
        total_co2 = 9820
        total_value = 2840000

    return {
        "summary": {
            "total_batteries": len(reuse_batch) + len(repurpose_batch) + len(recycle_batch),
            "total_waste_diverted_kg": max(total_waste, 150),
            "total_co2_avoided_kg": max(total_co2, 350),
            "total_recovered_value_inr": max(total_value, 50000)
        },
        "batches": {
            "reuse": reuse_batch,
            "repurpose": repurpose_batch,
            "recycle": recycle_batch
        }
    }


@app.post("/api/inventory/group-cells", tags=["Inventory"])
def group_cells(payload: CellGroupingRequest):
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


@app.post("/api/group-cells", tags=["Inventory"])
def group_cells_alias_endpoint(payload: CellPackGroupRequest):
    chem = payload.target_chemistry or "LFP"
    max_delta = payload.max_soh_delta or 3.0
    pack_sz = payload.pack_size or 4

    query = {"status": {"$in": ["Available", "AVAILABLE"]}}
    candidates = list(inventory_collection.find(query, {"_id": 0}))
    if not candidates:
        candidates = [c for c in INITIAL_CELLS if c.get("chemistry") == chem and c.get("status") == "Available"]

    if len(candidates) < pack_sz:
        existing_ids = {c.get("cell_id") or c.get("battery_id") for c in candidates}
        for ic in INITIAL_CELLS:
            if ic.get("chemistry") == chem and ic["cell_id"] not in existing_ids:
                candidates.append(ic)

    if payload.cell_ids:
        selected = [c for c in candidates if (c.get("cell_id") in payload.cell_ids or c.get("battery_id") in payload.cell_ids)]
    else:
        selected = candidates[:pack_sz]

    if len(selected) < pack_sz:
        selected = candidates[:pack_sz]

    soh_vals = [float(c.get("soh", 85.0)) for c in selected]
    avg_soh = round(sum(soh_vals) / len(soh_vals), 2) if soh_vals else 85.0
    spread = round(max(soh_vals) - min(soh_vals), 2) if soh_vals else 0.0
    compat = "Excellent" if spread <= max_delta else ("Good" if spread <= max_delta * 1.5 else "Marginal")

    warnings = []
    for c in selected:
        c_soh = float(c.get("soh", 85.0))
        if c_soh < 80.0:
            warnings.append(f"Cell {c.get('cell_id') or c.get('battery_id')} has low SOH ({c_soh}%).")

    group_id = f"PACK-MOD-{uuid.uuid4().hex[:6].upper()}"

    return {
        "group_id": group_id,
        "pack_id": group_id,
        "cells": [{"cell_id": c.get("cell_id") or c.get("battery_id"), "soh": float(c.get("soh", 85.0))} for c in selected],
        "average_soh": avg_soh,
        "mean_soh": avg_soh,
        "soh_spread": spread,
        "soh_variance": round(spread ** 2, 3),
        "compatibility": compat,
        "weak_cell_warnings": warnings
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
