from typing import Dict, Any, List


# Default weights (PENDING APPROVAL per DEC-001 / PEND-001 in DECISION_LOG.md)
DEFAULT_WEIGHTS = {
    "safety": 0.35,
    "technical": 0.25,
    "economic": 0.20,
    "confidence": 0.10,
    "environmental": 0.10,
}

CIRCULARITY_ROUTES = [
    {
        "route_id": "ROUTE_LIGHT_EV",
        "name": "Light EV / 2-Wheeler Repurposing",
        "min_soh": 80.0,
        "max_ir_ohm": 0.075,
        "economic_weight": 0.90,
        "environmental_weight": 0.85,
    },
    {
        "route_id": "ROUTE_SOLAR_BESS",
        "name": "Residential Solar BESS",
        "min_soh": 65.0,
        "max_ir_ohm": 0.120,
        "economic_weight": 0.80,
        "environmental_weight": 0.90,
    },
    {
        "route_id": "ROUTE_COMMERCIAL_UPS",
        "name": "Commercial & Telecom UPS",
        "min_soh": 60.0,
        "max_ir_ohm": 0.100,
        "economic_weight": 0.70,
        "environmental_weight": 0.75,
    },
    {
        "route_id": "ROUTE_GRID_STORAGE",
        "name": "Grid Peak Shaving Storage",
        "min_soh": 70.0,
        "max_ir_ohm": 0.090,
        "economic_weight": 0.75,
        "environmental_weight": 0.80,
    },
    {
        "route_id": "ROUTE_DIRECT_RECYCLE",
        "name": "Direct Hydrometallurgical Recycling",
        "min_soh": 0.0,
        "max_ir_ohm": 1.000,
        "economic_weight": 0.40,
        "environmental_weight": 0.60,
    },
]


def solve_mbco(
    soh: float,
    available_capacity_ah: float,
    safety_status: str,
    confidence: float,
    estimated_ir_ohm: float = 0.040,
    weights: Dict[str, float] = None,
) -> List[Dict[str, Any]]:
    """
    Multi-Objective Battery Circularity Optimisation (MBCO) solver.
    Evaluates candidate routes against technical, safety, economic,
    confidence, and environmental objectives with strict Safety Precedence gating.
    """
    w = weights or DEFAULT_WEIGHTS
    recommendations = []

    is_safe = safety_status == "PASSED"
    is_warning = safety_status == "WARNING"
    is_failed = safety_status == "FAILED"

    for r in CIRCULARITY_ROUTES:
        route_id = r["route_id"]
        is_recycle_route = route_id == "ROUTE_DIRECT_RECYCLE"

        # 1. Safety Eligibility Evaluation
        if is_failed:
            # Under critical failure, ONLY direct recycling is eligible
            safety_eligible = is_recycle_route
            safety_score = 1.0 if is_recycle_route else 0.0
        elif is_warning:
            # Under warning/suspicious, reuse is blocked; quarantine/recycling only
            safety_eligible = is_recycle_route
            safety_score = 0.5 if is_recycle_route else 0.0
        elif is_safe:
            safety_eligible = True
            safety_score = 1.0
        else:  # UNKNOWN
            safety_eligible = False
            safety_score = 0.1

        # 2. Technical Feasibility Evaluation
        soh_val = soh if soh is not None else 0.0
        if is_recycle_route:
            # Recycling is technically 100% feasible especially for degraded cells
            tech_fit = True
            tech_score = 1.0 if soh_val < 60.0 else max(0.2, (100.0 - soh_val) / 100.0)
        else:
            meets_soh = soh_val >= r["min_soh"]
            meets_ir = estimated_ir_ohm <= r["max_ir_ohm"]
            tech_fit = meets_soh and meets_ir

            if meets_soh and meets_ir:
                # Normalized closeness to ideal operating window
                soh_headroom = min(1.0, (soh_val - r["min_soh"]) / 20.0)
                tech_score = 0.70 + 0.30 * soh_headroom
            else:
                tech_score = 0.0

        # 3. Evidence Confidence
        conf_val = confidence if confidence is not None else 0.0
        conf_score = min(1.0, max(0.0, conf_val / 100.0))

        # 4. Economic Index
        econ_score = r["economic_weight"] if tech_fit else 0.1

        # 5. Environmental Offset Index
        env_score = r["environmental_weight"] if tech_fit else 0.1

        # Composite Multi-Objective Score
        if not safety_eligible:
            composite_score = 0.0
            status_note = "SAFETY_OVERRIDE_INELIGIBLE"
        elif not tech_fit:
            composite_score = round(w["safety"] * safety_score * 0.2, 4)
            status_note = f"SOH_BELOW_MINIMUM ({soh_val:.1f}% < {r['min_soh']}%)"
        else:
            raw_score = (
                w["safety"] * safety_score
                + w["technical"] * tech_score
                + w["economic"] * econ_score
                + w["confidence"] * conf_score
                + w["environmental"] * env_score
            )
            composite_score = round(max(0.0, min(1.0, raw_score)), 4)
            status_note = "OPTIMAL_CANDIDATE" if composite_score >= 0.75 else "VIABLE_CANDIDATE"

        recommendations.append({
            "route_id": route_id,
            "route_name": r["name"],
            "suitability_score": composite_score,
            "technical_fit": tech_fit,
            "safety_eligible": safety_eligible,
            "explainability": {
                "safety_score": round(safety_score, 2),
                "technical_score": round(tech_score, 2),
                "economic_score": round(econ_score, 2),
                "confidence_score": round(conf_score, 2),
                "environmental_score": round(env_score, 2),
                "status_note": status_note,
            },
        })

    # Sort descending by suitability score
    recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
    return recommendations

