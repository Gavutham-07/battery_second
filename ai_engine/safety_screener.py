from typing import Dict, Any, Tuple, List


def screen_battery_safety(
    features: Dict[str, Any],
    chemistry: str = "LFP"
) -> Tuple[str, List[str]]:
    """
    Evaluates physical measurements against chemistry-specific safety envelopes.
    Returns (safety_status, anomaly_flags).
    safety_status is one of: PASSED, WARNING, FAILED, UNKNOWN.
    """
    flags = []

    # 1. Check data sufficiency
    if not features or features.get("sample_count", 0) < 3 or features.get("v_min") is None:
        return "UNKNOWN", ["INSUFFICIENT_TELEMETRY"]

    t_max = features.get("t_max", 25.0)
    t_rate_max = features.get("t_rate_max", 0.0)
    v_max = features.get("v_max", 3.3)
    v_min = features.get("v_min", 3.2)
    ir = features.get("estimated_ir_ohm", 0.040)
    chem = (chemistry or "LFP").upper()

    # 2. Critical Thermal Violations (FAILED)
    if t_max > 55.0:
        flags.append("CRITICAL_OVER_TEMPERATURE")
    if t_rate_max >= 0.5:
        flags.append("THERMAL_RUNAWAY_RATE_ALERT")

    # 3. Critical Voltage Violations (FAILED)
    if chem == "LFP":
        if v_max > 3.80:
            flags.append("CRITICAL_OVER_VOLTAGE_LFP")
        if v_min < 2.00:
            flags.append("CRITICAL_UNDER_VOLTAGE_LFP")
    else:  # NMC / NCA
        if v_max > 4.30:
            flags.append("CRITICAL_OVER_VOLTAGE_NMC")
        if v_min < 2.50:
            flags.append("CRITICAL_UNDER_VOLTAGE_NMC")

    # 4. Critical Impedance Violations (FAILED)
    if ir > 0.300:
        flags.append("SEVERE_IMPEDANCE_DEGRADATION")

    if flags:
        return "FAILED", flags

    # 5. Warning Level Thermal Anomalies (WARNING)
    if t_max > 45.0:
        flags.append("ELEVATED_TEMPERATURE_WARNING")
    if t_rate_max >= 0.2:
        flags.append("RAPID_TEMPERATURE_RISE_WARNING")

    # 6. Warning Level Voltage Imbalance / Range (WARNING)
    if chem == "LFP":
        if v_max > 3.70:
            flags.append("OVER_VOLTAGE_WARNING_LFP")
        if v_min < 2.20:
            flags.append("UNDER_VOLTAGE_WARNING_LFP")
    else:
        if v_max > 4.25:
            flags.append("OVER_VOLTAGE_WARNING_NMC")
        if v_min < 2.80:
            flags.append("UNDER_VOLTAGE_WARNING_NMC")

    # 7. Warning Level Internal Resistance (WARNING)
    if ir > 0.120:
        flags.append("HIGH_INTERNAL_RESISTANCE_WARNING")

    if flags:
        return "WARNING", flags

    return "PASSED", ["NOMINAL_OPERATING_ENVELOPE"]

