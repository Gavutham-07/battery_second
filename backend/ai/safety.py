"""REVOLT Member 3 — Safety Screening Module.

Module: backend/ai/safety.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Deterministic, configurable safety screening of battery telemetry and assessment data.
- Screen for voltage boundaries, thermal limits, thermal rise (dT/dt), abnormal sag, sensor faults.
- Evaluate critical conditions that mandate immediate quarantine and specialist review.
- Prevent silent fallback to NMC thresholds when chemistry is unknown.
- Clearly enforce research rules:
  1. Critical safety indicators override all SOH and economic recommendations.
  2. Screening pass is NEVER described as proof of battery safety.
  3. Clearly separate deterministic safety screening from anomaly detection.
- Return strictly JSON-serializable output.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from backend.ai.assessment import assess_telemetry, _to_python_type


class SafetyState(str, Enum):
    SCREENING_CLEAR = "SCREENING_CLEAR"
    WARNING = "WARNING"
    FURTHER_TESTING_REQUIRED = "FURTHER_TESTING_REQUIRED"
    QUARANTINE_SPECIALIST_REVIEW = "QUARANTINE_SPECIALIST_REVIEW"


# Configurable chemistry default thresholds
DEFAULT_CHEMISTRY_SAFETY_LIMITS: Dict[str, Dict[str, float]] = {
    "NMC": {
        "min_voltage_critical": 2.0,       # Severe under-voltage / copper dissolution risk
        "min_voltage_warning": 2.7,        # Over-discharge warning
        "max_voltage_warning": 4.25,       # Slight over-voltage
        "max_voltage_critical": 4.35,      # Severe overcharge / thermal runaway risk
        "min_temp_critical": -20.0,        # Severe freezing
        "min_temp_warning": 0.0,           # Sub-zero operation warning
        "max_temp_warning": 45.0,          # Elevated operating temperature
        "max_temp_critical": 55.0,         # Precursor to thermal escalation
        "max_voltage_drop_warning": 0.8,   # High internal resistance / abnormal sag
        "max_temp_rise_warning": 8.0,      # Significant temperature rise during test
        "max_temp_rate_warning": 0.5,      # °C/s temperature ramp rate
    },
    "LFP": {
        "min_voltage_critical": 1.8,
        "min_voltage_warning": 2.5,
        "max_voltage_warning": 3.65,
        "max_voltage_critical": 3.80,
        "min_temp_critical": -20.0,
        "min_temp_warning": 0.0,
        "max_temp_warning": 50.0,
        "max_temp_critical": 65.0,
        "max_voltage_drop_warning": 0.6,
        "max_temp_rise_warning": 10.0,
        "max_temp_rate_warning": 0.6,
    },
    "LCO": {
        "min_voltage_critical": 2.2,
        "min_voltage_warning": 2.8,
        "max_voltage_warning": 4.25,
        "max_voltage_critical": 4.35,
        "min_temp_critical": -20.0,
        "min_temp_warning": 0.0,
        "max_temp_warning": 45.0,
        "max_temp_critical": 55.0,
        "max_voltage_drop_warning": 0.8,
        "max_temp_rise_warning": 8.0,
        "max_temp_rate_warning": 0.5,
    },
}

SAFETY_DISCLAIMER = (
    "Deterministic screening verifies only observed telemetry limits during the test. "
    "A screening pass does NOT certify cell structural integrity, absence of internal dendrites, "
    "or absolute long-term chemical stability."
)


def screen_battery_safety(
    readings_or_assessment: Union[List[Dict[str, Any]], Dict[str, Any]],
    chemistry: str = "NMC",
    custom_thresholds: Optional[Dict[str, float]] = None,
    bms_warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Perform deterministic safety screening on battery readings or assessment result.

    Rules:
    - Critical safety indicators override all SOH and economic recommendations.
    - Unknown chemistry must NOT silently use NMC thresholds. Triggers QUARANTINE_SPECIALIST_REVIEW.
    - Deterministic screening is cleanly isolated from anomaly detection.
    """
    chem_key = str(chemistry).strip().upper() if chemistry else "UNKNOWN"
    critical_violations: List[str] = []
    warnings: List[str] = []

    # 1. Chemistry verification
    applied_thresholds: Dict[str, float] = {}
    if custom_thresholds:
        applied_thresholds = dict(custom_thresholds)
    elif chem_key in DEFAULT_CHEMISTRY_SAFETY_LIMITS:
        applied_thresholds = dict(DEFAULT_CHEMISTRY_SAFETY_LIMITS[chem_key])
    else:
        # Unknown chemistry rule: must NOT silently use NMC-specific thresholds!
        critical_violations.append(
            f"Unknown or unsupported battery chemistry '{chem_key}'. Safety limits cannot be verified. "
            "Universal thresholds do not exist. Specialist review required."
        )

    # 2. Extract assessment data
    if isinstance(readings_or_assessment, dict) and "data_quality" in readings_or_assessment:
        assessment = readings_or_assessment
    else:
        assessment = assess_telemetry(readings_or_assessment, chemistry=chem_key)

    quality = assessment.get("data_quality", {})
    stats = assessment.get("extracted_features", {}).get("basic_stats")
    q_status = quality.get("status", "UNKNOWN")

    # 3. Check data completeness and sensor faults
    if q_status == "EMPTY":
        return _to_python_type({
            "safety_state": SafetyState.FURTHER_TESTING_REQUIRED.value,
            "is_safe_for_second_life": False,
            "critical_violations": [],
            "warnings": ["Telemetry data is empty. Safety cannot be evaluated."],
            "applied_thresholds": applied_thresholds,
            "chemistry": chem_key,
            "disclaimer": SAFETY_DISCLAIMER,
        })

    if q_status == "INVALID":
        critical_violations.append(
            "Sensor telemetry failed validation: sensor readings contain non-physical values, "
            "reverse polarity, or severe corrupted signals."
        )

    # 4. BMS Warnings screening
    if bms_warnings:
        for bw in bms_warnings:
            bw_upper = str(bw).upper()
            if any(term in bw_upper for term in ("CRITICAL", "SHORT", "VENT", "RUNAWAY", "OVERTEMP_LOCKOUT", "FIRE")):
                critical_violations.append(f"Critical BMS alarm reported: {bw}")
            else:
                warnings.append(f"BMS advisory warning: {bw}")

    # 5. Deterministic limits check (if thresholds available and stats exist)
    if stats and applied_thresholds:
        v_min = stats.get("voltage_min")
        v_max = stats.get("voltage_max")
        t_max = stats.get("temperature_max")
        t_min = stats.get("temperature_min")
        t_change = stats.get("temperature_change_c", 0.0)
        dur = stats.get("duration_s", 1.0)

        # Critical Under-Voltage Check
        min_v_crit = applied_thresholds.get("min_voltage_critical")
        if min_v_crit is not None and v_min is not None and v_min < min_v_crit:
            critical_violations.append(
                f"Severe under-voltage detected: min observed voltage {v_min:.3f} V is below critical limit {min_v_crit:.3f} V (copper dissolution risk)."
            )

        # Critical Over-Voltage Check
        max_v_crit = applied_thresholds.get("max_voltage_critical")
        if max_v_crit is not None and v_max is not None and v_max > max_v_crit:
            critical_violations.append(
                f"Severe over-voltage detected: max observed voltage {v_max:.3f} V exceeds critical limit {max_v_crit:.3f} V (overcharge / thermal hazard)."
            )

        # Critical Over-Temperature Check
        max_t_crit = applied_thresholds.get("max_temp_critical")
        if max_t_crit is not None and t_max is not None and t_max >= max_t_crit:
            critical_violations.append(
                f"Critical high temperature detected: max temperature {t_max:.1f} °C reaches or exceeds critical limit {max_t_crit:.1f} °C."
            )

        # Critical Sub-Zero Check
        min_t_crit = applied_thresholds.get("min_temp_critical")
        if min_t_crit is not None and t_min is not None and t_min <= min_t_crit:
            critical_violations.append(
                f"Critical sub-zero temperature detected: min temperature {t_min:.1f} °C is below critical limit {min_t_crit:.1f} °C."
            )

        # Warning Under-Voltage Check
        min_v_warn = applied_thresholds.get("min_voltage_warning")
        if min_v_warn is not None and v_min is not None and v_min < min_v_warn:
            if not any("under-voltage" in cv.lower() for cv in critical_violations):
                warnings.append(
                    f"Low voltage warning: min voltage {v_min:.3f} V is below standard operating cutoff {min_v_warn:.3f} V."
                )

        # Warning Over-Voltage Check
        max_v_warn = applied_thresholds.get("max_voltage_warning")
        if max_v_warn is not None and v_max is not None and v_max > max_v_warn:
            if not any("over-voltage" in cv.lower() for cv in critical_violations):
                warnings.append(
                    f"High voltage warning: max voltage {v_max:.3f} V is above nominal charge cutoff {max_v_warn:.3f} V."
                )

        # Warning Over-Temperature Check
        max_t_warn = applied_thresholds.get("max_temp_warning")
        if max_t_warn is not None and t_max is not None and t_max > max_t_warn:
            if not any("high temperature" in cv.lower() for cv in critical_violations):
                warnings.append(
                    f"Elevated temperature warning: max temperature {t_max:.1f} °C exceeds advisory threshold {max_t_warn:.1f} °C."
                )

        # Thermal rate check
        max_t_rise = applied_thresholds.get("max_temp_rise_warning")
        if max_t_rise is not None and abs(t_change) > max_t_rise:
            warnings.append(
                f"Abnormal temperature surge: temperature change of {t_change:.1f} °C observed during test."
            )

        if dur > 0:
            rate = abs(t_change) / dur
            max_rate = applied_thresholds.get("max_temp_rate_warning", 0.5)
            if rate > max_rate:
                warnings.append(
                    f"Rapid thermal escalation rate: {rate:.3f} °C/s exceeds threshold {max_rate:.3f} °C/s."
                )

    # 6. Data quality degradation warnings
    if q_status == "DEGRADED":
        warnings.append("Telemetry data quality is degraded (missing values or duplicate timestamps present).")

    # 7. Final State Arbitration
    if critical_violations:
        safety_state = SafetyState.QUARANTINE_SPECIALIST_REVIEW.value
        is_safe = False
    elif q_status in ("INVALID", "DEGRADED") and not stats:
        safety_state = SafetyState.FURTHER_TESTING_REQUIRED.value
        is_safe = False
    elif warnings:
        safety_state = SafetyState.WARNING.value
        is_safe = True  # Qualified safe under warning
    else:
        safety_state = SafetyState.SCREENING_CLEAR.value
        is_safe = True

    out = {
        "safety_state": safety_state,
        "is_safe_for_second_life": is_safe,
        "critical_violations": critical_violations,
        "warnings": warnings,
        "applied_thresholds": applied_thresholds,
        "chemistry": chem_key,
        "disclaimer": SAFETY_DISCLAIMER,
    }

    return _to_python_type(out)
