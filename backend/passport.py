import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any


def serialize_canonical_passport(passport: Dict[str, Any]) -> str:
    """
    Serializes passport data into a canonical, sorted JSON string excluding integrity_hash,
    qr_code, and database internal fields (_id) to guarantee bit-for-bit reproducibility.
    """
    canonical_dict = {
        "battery_id": str(passport.get("battery_id", "")),
        "chemistry": str(passport.get("chemistry", "")),
        "rated_capacity_ah": float(passport.get("rated_capacity_ah", 0.0)),
        "manufacturer": passport.get("manufacturer"),
        "source_vehicle": passport.get("source_vehicle"),
        "assessment": {
            "soh": float(passport["assessment"]["soh"]) if passport.get("assessment", {}).get("soh") is not None else None,
            "available_capacity_ah": float(passport["assessment"]["available_capacity_ah"]) if passport.get("assessment", {}).get("available_capacity_ah") is not None else None,
            "safety_status": str(passport.get("assessment", {}).get("safety_status", "UNKNOWN")),
            "confidence": float(passport["assessment"]["confidence"]) if passport.get("assessment", {}).get("confidence") is not None else None,
            "decision": str(passport.get("assessment", {}).get("decision", "FURTHER_TESTING")),
            "mode": str(passport.get("assessment", {}).get("mode", "LIVE")),
        },
        "issued_at": str(passport.get("issued_at", ""))
    }
    return json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))


def compute_passport_hash(passport: Dict[str, Any]) -> str:
    """Computes SHA-256 checksum over the canonical JSON representation."""
    canonical_str = serialize_canonical_passport(passport)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def generate_battery_passport(battery: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assembles a verifiable Digital Battery Passport from battery identity and assessment report,
    calculates the cryptographic SHA-256 integrity hash, and generates a QR code reference string.
    """
    issued_at = datetime.now(timezone.utc).isoformat()
    passport: Dict[str, Any] = {
        "battery_id": battery["battery_id"],
        "chemistry": battery.get("chemistry", "LFP"),
        "rated_capacity_ah": float(battery.get("rated_capacity_ah", 2.5)),
        "manufacturer": battery.get("manufacturer"),
        "source_vehicle": battery.get("source_vehicle"),
        "assessment": {
            "soh": report.get("soh"),
            "available_capacity_ah": report.get("available_capacity_ah"),
            "safety_status": report.get("safety_status", "UNKNOWN"),
            "confidence": report.get("confidence"),
            "decision": report.get("decision", "FURTHER_TESTING"),
            "mode": report.get("mode", "LIVE"),
        },
        "issued_at": issued_at
    }

    integrity_hash = compute_passport_hash(passport)
    passport["integrity_hash"] = integrity_hash
    passport["sha256_hash"] = integrity_hash
    passport["qr_code"] = f"revolt://passport/{passport['battery_id']}?hash={integrity_hash[:16]}"
    return passport


def verify_battery_passport(passport_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies the integrity of a Digital Battery Passport payload by re-computing its SHA-256
    hash and checking against the claimed integrity_hash. Detects any field tampering.
    """
    if not isinstance(passport_data, dict):
        return {
            "valid": False,
            "battery_id": "UNKNOWN",
            "computed_hash": "",
            "matched": False,
            "error": "Passport payload must be a JSON object",
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    claimed_hash = passport_data.get("integrity_hash") or passport_data.get("sha256_hash")
    battery_id = passport_data.get("battery_id", "UNKNOWN")

    if not claimed_hash:
        return {
            "valid": False,
            "battery_id": battery_id,
            "computed_hash": "",
            "matched": False,
            "error": "Missing 'integrity_hash' or 'sha256_hash' in passport payload",
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    try:
        computed_hash = compute_passport_hash(passport_data)
    except Exception as exc:
        return {
            "valid": False,
            "battery_id": battery_id,
            "computed_hash": "",
            "matched": False,
            "error": f"Failed to compute canonical hash: {str(exc)}",
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    matched = (claimed_hash == computed_hash)
    return {
        "valid": matched,
        "battery_id": battery_id,
        "computed_hash": computed_hash,
        "matched": matched,
        "error": None if matched else "Tamper detected: Computed hash does not match claimed integrity_hash",
        "verified_at": datetime.now(timezone.utc).isoformat()
    }
