"""REVOLT Member 3 — Valuation Engine.

Module: backend/ai/valuation.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Transparent, route-wise indicative economic valuation.
- Support potential circularity pathways:
    - Continued EV use
    - Light EV
    - Stationary solar storage
    - Backup power
    - Material recovery / recycling
- Strictly obey research constraints:
    - Never hardcode old ₹1,200 base value as a verified market price.
    - If reference price data is unavailable, return status 'not_configured'.
    - Expose all cost breakdowns and assumptions transparently.
    - Clearly label all outputs as indicative estimates.
    - Ensure strictly JSON-serializable output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.ai.assessment import _to_python_type

# Default route-specific cost factors (INR per pack/cell unit or per kWh)
DEFAULT_ROUTE_COSTS: Dict[str, Dict[str, float]] = {
    "continued_ev": {
        "testing_cost_inr": 250.0,
        "handling_cost_inr": 150.0,
        "refurbishment_cost_inr": 300.0,
        "logistics_cost_inr": 200.0,
        "processing_cost_inr": 100.0,
        "market_multiplier": 1.0,
    },
    "light_ev": {
        "testing_cost_inr": 200.0,
        "handling_cost_inr": 100.0,
        "refurbishment_cost_inr": 250.0,
        "logistics_cost_inr": 150.0,
        "processing_cost_inr": 100.0,
        "market_multiplier": 0.85,
    },
    "solar_storage": {
        "testing_cost_inr": 150.0,
        "handling_cost_inr": 80.0,
        "refurbishment_cost_inr": 180.0,
        "logistics_cost_inr": 120.0,
        "processing_cost_inr": 80.0,
        "market_multiplier": 0.75,
    },
    "backup_power": {
        "testing_cost_inr": 150.0,
        "handling_cost_inr": 80.0,
        "refurbishment_cost_inr": 150.0,
        "logistics_cost_inr": 120.0,
        "processing_cost_inr": 80.0,
        "market_multiplier": 0.70,
    },
    "low_power_devices": {
        "testing_cost_inr": 80.0,
        "handling_cost_inr": 50.0,
        "refurbishment_cost_inr": 80.0,
        "logistics_cost_inr": 70.0,
        "processing_cost_inr": 40.0,
        "market_multiplier": 0.50,
    },
    "recycling": {
        "testing_cost_inr": 50.0,
        "handling_cost_inr": 80.0,
        "refurbishment_cost_inr": 0.0,
        "logistics_cost_inr": 100.0,
        "processing_cost_inr": 150.0,
        "market_multiplier": 0.25,  # Material scrap recovery index
    },
}

VALUATION_DISCLAIMER = (
    "All values are indicative estimates for decision-support modeling. "
    "They do not constitute binding commercial offers, verified market prices, or appraisals."
)


def _load_valuation_config() -> Optional[Dict[str, Any]]:
    """Load valuation config from revolt_decision_engine_config.json if available."""
    current_file = Path(__file__).resolve()
    cfg_path = current_file.parent.parent / "models" / "research_artifacts" / "revolt_decision_engine_config.json"
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("valuation_config")
        except Exception:
            return None
    return None


def calculate_route_valuation(
    soh_pct: Optional[float],
    rated_capacity_ah: float = 2.5,
    nominal_voltage_v: float = 3.7,
    valuation_config: Optional[Dict[str, Any]] = None,
    pack_cell_count: int = 1,
) -> Dict[str, Any]:
    """Calculate indicative route-wise valuation across potential pathways.

    If reference price data is unavailable, returns status: 'not_configured'.
    """
    # 1. Resolve valuation configuration
    cfg = dict(valuation_config) if valuation_config else {}
    if not cfg:
        disk_cfg = _load_valuation_config()
        if disk_cfg:
            cfg.update(disk_cfg)

    ref_price_kwh = cfg.get("reference_price_per_kwh_inr")

    # If reference price is not set, explicitly return not_configured
    if ref_price_kwh is None or ref_price_kwh <= 0:
        return _to_python_type({
            "status": "not_configured",
            "message": (
                "Valuation reference price per kWh is not configured. "
                "Historical ₹1,200 baseline is unverified and deprecated. "
                "Please configure 'reference_price_per_kwh_inr' in decision engine config."
            ),
            "reference_price_per_kwh_inr": None,
            "route_valuations": {},
            "disclaimer": VALUATION_DISCLAIMER,
        })

    # If SOH is unavailable, valuation cannot determine usable capacity
    if soh_pct is None or soh_pct <= 0:
        return _to_python_type({
            "status": "soh_unavailable",
            "message": "SOH is not available; usable energy capacity cannot be calculated.",
            "reference_price_per_kwh_inr": float(ref_price_kwh),
            "route_valuations": {},
            "disclaimer": VALUATION_DISCLAIMER,
        })

    # Usable energy in kWh
    # E (Wh) = Ah * V * (SOH / 100)
    # E (kWh) = E (Wh) / 1000.0 * pack_cell_count
    unit_nominal_kwh = (rated_capacity_ah * nominal_voltage_v) / 1000.0
    total_rated_kwh = unit_nominal_kwh * pack_cell_count
    usable_kwh = total_rated_kwh * (soh_pct / 100.0)

    route_evals: Dict[str, Any] = {}

    for route_id, costs in DEFAULT_ROUTE_COSTS.items():
        mult = costs.get("market_multiplier", 1.0)
        route_gross_kwh_rate = ref_price_kwh * mult
        gross_value = usable_kwh * route_gross_kwh_rate

        t_cost = costs.get("testing_cost_inr", 0.0) * pack_cell_count
        h_cost = costs.get("handling_cost_inr", 0.0) * pack_cell_count
        r_cost = costs.get("refurbishment_cost_inr", 0.0) * pack_cell_count
        l_cost = costs.get("logistics_cost_inr", 0.0) * pack_cell_count
        p_cost = costs.get("processing_cost_inr", 0.0) * pack_cell_count

        total_deductions = t_cost + h_cost + r_cost + l_cost + p_cost
        indicative_net_value = max(0.0, gross_value - total_deductions)

        route_evals[route_id] = {
            "route_id": route_id,
            "effective_kwh_rate_inr": round(route_gross_kwh_rate, 2),
            "estimated_usable_kwh": round(usable_kwh, 4),
            "gross_value_inr": round(gross_value, 2),
            "cost_breakdown": {
                "testing_cost_inr": round(t_cost, 2),
                "handling_cost_inr": round(h_cost, 2),
                "refurbishment_cost_inr": round(r_cost, 2),
                "logistics_cost_inr": round(l_cost, 2),
                "processing_cost_inr": round(p_cost, 2),
                "total_deductions_inr": round(total_deductions, 2),
            },
            "indicative_net_value_inr": round(indicative_net_value, 2),
            "assumptions": [
                f"SOH: {soh_pct:.1f}%",
                f"Rated capacity: {rated_capacity_ah} Ah, {nominal_voltage_v} V",
                f"Market multiplier: {mult:.2f} of base rate {ref_price_kwh} INR/kWh",
            ],
        }

    return _to_python_type({
        "status": "configured",
        "reference_price_per_kwh_inr": round(float(ref_price_kwh), 2),
        "total_rated_kwh": round(total_rated_kwh, 4),
        "estimated_usable_kwh": round(usable_kwh, 4),
        "route_valuations": route_evals,
        "disclaimer": VALUATION_DISCLAIMER,
    })
