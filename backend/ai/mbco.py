"""REVOLT Member 3 — Multi-Objective Battery Circularity Optimisation (MBCO) Engine.

Module: backend/ai/mbco.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Multi-dimensional evaluation across:
    1. Technical suitability
    2. Safety eligibility
    3. Evidence confidence
    4. Economic value
    5. Environmental impact
    6. Traceability
- Evaluate and rank circularity pathways:
    - Continued EV use
    - Light EV applications
    - Stationary solar energy storage
    - Backup power
    - Low-power devices
    - Material recovery / recycling
- Enforce mandatory decision precedence:
    1. Critical safety condition -> QUARANTINE_SPECIALIST_REVIEW.
    2. Insufficient or unreliable evidence -> FURTHER_TESTING_REQUIRED.
    3. Technically incompatible application -> Mark ineligible.
    4. Eligible applications -> Multi-objective ranking.
    5. Transparent ranking with reasons and limitations.
- Strict research rules:
    - Never automatically select reuse based solely on high SOH.
    - Never allow economic value to override safety eligibility.
    - Never invent environmental impact values (exclude if unavailable).
    - Configurable weights and application constraints.
    - Strictly JSON-serializable outputs.
"""

from __future__ import annotations

import json
import math
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.ai.assessment import _to_python_type


class CircularityDecision(str, Enum):
    FURTHER_TESTING_REQUIRED = "FURTHER_TESTING_REQUIRED"
    QUARANTINE_SPECIALIST_REVIEW = "QUARANTINE_SPECIALIST_REVIEW"
    CONTINUED_USE_CANDIDATE = "CONTINUED_USE_CANDIDATE"
    SECOND_LIFE_CANDIDATE = "SECOND_LIFE_CANDIDATE"
    RECYCLING_ROUTE = "RECYCLING_ROUTE"


DEFAULT_APPLICATION_POLICIES: Dict[str, Dict[str, Any]] = {
    "continued_ev": {
        "name": "Continued EV Use",
        "description": "Continued high-power passenger/commercial EV duty.",
        "minimum_soh": 80.0,
        "max_resistance_ohm": 0.25,
        "requires_high_confidence": True,
        "circular_hierarchy_tier": 1.0,
    },
    "light_ev": {
        "name": "Light EV Applications",
        "description": "2-wheelers, 3-wheelers, intra-campus shuttles, golf carts.",
        "minimum_soh": 75.0,
        "max_resistance_ohm": 0.35,
        "requires_high_confidence": False,
        "circular_hierarchy_tier": 0.88,
    },
    "solar_storage": {
        "name": "Stationary Solar Energy Storage",
        "description": "Stationary daily cycling for residential or commercial solar PV.",
        "minimum_soh": 70.0,
        "max_resistance_ohm": 0.50,
        "requires_high_confidence": False,
        "circular_hierarchy_tier": 0.80,
    },
    "backup_power": {
        "name": "Backup Power / UPS",
        "description": "Emergency standby power with low daily duty cycle.",
        "minimum_soh": 70.0,
        "max_resistance_ohm": 0.60,
        "requires_high_confidence": False,
        "circular_hierarchy_tier": 0.75,
    },
    "low_power_devices": {
        "name": "Low-Power Devices",
        "description": "Portable power banks, streetlights, low-demand IoT applications.",
        "minimum_soh": 60.0,
        "max_resistance_ohm": 0.80,
        "requires_high_confidence": False,
        "circular_hierarchy_tier": 0.65,
    },
    "recycling": {
        "name": "Material Recovery & Hydrometallurgical Recycling",
        "description": "Black mass processing and elemental recovery (Ni, Co, Li).",
        "minimum_soh": 0.0,
        "max_resistance_ohm": None,
        "requires_high_confidence": False,
        "circular_hierarchy_tier": 0.40,
    },
}

DEFAULT_OBJECTIVE_WEIGHTS: Dict[str, float] = {
    "technical": 0.50,
    "confidence": 0.30,
    "economic": 0.20,
    # Environmental is excluded from numerical calculation when primary LCA data is unavailable
}


