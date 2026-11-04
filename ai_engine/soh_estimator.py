from typing import Dict, Any, Tuple, Optional


def estimate_soh_and_capacity(
    features: Dict[str, Any],
    rated_capacity_ah: float,
    chemistry: str = "LFP"
) -> Tuple[Optional[float], Optional[float]]:
    """
    Estimates decoupled State of Health (0.0 to 100.0%) and
    Available Capacity in Ampere-hours (Ah).
    """
    if not features or features.get("sample_count", 0) < 3 or rated_capacity_ah <= 0:
        return None, None

    v_initial = features.get("v_initial")
    v_final = features.get("v_final")
    coulomb_ah = features.get("coulomb_ah", 0.0)
    ir = features.get("estimated_ir_ohm", 0.040)
    chem = (chemistry or "LFP").upper()

    if v_initial is None or v_final is None:
        return None, None

    dv = max(0.01, abs(v_initial - v_final))

    # Expected full-discharge voltage window
    full_span = 0.85 if chem == "LFP" else 1.05

    # If test is a short screening cycle, estimate capacity using Coulomb count & delta V
    if coulomb_ah > 0.005 and dv > 0.02:
        # Scale integrated charge by fraction of discharge curve traversed
        fraction_discharged = min(0.95, max(0.05, dv / full_span))
        raw_capacity = coulomb_ah / fraction_discharged
    else:
        # Initial estimate based on open-circuit potential and internal resistance
        ir_penalty = max(0.0, (ir - 0.035) * 4.0)
        raw_capacity = rated_capacity_ah * max(0.50, 0.95 - ir_penalty)

    # Bound available capacity realistically
    available_capacity_ah = round(
        max(0.1, min(rated_capacity_ah * 1.02, raw_capacity)), 3
    )

    # Calculate decoupled SOH percentage
    soh_pct = round(
        min(100.0, max(0.0, (available_capacity_ah / rated_capacity_ah) * 100.0)), 2
    )

    return soh_pct, available_capacity_ah

