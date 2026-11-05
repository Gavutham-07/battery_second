"""REVOLT — Hackathon Demonstration Database Seeder.

Seeds realistic, verified demo scenarios into revolt_db:
1. BAT-101: Awaiting screening (ready for live 90s diagnostic test).
2. BAT-102: Assessed moderately aged NMC (Repurpose -> Solar Storage).
3. BAT-103: Approved LFP cell with minted SHA-256 Digital Battery Passport.
4. BAT-104: Thermally hazardous cell with strict Critical Danger lockout -> Recycle.
5. High-fidelity cell inventory ready for 4S balanced pack grouping.

Supports both live MongoDB instances and deterministic offline JSON caching.
"""

import os
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient

try:
    from backend.passport import generate_battery_passport, verify_battery_passport
except ImportError:
    try:
        from passport import generate_battery_passport, verify_battery_passport
    except ImportError:
        generate_battery_passport = None
        verify_battery_passport = None


def get_demo_dataset():
    """Generates the canonical demo dataset dictionary."""
    now_iso = datetime.now(timezone.utc).isoformat()

    batteries_docs = [
        {
            "battery_id": "BAT-101",
            "chemistry": "LFP",
            "rated_capacity_ah": 50.0,
            "voltage": 3.2,
            "manufacturer": "Tata AutoComp",
            "manufacture_date": "2021-04-12",
            "source_vehicle": "Tata Nexon EV Prime",
            "owner_name": "Aditya Sharma",
            "status": "Awaiting Screening",
            "soh_estimate": None,
            "safety_status": None,
            "recommended_action": None,
            "owner_preference": None,
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "battery_id": "BAT-102",
            "chemistry": "NMC",
            "rated_capacity_ah": 60.0,
            "voltage": 3.7,
            "manufacturer": "CATL",
            "manufacture_date": "2020-09-18",
            "source_vehicle": "MG ZS EV",
            "owner_name": "Priya Patel",
            "status": "Assessed",
            "soh_estimate": 76.5,
            "safety_status": "Safe",
            "recommended_action": "Repurpose",
            "owner_preference": "Sell / Exchange",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "battery_id": "BAT-103",
            "chemistry": "LFP",
            "rated_capacity_ah": 40.0,
            "voltage": 3.2,
            "manufacturer": "BYD FinDreams",
            "manufacture_date": "2022-01-15",
            "source_vehicle": "Mahindra XUV400",
            "owner_name": "Rohan Verma",
            "status": "Approved",
            "approved_route": "E-Rickshaw / Light EV",
            "soh_estimate": 89.4,
            "safety_status": "Safe",
            "recommended_action": "Direct Reuse",
            "owner_preference": "Reuse",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        {
            "battery_id": "BAT-104",
            "chemistry": "NMC",
            "rated_capacity_ah": 45.0,
            "voltage": 3.7,
            "manufacturer": "LG Energy Solution",
            "manufacture_date": "2019-11-03",
            "source_vehicle": "Hyundai Kona Electric",
            "owner_name": "Kavita Reddy",
            "status": "Assessed",
            "soh_estimate": 46.2,
            "safety_status": "Critical Danger",
            "recommended_action": "Recycle",
            "owner_preference": "Sell / Exchange",
            "created_at": now_iso,
            "updated_at": now_iso
        }
    ]

    # Construct canonical BAT-103 passport using the official passport module
    bat103_battery = {
        "battery_id": "BAT-103",
        "chemistry": "LFP",
        "rated_capacity_ah": 40.0,
        "manufacturer": "BYD FinDreams",
        "source_vehicle": "Mahindra XUV400",
    }
    bat103_rep_meta = {
        "battery_id": "BAT-103",
        "soh": 89.4,
        "available_capacity_ah": 35.76,
        "safety_status": "PASSED",
        "confidence": 97.0,
        "decision": "CONTINUE_EV",
        "mode": "VIRTUAL",
    }
    if generate_battery_passport is not None:
        bat103_passport = generate_battery_passport(bat103_battery, bat103_rep_meta)
        bat103_passport["passport_id"] = "PASSPORT-BAT-103-2026"
        bat103_passport["approved_route"] = "E-Rickshaw / Light EV"
        bat103_passport["technician_id"] = "TECH-BLR-02"
        bat103_passport["technician_notes"] = "Physical cell visual inspection cleared. Terminal busbars in factory condition."
        bat103_passport["minted_at"] = bat103_passport.get("issued_at", now_iso)
        bat103_passport["sha256_hash"] = bat103_passport.get("integrity_hash")
        bat103_passport["exchange_credit_inr"] = 32600.0
        bat103_passport["verification_url"] = "http://localhost:5173/verify/BAT-103"
        if verify_battery_passport is not None:
            verification_check = verify_battery_passport(bat103_passport)
            assert verification_check.get("valid") is True, f"Seeded passport integrity check failed: {verification_check}"
    else:
        bat103_passport = {
            "passport_id": "PASSPORT-BAT-103-2026",
            "battery_id": "BAT-103",
            "approved_route": "E-Rickshaw / Light EV",
            "technician_id": "TECH-BLR-02",
            "technician_notes": "Physical cell visual inspection cleared. Terminal busbars in factory condition.",
            "minted_at": now_iso,
            "integrity_hash": hashlib.sha256("BAT-103:TECH-BLR-02:E-Rickshaw / Light EV:2026".encode("utf-8")).hexdigest(),
            "sha256_hash": hashlib.sha256("BAT-103:TECH-BLR-02:E-Rickshaw / Light EV:2026".encode("utf-8")).hexdigest(),
            "exchange_credit_inr": 32600.0,
            "verification_url": "http://localhost:5173/verify/BAT-103"
        }

    reports_docs = [
        # BAT-102 Report: Repurpose
        {
            "battery_id": "BAT-102",
            "soh": 76.5,
            "available_capacity_ah": 45.9,
            "safety_status": "PASSED",
            "confidence": 93.0,
            "decision": "SECOND_LIFE_STORAGE",
            "mode": "VIRTUAL",
            "data_quality": "HIGH",
            "safety_flags": ["Moderate thermal rise (38.2°C) under high load"],
            "plain_english_explanation": "Cell retains 76.5% capacity with intact separator integrity. Ideal for stationary telecom and home solar storage.",
            "indicative_valuation": {
                "battery_id": "BAT-102",
                "chemistry": "NMC",
                "net_indicative_valuation_inr": 28400.0,
                "breakdown": {
                    "gross_capacity_credit_inr": 31200.0,
                    "safety_discount_inr": 0.0,
                    "confidence_discount_inr": 1800.0,
                    "processing_fee_inr": 1000.0
                }
            },
            "created_at": now_iso
        },
        # BAT-103 Report: Approved with SHA-256 Digital Passport
        {
            "battery_id": "BAT-103",
            "soh": 89.4,
            "available_capacity_ah": 35.76,
            "safety_status": "PASSED",
            "confidence": 97.0,
            "decision": "CONTINUE_EV",
            "mode": "VIRTUAL",
            "data_quality": "HIGH",
            "safety_flags": [],
            "plain_english_explanation": "Exceptional LFP health with tight voltage delta (<15mV). Premium candidate for light electric mobility repowering.",
            "indicative_valuation": {
                "battery_id": "BAT-103",
                "chemistry": "LFP",
                "net_indicative_valuation_inr": 32600.0,
                "breakdown": {
                    "gross_capacity_credit_inr": 34000.0,
                    "safety_discount_inr": 0.0,
                    "confidence_discount_inr": 400.0,
                    "processing_fee_inr": 1000.0
                }
            },
            "passport": bat103_passport,
            "created_at": now_iso
        },
        # BAT-104 Report: Critical Danger -> Recycle
        {
            "battery_id": "BAT-104",
            "soh": 46.2,
            "available_capacity_ah": 20.79,
            "safety_status": "FAILED",
            "confidence": 96.0,
            "decision": "RECYCLE",
            "mode": "VIRTUAL",
            "data_quality": "HIGH",
            "safety_flags": [
                "CRITICAL: Thermal Runaway Precursor (T_max = 58.4°C > 55.0°C cutoff)",
                "CRITICAL: Accelerated thermal ramp (dT/dt = 0.52°C/s >= 0.50°C/s)",
                "Severe capacity degradation below 50.0% threshold"
            ],
            "plain_english_explanation": "Severe thermal escalation detected during pulse excitation. Internal short circuit suspected. Cell is physically locked out from second-life reuse and slated for hydrometallurgical material recovery.",
            "indicative_valuation": {
                "battery_id": "BAT-104",
                "chemistry": "NMC",
                "net_indicative_valuation_inr": 4500.0,
                "breakdown": {
                    "gross_capacity_credit_inr": 4500.0,
                    "safety_discount_inr": 0.0,
                    "confidence_discount_inr": 0.0,
                    "processing_fee_inr": 0.0,
                    "scrap_floor_applied": True
                }
            },
            "created_at": now_iso
        }
    ]

    cell_inventory = [
        {"cell_id": "CELL-LFP-01", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.4, "internal_resistance_mohm": 12.1, "status": "Available"},
        {"cell_id": "CELL-LFP-02", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.9, "internal_resistance_mohm": 11.9, "status": "Available"},
        {"cell_id": "CELL-LFP-03", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 87.8, "internal_resistance_mohm": 12.4, "status": "Available"},
        {"cell_id": "CELL-LFP-04", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.2, "internal_resistance_mohm": 12.0, "status": "Available"},
        {"cell_id": "CELL-LFP-05", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 84.1, "internal_resistance_mohm": 13.8, "status": "Available"},
        {"cell_id": "CELL-LFP-06", "chemistry": "LFP", "capacity_ah": 3.2, "soh": 88.6, "internal_resistance_mohm": 12.2, "status": "Available"},
        {"cell_id": "CELL-NMC-01", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 91.2, "internal_resistance_mohm": 18.2, "status": "Available"},
        {"cell_id": "CELL-NMC-02", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 90.8, "internal_resistance_mohm": 18.5, "status": "Available"},
        {"cell_id": "CELL-NMC-03", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 91.5, "internal_resistance_mohm": 18.0, "status": "Available"},
        {"cell_id": "CELL-NMC-04", "chemistry": "NMC", "capacity_ah": 2.5, "soh": 78.4, "internal_resistance_mohm": 24.5, "status": "Available"},
        {"battery_id": "BAT-103", "chemistry": "LFP", "soh": 89.4, "status": "Available", "quantity": 1}
    ]

    txn_doc = {
        "transaction_id": "TXN-DEMO-BLR-103",
        "battery_id": "BAT-103",
        "technician_id": "TECH-BLR-02",
        "approved": True,
        "approved_route": "E-Rickshaw / Light EV",
        "notes": "Physical cell visual inspection cleared. Terminal busbars in factory condition.",
        "indicative_credit_inr": 32600.0,
        "signature_hash": hashlib.sha256("BAT-103:TECH-BLR-02:True".encode("utf-8")).hexdigest(),
        "timestamp": now_iso
    }

    return {
        "batteries": batteries_docs,
        "reports": reports_docs,
        "inventory": cell_inventory,
        "exchanges": [txn_doc]
    }


def save_offline_cache(dataset, output_file="data/seed_data.json"):
    """Saves the demo dataset as JSON for offline and mock usage."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"[CACHE] Demo fixtures saved to {output_file}")


def seed_database(mongo_uri="mongodb://localhost:27017", db_name="revolt_db", target_db=None, output_cache="data/seed_data.json", force_reseed=False):
    """Populates MongoDB and offline cache with demo datasets."""
    dataset = get_demo_dataset()
    save_offline_cache(dataset, output_cache)

    # If an explicit database handle is provided (e.g., mongomock during unit tests)
    if target_db is not None:
        demo_ids = [b["battery_id"] for b in dataset["batteries"]]
        if not force_reseed:
            existing_count = target_db["batteries"].count_documents({"battery_id": {"$in": demo_ids}})
            if existing_count == len(demo_ids):
                print(f"[MOCK] Demo records already present ({existing_count} items). Skipping re-seed.")
                return {"status": "SKIPPED_ALREADY_EXISTS", "mode": "MOCK_DB", "counts": {k: len(v) for k, v in dataset.items()}}

        target_db["batteries"].delete_many({"battery_id": {"$in": demo_ids}})
        target_db["reports"].delete_many({"battery_id": {"$in": demo_ids}})
        target_db["batteries"].insert_many(dataset["batteries"])
        target_db["reports"].insert_many(dataset["reports"])
        for item in dataset["inventory"]:
            query_key = {"cell_id": item["cell_id"]} if "cell_id" in item else {"battery_id": item["battery_id"]}
            target_db["inventory"].update_one(query_key, {"$set": item}, upsert=True)
        for item in dataset["exchanges"]:
            target_db["exchanges"].update_one({"transaction_id": item["transaction_id"]}, {"$set": item}, upsert=True)
        print("[MOCK] Injected seed dataset into provided target_db instance.")
        return {"status": "SUCCESS", "mode": "MOCK_DB", "counts": {k: len(v) for k, v in dataset.items()}}

    # Try connecting to live MongoDB
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        db = client[db_name]

        demo_ids = [b["battery_id"] for b in dataset["batteries"]]
        if not force_reseed:
            existing_count = db["batteries"].count_documents({"battery_id": {"$in": demo_ids}})
            if existing_count == len(demo_ids):
                print(f"[MONGODB] Demo records already present ({existing_count} items). Skipping destructive re-seed.")
                return {"status": "SKIPPED_ALREADY_EXISTS", "mode": "MONGODB", "counts": {k: len(v) for k, v in dataset.items()}}

        db["batteries"].delete_many({"battery_id": {"$in": demo_ids}})
        db["reports"].delete_many({"battery_id": {"$in": demo_ids}})
        db["tests"].delete_many({"battery_id": {"$in": demo_ids}})
        db["exchanges"].delete_many({"battery_id": {"$in": demo_ids}})
        db["inventory"].delete_many({"battery_id": {"$in": demo_ids}})

        db["batteries"].insert_many(dataset["batteries"])
        db["reports"].insert_many(dataset["reports"])

        for cell in dataset["inventory"]:
            query_key = {"cell_id": cell["cell_id"]} if "cell_id" in cell else {"battery_id": cell["battery_id"]}
            db["inventory"].update_one(query_key, {"$set": cell}, upsert=True)

        for txn in dataset["exchanges"]:
            db["exchanges"].update_one({"transaction_id": txn["transaction_id"]}, {"$set": txn}, upsert=True)

        print(f"[MONGODB] Successfully seeded {db_name} with demo datasets.")
        return {"status": "SUCCESS", "mode": "MONGODB", "counts": {k: len(v) for k, v in dataset.items()}}

    except Exception as e:
        print(f"[OFFLINE_FALLBACK] Live MongoDB unreachable ({e}). Offline cache is populated and operational.")
        return {"status": "SUCCESS", "mode": "OFFLINE_CACHE", "counts": {k: len(v) for k, v in dataset.items()}}


if __name__ == "__main__":
    force = "--force-reseed" in sys.argv or "-f" in sys.argv
    seed_database(force_reseed=force)