def _load_engine_config() -> Optional[Dict[str, Any]]:
    """Attempt to load revolt_decision_engine_config.json if available."""
    current_file = Path(__file__).resolve()
    cfg_path = current_file.parent.parent / "models" / "research_artifacts" / "revolt_decision_engine_config.json"
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def run_mbco_engine(
    assessment_data: Dict[str, Any],
    safety_result: Dict[str, Any],
    confidence_result: Dict[str, Any],
    soh_pct: Optional[float] = None,
    economic_valuations: Optional[Dict[str, Any]] = None,
    application_policies: Optional[Dict[str, Dict[str, Any]]] = None,
    objective_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Execute Multi-Objective Battery Circularity Optimisation (MBCO).

    Mandatory decision precedence:
    1. Critical safety condition -> QUARANTINE_SPECIALIST_REVIEW.
    2. Insufficient or unreliable evidence -> FURTHER_TESTING_REQUIRED.
    3. Technically incompatible application -> mark ineligible.
    4. Eligible applications -> evaluate multi-objective score.
    5. Present ranked pathways with transparent reasons and limitations.
    """
    # Merge policies with research config if present
    policies = dict(DEFAULT_APPLICATION_POLICIES)
    disk_cfg = _load_engine_config()
    if disk_cfg and "application_policies" in disk_cfg:
        for k, v in disk_cfg["application_policies"].items():
            if k in policies:
                policies[k].update(v)
            else:
                policies[k] = v

    if application_policies:
        for k, v in application_policies.items():
            if k in policies:
                policies[k].update(v)
            else:
                policies[k] = v

    weights = dict(DEFAULT_OBJECTIVE_WEIGHTS)
    if objective_weights:
        weights.update(objective_weights)

    safety_state = safety_result.get("safety_state", "UNKNOWN")
    critical_violations = safety_result.get("critical_violations", [])
    conf_status = confidence_result.get("confidence_status", "UNKNOWN")
    conf_score = float(confidence_result.get("confidence_score", 0.0))
    further_testing_flag = confidence_result.get("further_testing_required", False)

    # Check apparent resistance from assessment
    extracted = assessment_data.get("extracted_features", {})
    pulse_feats = extracted.get("pulse_features", {}) or {}
    apparent_res = pulse_feats.get("pulse_05c_resistance_est_ohm")
    if apparent_res is None:
        apparent_res = pulse_feats.get("pulse_1c_resistance_est_ohm")

    # PRECEDENCE LEVEL 1: Critical Safety Condition
    if safety_state == "QUARANTINE_SPECIALIST_REVIEW" or len(critical_violations) > 0:
        pathway_evaluations: Dict[str, Any] = {}
        for route_id, policy in policies.items():
            if route_id == "recycling":
                # Hazardous / specialist recycling route only
                pathway_evaluations[route_id] = {
                    "pathway_name": policy.get("name", route_id),
                    "eligibility": True,
                    "technical_suitability": 0.5,
                    "safety_status": safety_state,
                    "confidence_status": conf_status,
                    "economic_value": "not_configured" if not economic_valuations else economic_valuations.get(route_id, "not_configured"),
                    "environmental_information_status": "not_available_without_primary_lca_data",
                    "ranking_score": None,
                    "reasons": ["Designated for controlled recycling or safe disposal following quarantine review."],
                    "missing_information": [],
                    "limitations": ["Requires hazardous handling protocol."],
                }
            else:
                pathway_evaluations[route_id] = {
                    "pathway_name": policy.get("name", route_id),
                    "eligibility": False,
                    "technical_suitability": 0.0,
                    "safety_status": safety_state,
                    "confidence_status": conf_status,
                    "economic_value": "not_configured" if not economic_valuations else economic_valuations.get(route_id, "not_configured"),
                    "environmental_information_status": "not_available_without_primary_lca_data",
                    "ranking_score": None,
                    "reasons": [
                        "DISQUALIFIED: Critical safety screening violation takes precedence over all SOH and economic considerations.",
                        *critical_violations,
                    ],
                    "missing_information": [],
                    "limitations": ["Reuse strictly prohibited under active safety flags."],
                }

        return _to_python_type({
            "final_decision": CircularityDecision.QUARANTINE_SPECIALIST_REVIEW.value,
            "decision_precedence_applied": "Level 1: Critical Safety Override",
            "precedence_explanation": "Critical safety hazard detected. All second-life reuse pathways immediately disqualified.",
            "pathway_evaluations": pathway_evaluations,
            "ranked_pathways": [
                {"pathway_id": "recycling", "pathway_name": policies["recycling"].get("name"), "ranking_score": None}
            ],
            "recommended_pathway": "recycling" if "recycling" in policies else None,
            "weights_used": weights,
            "weights_disclaimer": "Provisional weights are prototype policy choices, not validated industry standards.",
        })

    # PRECEDENCE LEVEL 2: Insufficient or Unreliable Evidence
    # If confidence is insufficient or further testing is explicitly mandated,
    # or if SOH is required to decide reuse and SOH is completely unavailable.
    soh_status = assessment_data.get("soh_assessment", {}).get("status")
    soh_missing = (soh_pct is None or math.isnan(soh_pct)) and (soh_status != "model_compatible_full_discharge")

    if conf_status == "CONFIDENCE_INSUFFICIENT" or further_testing_flag or soh_missing:
        pathway_evaluations = {}
        for route_id, policy in policies.items():
            min_soh = policy.get("minimum_soh", 0.0)
            missing_info: List[str] = []
            if soh_pct is None:
                missing_info.append("Verified SOH measurement (protocol mismatch or incomplete test)")
            if not pulse_feats.get("complete_pulse_sequence"):
                missing_info.append("Complete pulse response sequence (0.5C and 1C load steps)")

            pathway_evaluations[route_id] = {
                "pathway_name": policy.get("name", route_id),
                "eligibility": False if min_soh > 0 else True,
                "technical_suitability": 0.0 if min_soh > 0 else 0.5,
                "safety_status": safety_state,
                "confidence_status": conf_status,
                "economic_value": "not_configured" if not economic_valuations else economic_valuations.get(route_id, "not_configured"),
                "environmental_information_status": "not_available_without_primary_lca_data",
                "ranking_score": None,
                "reasons": [
                    "DECISION DEFERRED: Insufficient evidence to establish pathway eligibility.",
                    *confidence_result.get("reasons", []),
                ],
                "missing_information": missing_info,
                "limitations": confidence_result.get("limitations", []),
            }

        return _to_python_type({
            "final_decision": CircularityDecision.FURTHER_TESTING_REQUIRED.value,
            "decision_precedence_applied": "Level 2: Evidence Adequacy Precedence",
            "precedence_explanation": (
                "Telemetry or model applicability is insufficient to guarantee second-life suitability. "
                "Further protocol testing required prior to circularity routing."
            ),
            "pathway_evaluations": pathway_evaluations,
            "ranked_pathways": [],
            "recommended_pathway": None,
            "weights_used": weights,
            "weights_disclaimer": "Provisional weights are prototype policy choices, not validated industry standards.",
        })

    # PRECEDENCE LEVEL 3 & 4: Technical Compatibility & Multi-Objective Ranking
    effective_soh = float(soh_pct) if soh_pct is not None else 100.0
    pathway_evaluations = {}
    eligible_candidates: List[Dict[str, Any]] = []

    for route_id, policy in policies.items():
        min_soh = float(policy.get("minimum_soh", 0.0))
        max_res = policy.get("max_resistance_ohm")
        req_high_conf = policy.get("requires_high_confidence", False)

        reasons: List[str] = []
        limitations: List[str] = []
        missing_info: List[str] = []
        is_eligible = True

        # Check SOH threshold
        if effective_soh < min_soh:
            is_eligible = False
            reasons.append(f"Incompatible: SOH {effective_soh:.1f}% is below minimum requirement of {min_soh:.1f}%.")

        # Check resistance threshold
        if max_res is not None and apparent_res is not None:
            if apparent_res > max_res:
                is_eligible = False
                reasons.append(
                    f"Incompatible: Apparent resistance {apparent_res:.3f} Ω exceeds application ceiling of {max_res:.3f} Ω."
                )

        # Check high-confidence requirement
        if req_high_conf and conf_score < 0.75:
            is_eligible = False
            reasons.append(
                f"Incompatible: Route requires high evidence confidence (>= 0.75). Observed confidence is {conf_score:.2f}."
            )

        # Technical suitability score (0.0 to 1.0)
        # Combines SOH, resistance, and circular value hierarchy tier
        tech_score = 0.0
        if is_eligible:
            tier = float(policy.get("circular_hierarchy_tier", 0.70))
            if route_id == "recycling":
                tech_score = tier
            else:
                base_suitability = effective_soh / 100.0
                tech_score = base_suitability * tier
                reasons.append(f"Technically suitable: SOH ({effective_soh:.1f}%) meets threshold ({min_soh:.1f}%).")

        # Economic value handling (transparent, indicative)
        econ_val_raw = None
        econ_score = 0.5  # Neutral default when not configured
        if economic_valuations and route_id in economic_valuations:
            econ_entry = economic_valuations[route_id]
            if isinstance(econ_entry, (int, float)):
                econ_val_raw = float(econ_entry)
                econ_score = min(1.0, max(0.0, econ_val_raw / 5000.0))
            elif isinstance(econ_entry, dict) and "indicative_net_value_inr" in econ_entry:
                val = econ_entry["indicative_net_value_inr"]
                if isinstance(val, (int, float)):
                    econ_val_raw = float(val)
                    econ_score = min(1.0, max(0.0, econ_val_raw / 5000.0))

        # Multi-Objective Score:
        # Score = w_tech * Tech_Score + w_conf * Conf_Score + w_econ * Econ_Score
        # Environmental is excluded from numerical calculation when primary LCA data is unavailable
        ranking_score = None
        if is_eligible:
            w_tech = weights.get("technical", 0.50)
            w_conf = weights.get("confidence", 0.30)
            w_econ = weights.get("economic", 0.20)
            composite = (w_tech * tech_score) + (w_conf * conf_score) + (w_econ * econ_score)
            ranking_score = round(composite, 4)

        pathway_evaluations[route_id] = {
            "pathway_name": policy.get("name", route_id),
            "eligibility": is_eligible,
            "technical_suitability": round(tech_score, 3),
            "safety_status": safety_state,
            "confidence_status": conf_status,
            "economic_value": econ_val_raw if econ_val_raw is not None else "not_configured",
            "environmental_information_status": "not_available_without_primary_lca_data",
            "ranking_score": ranking_score,
            "reasons": reasons if reasons else ["Eligible candidate."],
            "missing_information": missing_info,
            "limitations": limitations,
        }

        if is_eligible and ranking_score is not None:
            eligible_candidates.append({
                "pathway_id": route_id,
                "pathway_name": policy.get("name", route_id),
                "ranking_score": ranking_score,
                "technical_suitability": round(tech_score, 3),
            })

    # Sort eligible candidates descending by ranking score
    eligible_candidates.sort(key=lambda x: x["ranking_score"], reverse=True)

    # PRECEDENCE LEVEL 5: Decision State Determination
    if not eligible_candidates:
        final_decision = CircularityDecision.RECYCLING_ROUTE.value
        rec_pathway = "recycling"
    else:
        top_cand = eligible_candidates[0]["pathway_id"]
        rec_pathway = top_cand
        if top_cand == "continued_ev":
            final_decision = CircularityDecision.CONTINUED_USE_CANDIDATE.value
        elif top_cand in ("light_ev", "solar_storage", "backup_power", "low_power_devices"):
            final_decision = CircularityDecision.SECOND_LIFE_CANDIDATE.value
        else:
            final_decision = CircularityDecision.RECYCLING_ROUTE.value

    return _to_python_type({
        "final_decision": final_decision,
        "decision_precedence_applied": "Level 4 & 5: Multi-Objective Circularity Ranking",
        "precedence_explanation": "Evaluated technical thresholds, safety clearance, confidence evidence, and ranked eligible pathways.",
        "pathway_evaluations": pathway_evaluations,
        "ranked_pathways": eligible_candidates,
        "recommended_pathway": rec_pathway,
        "weights_used": weights,
        "weights_disclaimer": "Provisional weights are prototype policy choices, not validated industry standards.",
    })
