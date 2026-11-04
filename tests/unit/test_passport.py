import pytest
import copy
from backend.passport import (
    generate_battery_passport,
    verify_battery_passport,
    compute_passport_hash,
)


@pytest.fixture
def sample_battery():
    return {
        "battery_id": "BAT-UNIT-PASS-01",
        "chemistry": "LFP",
        "rated_capacity_ah": 2.5,
        "manufacturer": "EVE Energy",
        "source_vehicle": "Ola S1 Pro"
    }


@pytest.fixture
def sample_report():
    return {
        "battery_id": "BAT-UNIT-PASS-01",
        "soh": 84.5,
        "available_capacity_ah": 2.11,
        "safety_status": "PASSED",
        "confidence": 92.0,
        "decision": "SECOND_LIFE_STORAGE",
        "mode": "LIVE"
    }


def test_generate_passport_deterministic_hash(sample_battery, sample_report):
    passport = generate_battery_passport(sample_battery, sample_report)
    assert passport["battery_id"] == "BAT-UNIT-PASS-01"
    assert passport["chemistry"] == "LFP"
    assert passport["assessment"]["soh"] == 84.5
    assert "integrity_hash" in passport
    assert len(passport["integrity_hash"]) == 64  # SHA-256 is 64 hex characters

    # Re-computing hash over same passport produces identical hash
    recomputed = compute_passport_hash(passport)
    assert recomputed == passport["integrity_hash"]

    # Verify function passes
    verif = verify_battery_passport(passport)
    assert verif["valid"] is True
    assert verif["matched"] is True
    assert verif["error"] is None


def test_passport_tamper_detection_soh(sample_battery, sample_report):
    passport = generate_battery_passport(sample_battery, sample_report)

    # Tamper with SOH (e.g. fraudulent increase from 84.5% to 95.0%)
    tampered = copy.deepcopy(passport)
    tampered["assessment"]["soh"] = 95.0

    verif = verify_battery_passport(tampered)
    assert verif["valid"] is False
    assert verif["matched"] is False
    assert verif["error"] is not None
    assert "Tamper detected" in verif["error"]


def test_passport_tamper_detection_safety_status(sample_battery, sample_report):
    # Create failing battery passport
    report_failed = copy.deepcopy(sample_report)
    report_failed["safety_status"] = "FAILED"
    report_failed["decision"] = "RECYCLE"

    passport = generate_battery_passport(sample_battery, report_failed)
    assert verify_battery_passport(passport)["valid"] is True

    # Tamper: flip safety from FAILED to PASSED
    tampered = copy.deepcopy(passport)
    tampered["assessment"]["safety_status"] = "PASSED"

    verif = verify_battery_passport(tampered)
    assert verif["valid"] is False
    assert verif["matched"] is False
    assert "Tamper detected" in verif["error"]


def test_passport_tamper_detection_battery_id(sample_battery, sample_report):
    passport = generate_battery_passport(sample_battery, sample_report)

    # Tamper: spoof battery_id
    tampered = copy.deepcopy(passport)
    tampered["battery_id"] = "BAT-SPOOFED-99"

    verif = verify_battery_passport(tampered)
    assert verif["valid"] is False
    assert verif["matched"] is False


def test_passport_tamper_detection_chemistry(sample_battery, sample_report):
    passport = generate_battery_passport(sample_battery, sample_report)

    # Tamper: change chemistry from LFP to NMC
    tampered = copy.deepcopy(passport)
    tampered["chemistry"] = "NMC"

    verif = verify_battery_passport(tampered)
    assert verif["valid"] is False
    assert verif["matched"] is False


def test_passport_missing_hash(sample_battery, sample_report):
    passport = generate_battery_passport(sample_battery, sample_report)
    tampered = copy.deepcopy(passport)
    del tampered["integrity_hash"]

    verif = verify_battery_passport(tampered)
    assert verif["valid"] is False
    assert "Missing 'integrity_hash'" in verif["error"]


def test_passport_qr_code_format(sample_battery, sample_report):
    passport = generate_battery_passport(sample_battery, sample_report)
    assert "qr_code" in passport
    assert passport["qr_code"].startswith("revolt://passport/BAT-UNIT-PASS-01?hash=")
    assert passport["integrity_hash"].startswith(passport["qr_code"].split("hash=")[1])

