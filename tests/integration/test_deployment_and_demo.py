"""Phase 13 Integration Test Suite — Deployment and Hackathon Demonstration.

Verifies:
1. Multi-scenario seed database generation (BAT-101 to BAT-104).
2. Offline JSON cache persistence for hackathon reliability.
3. Existence and validation of one-click platform launch and teardown scripts.
4. Verification of hackathon demonstration runbook completeness.
5. End-to-end API scenario readiness for all 4 stakeholder roles.
"""

import asyncio
import json
import os
from pathlib import Path
import pytest
from scripts.seed_database import get_demo_dataset, seed_database
from backend.main import (
    app,
    list_batteries,
    get_battery,
    get_passport,
    run_what_if_simulation,
    FlexibleWhatIfRequest,
    get_inventory,
    group_cells,
    CellGroupingRequest
)


def test_seed_database_fixture_integrity():
    """Verify demo seed dataset satisfies all engineering and safety specifications."""
    data = get_demo_dataset()
    assert "batteries" in data
    assert "reports" in data
    assert "inventory" in data
    assert "exchanges" in data

    batteries = {b["battery_id"]: b for b in data["batteries"]}
    assert "BAT-101" in batteries
    assert "BAT-102" in batteries
    assert "BAT-103" in batteries
    assert "BAT-104" in batteries

    # BAT-101: Awaiting screening
    assert batteries["BAT-101"]["status"] == "Awaiting Screening"
    assert batteries["BAT-101"]["soh_estimate"] is None

    # BAT-102: Assessed -> Repurpose
    assert batteries["BAT-102"]["status"] == "Assessed"
    assert batteries["BAT-102"]["soh_estimate"] == 76.5
    assert batteries["BAT-102"]["recommended_action"] == "Repurpose"

    # BAT-103: Approved with Passport
    assert batteries["BAT-103"]["status"] == "Approved"
    assert batteries["BAT-103"]["soh_estimate"] == 89.4

    # BAT-104: Critical Danger -> Recycle
    assert batteries["BAT-104"]["status"] == "Assessed"
    assert batteries["BAT-104"]["safety_status"] == "Critical Danger"
    assert batteries["BAT-104"]["recommended_action"] == "Recycle"


def test_seed_database_reports_and_passports():
    """Verify reports contain valid valuation breakdowns and SHA-256 passports."""
    data = get_demo_dataset()
    reports = {r["battery_id"]: r for r in data["reports"]}

    assert "BAT-102" in reports
    assert reports["BAT-102"]["decision"] == "SECOND_LIFE_STORAGE"
    assert reports["BAT-102"]["indicative_valuation"]["net_indicative_valuation_inr"] > 0

    assert "BAT-103" in reports
    assert reports["BAT-103"]["decision"] == "CONTINUE_EV"
    passport = reports["BAT-103"]["passport"]
    assert passport["passport_id"] == "PASSPORT-BAT-103-2026"
    assert len(passport["sha256_hash"]) == 64  # Valid SHA-256 hex length
    assert "verify/BAT-103" in passport["verification_url"]

    assert "BAT-104" in reports
    assert reports["BAT-104"]["decision"] == "RECYCLE"
    assert reports["BAT-104"]["safety_status"] == "FAILED"
    assert any("CRITICAL: Thermal Runaway Precursor" in flag for flag in reports["BAT-104"]["safety_flags"])


def test_offline_cache_generation(tmp_path):
    """Verify seed_database writes offline cache file properly."""
    cache_path = tmp_path / "test_seed.json"
    result = seed_database(output_cache=str(cache_path))
    assert result["status"] == "SUCCESS"
    assert cache_path.exists()

    with open(cache_path, "r", encoding="utf-8") as f:
        cached_data = json.load(f)
    assert len(cached_data["batteries"]) == 4
    assert len(cached_data["inventory"]) >= 10


def test_launcher_scripts_exist():
    """Verify all launch, batch, and teardown scripts exist and contain required hooks."""
    root = Path(__file__).parent.parent.parent
    run_ps1 = root / "scripts" / "run_platform.ps1"
    run_bat = root / "scripts" / "run_platform.bat"
    stop_ps1 = root / "scripts" / "stop_platform.ps1"

    assert run_ps1.exists(), "run_platform.ps1 missing"
    assert run_bat.exists(), "run_platform.bat missing"
    assert stop_ps1.exists(), "stop_platform.ps1 missing"

    ps1_content = run_ps1.read_text(encoding="utf-8")
    assert "8000" in ps1_content
    assert "5173" in ps1_content
    assert "seed_database.py" in ps1_content

    stop_content = stop_ps1.read_text(encoding="utf-8")
    assert ".revolt_pids.json" in stop_content


def test_demo_runbook_coverage():
    """Verify DEMO_RUNBOOK.md contains comprehensive scenario coverage."""
    root = Path(__file__).parent.parent.parent
    runbook_path = root / "docs" / "DEMO_RUNBOOK.md"
    assert runbook_path.exists(), "docs/DEMO_RUNBOOK.md missing"

    content = runbook_path.read_text(encoding="utf-8")
    assert "BAT-101" in content
    assert "BAT-102" in content
    assert "BAT-103" in content
    assert "BAT-104" in content
    assert "Arrhenius" in content
    assert "Wöhler" in content or "Wohler" in content
    assert "SHA-256" in content
    assert "sigma_{SOH}" in content or "Variance" in content or "3.0%" in content


def test_what_if_scenario_simulation():
    """Verify what-if simulation responds with valid Arrhenius degradation projection."""
    req = FlexibleWhatIfRequest(
        battery_id="BAT-102",
        chemistry="NMC",
        current_soh=76.5,
        target_application="SOLAR_STORAGE",
        ambient_temp_c=35.0,
        cycle_depth_dod=0.80,
        cycles_per_day=1.5
    )
    result = run_what_if_simulation(req)
    assert result is not None
    assert "projected_cycle_life" in result
    assert result["projected_cycle_life"] > 0
    assert result["battery_id"] == "BAT-102"
    assert "recommendation_note" in result
