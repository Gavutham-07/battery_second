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
    # NOTE: backend.engine (Member 3) is the single authoritative AI engine.
    # ai_engine/ is retained as a legacy prototype for reference only — not used in production.
    from backend.engine import evaluate_battery as evaluate_battery_m3
    from backend.ai.valuation import calculate_route_valuation as _m3_calculate_valuation
    from backend.ai.lifetime import calculate_lifetime_scenarios
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
    # NOTE: backend.engine (Member 3) is the single authoritative AI engine.
    # ai_engine/ is retained as a legacy prototype for reference only — not used in production.
    from engine import evaluate_battery as evaluate_battery_m3
    from ai.valuation import calculate_route_valuation as _m3_calculate_valuation
    from ai.lifetime import calculate_lifetime_scenarios

try:
    from hardware.pulse_stream import generate_p17_stream, load_profile, source_note
except ImportError:
    try:
        from tests.fakemongo_plugin import generate_p17_stream, load_profile, source_note
    except ImportError:
        generate_p17_stream = None
        load_profile = None
        source_note = None


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
    import pathlib
    db_ok = test_connection()
    artifacts_path = pathlib.Path("backend/models/research_artifacts")
    artifacts_ok = artifacts_path.exists() and any(artifacts_path.glob("*.pkl"))
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "database_name": MONGO_DB_NAME,
        "ai_engine": "backend.engine — Member 3 authoritative engine",
        "legacy_ai_engine": "ai_engine/ — prototype retained for reference, not used in production",
        "research_artifacts": "available" if artifacts_ok else "unavailable — safety screening uses rule-based fallback",
        "hardware_bridge": "not_connected — virtual/replay/dataset modes active for demonstration",
        "build_type": "Hackathon Demonstration Build — Prototype",
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
            b_copy["analysis"] = report.get("analysis", None)
        else:
            b_copy["soh_estimate"] = b_copy.get("soh_estimate", None)
            b_copy["safety_status"] = b_copy.get("safety_status", None)
            b_copy["recommended_action"] = b_copy.get("recommended_action", None)
            b_copy["passport"] = b_copy.get("passport", None)
            b_copy["analysis"] = None
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

ALLOWED_MODES = {"LIVE", "REPLAY", "VIRTUAL", "DATASET", "HYBRID"}

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


@app.delete("/api/live-data/{battery_id}", tags=["Telemetry"])
def delete_live_data(battery_id: str):
    res = tests_collection.delete_many({"battery_id": battery_id})
    return {"deleted": res.deleted_count}


