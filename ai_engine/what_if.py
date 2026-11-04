import math
from typing import Dict, Any


def simulate_what_if(
    battery_id: str,
    current_soh: float,
    daily_hours: float,
    temp_c: float,
    dod_pct: float,
    chemistry: str = "LFP"
) -> Dict[str, Any]:
    """
    Simulates conditional remaining useful life (RUL) under varying operating
    temperature, duty cycle (daily hours), and Depth-of-Discharge (DoD) workloads.
    """
    soh_val = current_soh if current_soh is not None else 80.0
    chem = (chemistry or "LFP").upper()

    # Baseline cycle life from 100% to 70% knee at reference (25 C, 50% DoD)
    baseline_cycle_capacity = 3000 if chem == "LFP" else 2000

    # 1. Thermal Acceleration Factor (Arrhenius-like exponential scaling)
    if temp_c >= 25.0:
        thermal_factor = math.exp(0.040 * (temp_c - 25.0))
    else:
        # Cold temperature lithium-plating stress
        thermal_factor = 1.0 + 0.025 * (25.0 - temp_c)

    # 2. Depth of Discharge (DoD) Stress Factor (Wöhler power law)
    dod_norm = max(10.0, min(100.0, dod_pct))
    dod_factor = (dod_norm / 50.0) ** 1.35

    # 3. Overall Acceleration Stress Multiplier
    acceleration_factor = round(max(0.5, thermal_factor * dod_factor), 2)

    # 4. Projected Remaining Cycles to 70% SOH Knee
    soh_headroom = max(0.0, soh_val - 70.0)
    baseline_remaining_cycles = (soh_headroom / 30.0) * baseline_cycle_capacity
    projected_cycle_life = max(25, int(round(baseline_remaining_cycles / acceleration_factor)))

    # 5. Projected Calendar Months Remaining
    # Daily cycle throughput equivalent
    daily_cycle_fraction = (daily_hours / 4.0) * (dod_norm / 100.0)
    daily_cycles = max(0.05, daily_cycle_fraction)
    days_remaining = projected_cycle_life / daily_cycles
    projected_months = max(1, int(round(days_remaining / 30.4)))

    # 6. Operational Recommendations
    if temp_c >= 38.0:
        recommended_dod = 70.0
    elif dod_norm >= 85.0:
        recommended_dod = 75.0
    else:
        recommended_dod = 80.0

    return {
        "battery_id": battery_id,
        "input_conditions": {
            "current_soh": soh_val,
            "daily_hours": daily_hours,
            "temp_c": temp_c,
            "dod_pct": dod_norm,
        },
        "projected_cycle_life": projected_cycle_life,
        "projected_months_remaining": projected_months,
        "acceleration_factor": acceleration_factor,
        "recommended_dod_limit": recommended_dod,
    }

