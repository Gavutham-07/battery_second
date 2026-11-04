"""REVOLT Member 3 — Scenario-Based Lifetime Engine.

Module: backend/ai/lifetime.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Calculate conditional lifetime scenarios across circularity operational regimes.
- Provide estimates only when supported by defensible reference model calibration.
- Return 'not_calibrated' if reference cycle life data is unavailable.
- Explicitly display all operating assumptions and stress acceleration factors.
- Strictly never guarantee remaining years or cycle life.
- Ensure strictly JSON-serializable output.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.ai.assessment import _to_python_type

LIFETIME_DISCLAIMER = (
    "Scenario-based projections are conditional mathematical estimates based on specified reference inputs. "
    "They do NOT constitute a performance warranty, operational guarantee, or insurance against degradation."
)

DEFAULT_APPLICATION_PROFILES: Dict[str, Dict[str, Any]] = {
    "solar_storage": {
        "name": "Stationary Solar PV Storage",
        "typical_daily_cycles": 1.0,
        "default_dod_pct": 80.0,
        "retirement_soh_pct": 70.0,
        "daily_operating_hours": 8.0,
    },
    "backup_power": {
        "name": "Standby Backup Power / UPS",
        "typical_daily_cycles": 0.15,
        "default_dod_pct": 50.0,
        "retirement_soh_pct": 65.0,
        "daily_operating_hours": 24.0,
    },
    "light_ev": {
        "name": "Light EV / 2-Wheeler Duty",
        "typical_daily_cycles": 1.25,
        "default_dod_pct": 80.0,
        "retirement_soh_pct": 75.0,
        "daily_operating_hours": 4.0,
    },
    "low_power_devices": {
        "name": "Low-Power Auxiliary Systems",
        "typical_daily_cycles": 0.50,
        "default_dod_pct": 70.0,
        "retirement_soh_pct": 60.0,
        "daily_operating_hours": 6.0,
    },
}


def _load_lifetime_config() -> Optional[Dict[str, Any]]:
    """Attempt to load lifetime config from revolt_decision_engine_config.json."""
    current_file = Path(__file__).resolve()
    cfg_path = current_file.parent.parent / "models" / "research_artifacts" / "revolt_decision_engine_config.json"
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("lifetime_config")
        except Exception:
            return None
    return None


def calculate_lifetime_scenarios(
    soh_pct: Optional[float],
    daily_operating_hours: Optional[float] = None,
    operating_temperature_c: Optional[float] = None,
    depth_of_discharge_pct: Optional[float] = None,
    application_profile: str = "solar_storage",
    lifetime_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate scenario-based lifetime projections.

    If reference calibration data is unavailable, returns status: 'not_calibrated'.
    """
    # 1. Resolve configuration
    cfg = dict(lifetime_config) if lifetime_config else {}
    if not cfg:
        disk_cfg = _load_lifetime_config()
        if disk_cfg:
            cfg.update(disk_cfg)

    ref_cycle_life = cfg.get("reference_cycle_life")
    ref_dod = cfg.get("reference_dod_pct", 80.0) or 80.0
    ref_temp = cfg.get("reference_temperature_c", 25.0) or 25.0

    # Rule: Return not_calibrated if suitable reference data is unavailable
    if ref_cycle_life is None or ref_cycle_life <= 0:
        return _to_python_type({
            "status": "not_calibrated",
            "message": (
                "Cell degradation reference cycle life is not calibrated. "
                "Arbitrary degradation slopes are prohibited. "
                "Provide 'reference_cycle_life' in lifetime configuration to model conditional scenarios."
            ),
            "calibrated_scenarios": {},
            "disclaimer": LIFETIME_DISCLAIMER,
        })

    if soh_pct is None or math.isnan(soh_pct):
        return _to_python_type({
            "status": "soh_unavailable",
            "message": "Current SOH is unavailable. Lifetime scenario calculation requires a validated SOH baseline.",
            "calibrated_scenarios": {},
            "disclaimer": LIFETIME_DISCLAIMER,
        })

    # 2. Resolve application profile parameters
    app_key = str(application_profile).lower()
    profile = DEFAULT_APPLICATION_PROFILES.get(app_key, DEFAULT_APPLICATION_PROFILES["solar_storage"])

    dod = depth_of_discharge_pct if depth_of_discharge_pct is not None else profile["default_dod_pct"]
    temp = operating_temperature_c if operating_temperature_c is not None else ref_temp
    hours = daily_operating_hours if daily_operating_hours is not None else profile["daily_operating_hours"]
    retire_soh = profile["retirement_soh_pct"]
    daily_cycles = profile["typical_daily_cycles"]

    # 3. Physics-informed stress acceleration modeling
    # Thermal acceleration: Arrhenius rule of thumb (~doubling degradation per 10°C rise)
    temp_delta = temp - ref_temp
    thermal_stress_factor = round(2.0 ** (temp_delta / 10.0), 3)

    # DOD stress factor: Power law relationship (~(DOD / ref_DOD)^1.5)
    dod_ratio = max(0.1, dod / ref_dod)
    dod_stress_factor = round(dod_ratio ** 1.5, 3)

    combined_acceleration = max(0.2, thermal_stress_factor * dod_stress_factor)

    # Remaining SOH headroom to retirement
    soh_headroom = max(0.0, soh_pct - retire_soh)
    nominal_total_headroom = max(1.0, 100.0 - retire_soh)
    fraction_remaining = soh_headroom / nominal_total_headroom

    # Projected remaining cycles under scenario
    effective_cycle_budget = ref_cycle_life * fraction_remaining
    projected_cycles = int(max(0, effective_cycle_budget / combined_acceleration))

    # Projected days and years
    if daily_cycles > 0:
        projected_days = int(projected_cycles / daily_cycles)
        projected_years = round(projected_days / 365.25, 2)
    else:
        projected_days = 0
        projected_years = 0.0

    scenarios = {
        "nominal_case": {
            "description": f"Standard {profile['name']} under reference conditions ({ref_temp}°C, {ref_dod}% DOD)",
            "operating_temperature_c": ref_temp,
            "depth_of_discharge_pct": ref_dod,
            "projected_cycles": int(effective_cycle_budget),
            "projected_years": round((effective_cycle_budget / max(0.01, daily_cycles)) / 365.25, 2),
        },
        "operating_scenario": {
            "description": f"Specified scenario for {profile['name']}",
            "operating_temperature_c": round(float(temp), 1),
            "depth_of_discharge_pct": round(float(dod), 1),
            "daily_operating_hours": round(float(hours), 1),
            "daily_cycles_assumed": daily_cycles,
            "thermal_stress_factor": thermal_stress_factor,
            "dod_stress_factor": dod_stress_factor,
            "combined_acceleration_factor": round(combined_acceleration, 3),
            "projected_remaining_cycles": projected_cycles,
            "projected_remaining_days": projected_days,
            "projected_remaining_years": projected_years,
        },
    }

    return _to_python_type({
        "status": "calibrated",
        "current_soh_pct": round(float(soh_pct), 1),
        "application_profile": app_key,
        "retirement_threshold_soh_pct": retire_soh,
        "reference_baseline": {
            "reference_cycle_life": ref_cycle_life,
            "reference_dod_pct": ref_dod,
            "reference_temperature_c": ref_temp,
        },
        "scenarios": scenarios,
        "assumptions": [
            f"Retirement SOH threshold: {retire_soh}%",
            f"Application: {profile['name']} with {daily_cycles} cycles/day",
            f"Thermal stress model: Arrhenius doubling per 10°C delta from {ref_temp}°C",
            f"DOD stress model: Power law exponent 1.5 relative to {ref_dod}% DOD",
        ],
        "disclaimer": LIFETIME_DISCLAIMER,
    })