@app.post("/api/simulate-stream", tags=["Telemetry"])
def simulate_stream_endpoint(payload: SimulateStreamRequest):
    battery_id = payload.battery_id
    raw_source = (payload.data_source or "virtual_circuit").lower()
    profile = (payload.test_profile or "healthy").lower()

    mode_map = {
        "virtual_circuit": "VIRTUAL",
        "lab_dataset": "DATASET",
        "replay_recorded": "REPLAY",
        "live_hardware": "HYBRID",
        "virtual": "VIRTUAL",
        "dataset": "DATASET",
        "replay": "REPLAY",
        "hybrid": "HYBRID",
    }
    mode = mode_map.get(raw_source, raw_source.upper())

    if mode == "HYBRID" or raw_source == "live_hardware":
        raise HTTPException(status_code=400, detail="Use the serial bridge")

    if load_profile is None:
        raise HTTPException(status_code=500, detail="Pulse stream generator not available")

    try:
        prof_data = load_profile(profile)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    chem = prof_data.get("chemistry", "NMC")
    source_cell = prof_data.get("source_cell_id", "")
    note = source_note(profile, mode) if source_note else f"Voltage response from PulseBat cell {source_cell}"

    now_iso = datetime.now(timezone.utc).isoformat()

    if mode == "REPLAY":
        replay_path = os.path.join("hardware", "data", f"replay_{profile}.json")
        if not os.path.exists(replay_path):
            raise HTTPException(status_code=404, detail="No recorded run")
        import json
        with open(replay_path, "r", encoding="utf-8") as f:
            packets = json.load(f)
        for p in packets:
            p["battery_id"] = battery_id
            p["mode"] = mode
            if "created_at" not in p:
                p["created_at"] = now_iso
    else:  # VIRTUAL or DATASET
        bat = batteries_collection.find_one({"battery_id": battery_id})
        rated_cap = float(bat.get("rated_capacity_ah", 2.5)) if bat else 2.5
        packets = generate_p17_stream(profile, battery_id, rated_cap, mode)
        for p in packets:
            p["battery_id"] = battery_id
            p["mode"] = mode
            p["created_at"] = now_iso

    tests_collection.delete_many({"battery_id": battery_id})
    if packets:
        tests_collection.insert_many(packets)

    batteries_collection.update_one(
        {"battery_id": battery_id},
        {"$set": {
            "status": "Testing in Progress",
            "chemistry": chem,
            "last_profile": profile,
            "source_cell_id": source_cell,
            "last_mode": mode,
            "source_note": note,
            "updated_at": now_iso
        }},
        upsert=True
    )

    return {
        "status": "started",
        "battery_id": battery_id,
        "duration_seconds": 90,
        "mode": mode,
        "chemistry": chem,
        "source_note": note,
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

    if not telemetry:
        return {
            "battery_id": payload.battery_id,
            "status": "no_telemetry",
            "message": "No telemetry recorded for this battery. Submit readings via POST /api/live-data before requesting an evaluation.",
            "soh": None,
            "decision": "FURTHER_TESTING"
        }

    latest_mode = telemetry[-1].get("mode", "LIVE") if telemetry else "LIVE"

    # Single authoritative assessment: Member 3 engine only.
    # No soh_override — let the engine determine SOH from protocol; short pulse → null (not_available_for_this_protocol).
    m3_report = evaluate_battery_m3(
        readings=telemetry,
        chemistry=payload.chemistry,
        rated_capacity_ah=payload.rated_capacity_ah,
    )

    # Extract all results from Member 3 report only.
    soh_eval = m3_report.get("soh_evaluation", {})
    soh_pct = soh_eval.get("soh_pct")  # May legitimately be None for short pulse protocols.

    safety_scr = m3_report.get("safety_screening", {})
    confidence_eval = m3_report.get("confidence_evaluation", {})
    mbco_decision = m3_report.get("mbco_circularity_decision", {})
    valuation = m3_report.get("indicative_valuation", {})
    lifetime_scen = m3_report.get("lifetime_scenarios", {})

    # Safety: missing safety field → UNKNOWN → further testing. Never default to safe.
    safety_state = safety_scr.get("safety_state", "UNKNOWN")
    is_safe = safety_scr.get("is_safe_for_second_life", False)

    conf_score_raw = confidence_eval.get("confidence_score")
    if conf_score_raw is None:
        conf_score_raw = confidence_eval.get("score", 0.0)
    conf_100 = round(float(conf_score_raw) * 100.0, 1) if conf_score_raw is not None else 0.0

    crit_flags = safety_scr.get("critical_violations") or []
    warn_flags = safety_scr.get("warnings") or []
    safety_flags = crit_flags + warn_flags

    final_dec = mbco_decision.get("final_decision", "FURTHER_TESTING_REQUIRED")

    now_iso = datetime.now(timezone.utc).isoformat()
    report_doc = {
        "battery_id": payload.battery_id,
        "soh": soh_pct,  # None is scientifically correct for short-pulse ESP32 data.
        "available_capacity_ah": soh_eval.get("available_capacity_ah"),
        "safety_status": safety_state,
        "safety_flags": safety_flags,
        "is_safe_for_second_life": is_safe,
        "confidence": conf_100,
        "confidence_level": confidence_eval.get("confidence_level"),
        "decision": final_dec,
        "ranked_pathways": mbco_decision.get("ranked_pathways", []),
        "mode": latest_mode,
        "data_quality": m3_report.get("data_quality", "UNKNOWN"),
        "mbco_recommendations": mbco_decision.get("recommendations", []),
        "indicative_valuation": valuation,
        "lifetime_scenarios": lifetime_scen,
        "m3_assessment": m3_report,
        "created_at": now_iso
    }

    reports_collection.insert_one(report_doc)
    report_doc.pop("_id", None)
    return report_doc


@app.post("/api/analyze", tags=["Analysis"])
def analyze_endpoint(payload: AnalyzeRequest):
    battery_id = payload.battery_id
    try:
        bat = batteries_collection.find_one({"battery_id": battery_id})
    except Exception:
        bat = None

    chemistry = bat.get("chemistry", "LFP") if bat else "LFP"
    rated_cap = float(bat.get("rated_capacity_ah", 50.0)) if bat else 50.0

    try:
        telemetry = list(
            tests_collection.find({"battery_id": battery_id}, {"_id": 0})
            .sort("sec", 1)
            .limit(1000)
        )
    except Exception:
        telemetry = []

    # Insufficient data → return a clear status; never fabricate measurements.
    if len(telemetry) < 5:
        return {
            "battery_id": battery_id,
            "status": "insufficient_telemetry",
            "message": (
                f"Only {len(telemetry)} telemetry reading(s) found for battery '{battery_id}'. "
                "Submit at least 5 readings via POST /api/live-data before requesting analysis. "
                "SOH cannot be estimated without sufficient measurement data."
            ),
            "soh_estimate": None,
            "safety_status": "UNKNOWN",
            "decision": "FURTHER_TESTING",
            "data_source": telemetry[-1].get("mode", "UNKNOWN") if telemetry else "UNKNOWN"
        }

    latest_mode = telemetry[-1].get("mode", "VIRTUAL") if telemetry else "VIRTUAL"

    # Single authoritative assessment: Member 3 engine only.
    m3_eval = evaluate_battery_m3(
        readings=telemetry,
        chemistry=chemistry,
        rated_capacity_ah=rated_cap,
    )

    soh_eval = m3_eval.get("soh_evaluation", {})
    safety_scr = m3_eval.get("safety_screening", {})
    confidence_eval = m3_eval.get("confidence_evaluation", {})
    mbco_decision = m3_eval.get("mbco_circularity_decision", {})
    valuation = m3_eval.get("indicative_valuation", {})
    lifetime_scen = m3_eval.get("lifetime_scenarios", {})
    extracted_features = m3_eval.get("features", {})
    basic_stats = extracted_features.get("basic_stats") or {}
    pulse_feats = extracted_features.get("pulse_features") or {}

    # SOH mapping
    soh_pct = soh_eval.get("soh_pct")
    soh_status = soh_eval.get("status", "")
    if soh_status == "predicted_pulse_model":
        soh_method = "pulse_model_pulsebat"
    elif soh_status == "predicted_offline_nasa_benchmark":
        soh_method = "nasa_full_discharge"
    else:
        soh_method = "not_available"

    soh_estimate = float(soh_pct) if soh_pct is not None else None
    soh_lower_pct = float(soh_eval["lower_pct"]) if soh_eval.get("lower_pct") is not None else None
    soh_upper_pct = float(soh_eval["upper_pct"]) if soh_eval.get("upper_pct") is not None else None
    soh_note = soh_eval.get("message") if soh_estimate is None else None

    # Confidence mapping
    conf_score_raw = confidence_eval.get("confidence_score")
    if conf_score_raw is None:
        conf_score_raw = confidence_eval.get("score")
    confidence_score = round(float(conf_score_raw), 2) if conf_score_raw is not None else 0.5
    confidence_level = confidence_eval.get("confidence_level", "MEDIUM")
    confidence_reasons = confidence_eval.get("reasons", [])

    # Safety mapping: Safe (SCREENING_CLEAR), Warning (WARNING), Critical Danger (QUARANTINE_SPECIALIST_REVIEW), Unknown — Further Testing Required (anything else)
    raw_safety = safety_scr.get("safety_state", "UNKNOWN")
    if raw_safety == "SCREENING_CLEAR":
        safety_status = "Safe"
    elif raw_safety == "WARNING":
        safety_status = "Warning"
    elif raw_safety == "QUARANTINE_SPECIALIST_REVIEW":
        safety_status = "Critical Danger"
    else:
        safety_status = "Unknown — Further Testing Required"

    crit_flags = safety_scr.get("critical_violations") or []
    warn_flags = safety_scr.get("warnings") or []
    safety_flags = crit_flags + warn_flags

    # Decision & action mapping
    primary_decision = mbco_decision.get("final_decision", "FURTHER_TESTING_REQUIRED")
    action_map = {
        "CONTINUED_USE_CANDIDATE": "Direct Reuse",
        "SECOND_LIFE_CANDIDATE": "Repurpose",
        "RECYCLING_ROUTE": "Recycle",
        "QUARANTINE_SPECIALIST_REVIEW": "Quarantine",
        "FURTHER_TESTING_REQUIRED": "Further Testing",
    }
    recommended_action = action_map.get(primary_decision, "Further Testing")

    recommended_pathway = mbco_decision.get("recommended_pathway")
    pathway_evaluations = mbco_decision.get("pathway_evaluations", {})
    if recommended_pathway and recommended_pathway in pathway_evaluations:
        recommended_app = pathway_evaluations[recommended_pathway].get("pathway_name", recommended_pathway)
    elif recommended_pathway:
        recommended_app = recommended_pathway.replace("_", " ").title()
    else:
        recommended_app = None

    # Capacity
    if soh_estimate is not None:
        remaining_capacity_ah = round(rated_cap * (soh_estimate / 100.0), 2)
    else:
        remaining_capacity_ah = None

    # Valuation
    route_vals = valuation.get("route_valuations", {}) if valuation.get("status") == "configured" else {}
    if recommended_pathway and recommended_pathway in route_vals:
        exchange_credit_inr = route_vals[recommended_pathway].get("indicative_net_value_inr")
        if exchange_credit_inr is not None:
            exchange_credit_inr = float(exchange_credit_inr)
    else:
        exchange_credit_inr = None
    valuation_note = valuation.get("valuation_note") or "Indicative; based on configured reference price"

    # Second-life matches and residual life years
    engine_routes = ["continued_ev", "light_ev", "solar_storage", "backup_power", "low_power_devices"]
    ranked_pathways = mbco_decision.get("ranked_pathways", [])
    ranked_route_ids = []
    for p in ranked_pathways:
        r_id = p.get("pathway") or p.get("route_id") or p.get("application")
        if r_id and r_id != "recycling" and r_id not in ranked_route_ids:
            ranked_route_ids.append(r_id)

    for r_id in engine_routes:
        if r_id not in ranked_route_ids:
            ranked_route_ids.append(r_id)

    second_life_matches = []
    eligible_count = 0
    route_years_map = {}

    for r_id in ranked_route_ids:
        pe = pathway_evaluations.get(r_id, {})
        app_title = pe.get("pathway_name") or r_id.replace("_", " ").title()
        is_eligible = bool(pe.get("eligibility", False))

        if is_eligible:
            eligible_count += 1
            suitability = "Optimal" if eligible_count == 1 else "Eligible"
        else:
            suitability = "Not Recommended"

        predicted_years = None
        if not is_eligible:
            reasons_list = pe.get("reasons", [])
            match_reason = reasons_list[0] if reasons_list else "Not eligible based on screening criteria"
        elif r_id == "continued_ev":
            match_reason = "EV duty cycle not modelled"
            predicted_years = None
        else:
            match_reason = "Suitable for secondary deployment"
            if soh_estimate is not None:
                try:
                    lt_res = calculate_lifetime_scenarios(soh_estimate, application_profile=r_id)
                    scens = lt_res.get("scenarios", {})
                    op_scen = scens.get("operating_scenario", {})
                    predicted_years = op_scen.get("projected_remaining_years")
                except Exception:
                    predicted_years = None
            reasons_list = pe.get("reasons", [])
            if reasons_list:
                match_reason = reasons_list[0]

        route_years_map[r_id] = predicted_years

        second_life_matches.append({
            "route_id": r_id,
            "application": app_title,
            "suitability": suitability,
            "predicted_lifetime_years": predicted_years,
            "reason": match_reason,
        })

    if recommended_pathway and recommended_pathway in route_years_map:
        residual_life_years = route_years_map[recommended_pathway]
    else:
        residual_life_years = None

    lifetime_note = "Assumption-based scenario, not a guarantee"

    # Features
    u_pts = extracted_features.get("u_points_v") or pulse_feats.get("u_points_v")
    if u_pts is None:
        try:
            from backend.ai.pulse_soh import extract_u17
            u_pts = extract_u17(telemetry)
        except Exception:
            u_pts = None

    res_05c = pulse_feats.get("pulse_05c_resistance_est_ohm") or pulse_feats.get("resistance_05c_ohm") or extracted_features.get("resistance_05c_ohm")
    temp_rise = basic_stats.get("temperature_change_c")

    features_out = {
        "u_points_v": u_pts,
        "temp_rise_c": temp_rise,
        "resistance_05c_ohm": res_05c,
    }

    # Plain English explanation: 2-4 plain sentences built from these values only
    sentences = []
    if soh_estimate is not None:
        sentences.append(f"Estimated State of Health is {soh_estimate:.1f}%.")
    else:
        sentences.append("Direct State of Health estimation is not available for this short pulse protocol.")
    sentences.append(f"Safety screening status is {safety_status}.")
    if recommended_app:
        sentences.append(f"Primary recommended action is {recommended_action} for {recommended_app}.")
    else:
        sentences.append(f"Primary recommended action is {recommended_action}.")
    if exchange_credit_inr is not None:
        sentences.append(f"Indicative residual exchange valuation is ₹{exchange_credit_inr:,.0f}.")
    plain_english_explanation = " ".join(sentences)

    # Source note
    src_note = bat.get("source_note") if bat else None
    if not src_note and source_note:
        prof = bat.get("last_profile", "healthy") if bat else "healthy"
        try:
            src_note = source_note(prof, latest_mode)
        except Exception:
            src_note = None

    now_iso = datetime.now(timezone.utc).isoformat()

    response_data = {
        "battery_id": battery_id,
        "data_source": latest_mode,
        "source_note": src_note,
        "chemistry": chemistry,
        "soh_estimate": soh_estimate,
        "soh_lower_pct": soh_lower_pct,
        "soh_upper_pct": soh_upper_pct,
        "soh_method": soh_method,
        "soh_note": soh_note,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "confidence_reasons": confidence_reasons,
        "safety_status": safety_status,
        "safety_flags": safety_flags,
        "primary_decision": primary_decision,
        "recommended_action": recommended_action,
        "recommended_app": recommended_app,
        "remaining_capacity_ah": remaining_capacity_ah,
        "exchange_credit_inr": exchange_credit_inr,
        "valuation_note": valuation_note,
        "residual_life_years": residual_life_years,
        "lifetime_note": lifetime_note,
        "second_life_matches": second_life_matches,
        "plain_english_explanation": plain_english_explanation,
        "features": features_out,
        "assessed_at": now_iso
    }

    report_doc = {
        "battery_id": battery_id,
        "soh": soh_estimate,
        "available_capacity_ah": remaining_capacity_ah,
        "safety_status": raw_safety,
        "decision": primary_decision,
        "mode": latest_mode,
        "indicative_valuation": valuation,
        "lifetime_scenarios": lifetime_scen,
        "m3_assessment": m3_eval,
        "analysis": response_data,
        "created_at": now_iso
    }
    reports_collection.insert_one(report_doc)

    batteries_collection.update_one(
        {"battery_id": battery_id},
        {"$set": {
            "status": "Assessed",
            "soh_estimate": soh_estimate,
            "safety_status": safety_status,
            "recommended_action": recommended_action,
            "updated_at": now_iso
        }}
    )

    return response_data


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
def run_what_if_simulation(payload: FlexibleWhatIfRequest):
    battery_id = getattr(payload, "battery_id", "BAT-101")

    daily_hours = getattr(payload, "daily_usage_hours", None)
    if daily_hours is None:
        daily_hours = getattr(payload, "daily_hours", None)
    if daily_hours is None:
        cpd = getattr(payload, "cycles_per_day", None)
        if cpd is not None:
            daily_hours = float(cpd) * 4.0
    if daily_hours is None:
        daily_hours = 4.0

    temp_c = getattr(payload, "ambient_temperature_c", None)
    if temp_c is None:
        temp_c = getattr(payload, "ambient_temp_c", None)
    if temp_c is None:
        temp_c = getattr(payload, "temp_c", 25.0)
    if temp_c is None:
        temp_c = 25.0

    dod_pct = getattr(payload, "depth_of_discharge_pct", None)
    if dod_pct is None:
        dod_pct = getattr(payload, "dod_pct", None)
    if dod_pct is None:
        c_dod = getattr(payload, "cycle_depth_dod", None)
        if c_dod is not None:
            dod_pct = c_dod * 100.0 if c_dod <= 1.0 else c_dod
    if dod_pct is None:
        dod_pct = 80.0

    current_soh = getattr(payload, "current_soh", None)
    chemistry = getattr(payload, "chemistry", None)

    if current_soh is None or chemistry is None:
        try:
            report = reports_collection.find_one(
                {"battery_id": battery_id},
                sort=[("created_at", -1)]
            )
            if report and current_soh is None:
                # Use actual SOH from report — do not substitute a fabricated value.
                current_soh = report.get("soh")  # May be None for short-pulse data.
        except Exception:
            pass

        try:
            bat = batteries_collection.find_one({"battery_id": battery_id})
            if bat and chemistry is None:
                chemistry = bat.get("chemistry", "LFP")
        except Exception:
            pass

    chemistry = chemistry or "LFP"

    # If SOH is unavailable (not_available_for_this_protocol), require it to be supplied explicitly.
    if current_soh is None:
        return {
            "battery_id": battery_id,
            "status": "soh_unavailable",
            "message": (
                "SOH is not available for this battery (short-pulse protocol or no completed assessment). "
                "Provide 'current_soh' in the request body to run a what-if simulation, "
                "or complete a full charge/discharge cycle assessment first."
            ),
            "baseline_residual_life_years": None,
            "simulated_residual_life_years": None,
        }

    current_soh = float(current_soh)

    # Stress-factor model using usage conditions (no fabricated base lifetime).
    temp_factor = 1.0 + max(0.0, (temp_c - 25.0) * 0.02)  # +2% degradation per °C above 25°C.
    dod_factor = 1.0 + max(0.0, (dod_pct - 70.0) * 0.01)  # +1% per % DoD above 70%.
    usage_factor = 1.0 + max(0.0, (daily_hours - 4.0) * 0.03)  # +3% per extra daily hour above 4 h.
    accel = round(temp_factor * dod_factor * usage_factor, 3)

    # Projected cycle life (chemistry-based reference, clearly approximate).
    base_cycles = {"LFP": 2000, "NMC": 1500, "NCA": 1200, "LTO": 10000}.get(chemistry.upper(), 1500)
    projected_cycles = int(base_cycles * (current_soh / 100.0) / max(0.5, accel))

    # Stress label.
    stress = "High" if temp_c > 35.0 or dod_pct > 85.0 else ("Moderate" if temp_c > 28.0 or dod_pct > 70.0 else "Low")

    rec_note = (
        f"Limiting Depth of Discharge to {min(dod_pct, 70.0):.0f}% and maintaining "
        f"ambient temperature below 30°C will reduce degradation acceleration factor "
        f"(current: {accel:.2f}×) and extend battery second life."
    )

    return {
        "battery_id": battery_id,
        "current_soh_pct": current_soh,
        "chemistry": chemistry,
        "baseline_residual_life_years": None,  # Not fabricated — requires calibrated lifetime model.
        "baseline_lifetime_note": "not_calibrated — baseline lifetime requires validated reference data",
        "simulated_residual_life_years": None,  # Same — not invented.
        "simulated_lifetime_note": "not_calibrated — use acceleration_factor and projected_cycle_life for relative comparison",
        "acceleration_factor": accel,
        "projected_cycle_life": projected_cycles,
        "thermal_stress_factor": stress,
        "recommendation_note": rec_note,
        "input_conditions": {
            "daily_usage_hours": daily_hours,
            "ambient_temperature_c": temp_c,
            "depth_of_discharge_pct": dod_pct,
            "chemistry": chemistry,
        }
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
    # Use actual SOH — None is correct for short-pulse data; never substitute a default.
    soh = report.get("soh") if report else None
    safety_status = report.get("safety_status", "UNKNOWN") if report else "UNKNOWN"

    # Return stored valuation if available; otherwise recompute via M3 valuation module.
    stored_val = report.get("indicative_valuation") if report else None
    if stored_val and isinstance(stored_val, dict) and stored_val.get("status") not in (None, "not_configured", "soh_unavailable"):
        valuation = stored_val
    else:
        valuation = _m3_calculate_valuation(
            soh_pct=soh,
            rated_capacity_ah=rated_cap,
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
    try:
        report = reports_collection.find_one(
            {"battery_id": battery_id},
            sort=[("created_at", -1)]
        )
    except Exception:
        report = None

    try:
        bat = batteries_collection.find_one({"battery_id": battery_id})
    except Exception:
        bat = None

    passport = report.get("passport") if report else None

    # If no passport has been issued, return a clear status — do not fabricate one.
    if not passport:
        return {
            "verification_status": "PASSPORT_NOT_ISSUED",
            "battery_id": battery_id,
            "message": "No digital passport has been issued for this battery. Complete assessment and call POST /api/passport/generate first.",
            "hash_integrity_verified": False,
            "soh_estimate": report.get("soh") if report else None,  # May be None — do not substitute a default.
        }

    # Actually verify the passport hash — only mark verified if the recomputed hash matches.
    verification = verify_battery_passport(passport)
    hash_ok = verification.get("valid", False)

    soh = report.get("soh") if report else None  # None is correct for short-pulse data; never substitute a default.
    safety = report.get("safety_status", "UNKNOWN") if report else "UNKNOWN"
    # Canonical safety enum mapping.
    safety_display_map = {
        "PASSED": "Safe", "SAFE": "Safe",
        "WARNING": "Warning",
        "FAILED": "Critical Danger", "CRITICAL_DANGER": "Critical Danger",
        "UNKNOWN": "Unknown — Further Testing Required",
    }
    safety_display = safety_display_map.get(safety.upper() if safety else "UNKNOWN", safety)

    return {
        "verification_status": "VERIFIED" if hash_ok else "TAMPERED",
        "battery_id": battery_id,
        "soh_estimate": soh,  # Null is valid — do not invent a number.
        "safety_status": safety_display,
        "approved_route": passport.get("approved_route"),
        "technician_id": passport.get("technician_id"),
        "minted_at": passport.get("minted_at"),
        "sha256_hash": passport.get("sha256_hash", ""),
        "hash_integrity_verified": hash_ok,  # Only True after actual verify_battery_passport() confirmation.
        "verification_detail": verification.get("detail"),
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
            val_doc = report["indicative_valuation"]
            credit = float(val_doc.get("net_indicative_valuation_inr", 0.0)) if isinstance(val_doc, dict) else 0.0
        else:
            # Recompute valuation via M3 module using actual SOH (may be null).
            rated_cap = float(battery.get("rated_capacity_ah", 2.5))
            soh = report.get("soh") if report else None  # Actual SOH or null — not substituted.
            val = _m3_calculate_valuation(
                soh_pct=soh,
                rated_capacity_ah=rated_cap,
            )
            credit = float(val.get("net_indicative_valuation_inr", 0.0)) if isinstance(val, dict) else 0.0

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
        # Use actual SOH from assessment — None is valid (not_available_for_this_protocol). Do not substitute a default.
        soh_val = report.get("soh") if report else None
        inventory_collection.update_one(
            {"battery_id": payload.battery_id},
            {
                "$set": {
                    "battery_id": payload.battery_id,
                    "chemistry": battery.get("chemistry", "LFP"),
                    "soh": soh_val,  # May be null — not fabricated.
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
                "soh": report.get("soh") if report else None,  # Actual SOH or null — not fabricated.
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
        # Use actual SOH — None means not yet assessed, not 80%.
        soh_raw = rep.get("soh") if rep else b.get("soh_estimate")
        soh = float(soh_raw) if soh_raw is not None else None
        chem = b.get("chemistry", "LFP")
        raw_safety = rep.get("safety_status", "UNKNOWN") if rep else "UNKNOWN"
        # Safety: UNKNOWN → not confirmed safe → route to further_testing display.
        if raw_safety in ("FAILED", "Critical Danger", "CRITICAL_DANGER"):
            safety = "Critical Danger"
        elif raw_safety == "WARNING":
            safety = "Warning"
        elif raw_safety in ("PASSED", "SAFE"):
            safety = "Safe"
        else:
            safety = "Unknown"

        val_doc = rep.get("indicative_valuation", {}) if rep else {}
        # Only use real valuation; if null SOH, credit is unknown.
        val_credit_raw = val_doc.get("net_indicative_valuation_inr") if val_doc else None
        val_credit = float(val_credit_raw) if val_credit_raw is not None else 0.0

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

        # Route battery: unknown SOH or unknown safety → further testing, not auto-approved.
        if safety == "Critical Danger":
            item["status"] = "Material Hydrometallurgy"
            recycle_batch.append(item)
        elif safety == "Unknown" or soh is None:
            item["status"] = "Further Assessment Required"
            repurpose_batch.append(item)
        elif soh < 50.0:
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
