from typing import Dict, Any


def calculate_valuation(
    battery_id: str,
    chemistry: str,
    rated_capacity_ah: float,
    available_capacity_ah: float,
    soh: float,
    safety_status: str,
    estimated_ir_ohm: float = 0.040,
) -> Dict[str, Any]:
    """
    Computes a transparent, component-level indicative trade-in valuation.
    Rejects universal linear SOH multipliers in favor of itemized economics.
    """
    chem = (chemistry or "LFP").upper()

    # Chemistry-specific economic baselines (PENDING APPROVAL per PEND-002)
    if chem == "LFP":
        base_rate_per_ah = 160.0  # INR per nominal Ah
        scrap_rate_per_ah = 40.0  # INR per Ah material floor
    else:  # NMC / NCA
        base_rate_per_ah = 200.0
        scrap_rate_per_ah = 60.0

    cap_val = available_capacity_ah if available_capacity_ah is not None else (rated_capacity_ah * 0.8)
    soh_val = soh if soh is not None else 80.0
    material_scrap_floor = round(rated_capacity_ah * scrap_rate_per_ah, 2)

    # 1. Gross Residual Capacity Credit
    gross_credit = round(base_rate_per_ah * cap_val * (soh_val / 100.0), 2)

    # 2. Health & Degradation Penalty
    soh_deficit = max(0.0, 100.0 - soh_val)
    ir_penalty_rate = max(0.0, (estimated_ir_ohm - 0.040) * 100.0)
    degradation_penalty = round(
        base_rate_per_ah * cap_val * (soh_deficit / 100.0) * 0.35 + ir_penalty_rate, 2
    )

    # 3. Safety Risk Deduction (Safety Precedence)
    if safety_status == "FAILED":
        # Critical safety failure eliminates all residual utility value
        safety_penalty = round(gross_credit, 2)
    elif safety_status == "WARNING":
        # Warning incurs heavy refurbishing/quarantine penalty (60% of gross)
        safety_penalty = round(gross_credit * 0.60, 2)
    elif safety_status == "UNKNOWN":
        # Unverified status incurs diagnostic risk buffer (35% of gross)
        safety_penalty = round(gross_credit * 0.35, 2)
    else:
        # Nominal safety envelope
        safety_penalty = 0.0

    # 4. Standard Diagnostic Testing Fee
    diagnostic_fee = 25.00

    # 5. Net Indicative Valuation
    net_raw = gross_credit - degradation_penalty - safety_penalty - diagnostic_fee
    net_valuation = round(max(material_scrap_floor, net_raw), 2)

    return {
        "battery_id": battery_id,
        "chemistry": chem,
        "rated_capacity_ah": rated_capacity_ah,
        "available_capacity_ah": cap_val,
        "soh": soh_val,
        "safety_status": safety_status,
        "breakdown": {
            "chemistry_base_rate_per_ah": base_rate_per_ah,
            "gross_capacity_credit_inr": gross_credit,
            "degradation_penalty_inr": degradation_penalty,
            "safety_risk_penalty_inr": safety_penalty,
            "diagnostic_test_fee_inr": diagnostic_fee,
            "material_scrap_floor_inr": material_scrap_floor,
        },
        "net_indicative_valuation_inr": net_valuation,
        "disclaimer": "Indicative prototype estimation, not a certified market quote."
    }

