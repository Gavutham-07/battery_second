import math
import uuid
from typing import List, Dict, Any, Optional


def find_optimal_cell_pack(
    cells: List[Dict[str, Any]],
    chemistry: str = "LFP",
    pack_size: int = 4,
    max_std_dev: float = 3.0,
    target_capacity_ah: Optional[float] = None
) -> Dict[str, Any]:
    """
    Finds the optimal balanced subset of candidate cells that minimizes intra-pack
    SOH variance and ensures standard deviation does not exceed max_std_dev (default <= 3.0%).
    """
    # Filter candidates with valid SOH and matching chemistry (if specified)
    eligible_candidates = [
        c for c in cells
        if c.get("soh") is not None and (not chemistry or c.get("chemistry") == chemistry)
    ]

    if len(eligible_candidates) < pack_size:
        return {
            "eligible": False,
            "chemistry": chemistry,
            "cell_count": 0,
            "required_count": pack_size,
            "available_count": len(eligible_candidates),
            "suitability": "INSUFFICIENT_CELLS",
            "message": f"Insufficient available cells for {pack_size}-cell pack. Found {len(eligible_candidates)}, needed {pack_size}."
        }

    # Sort candidates by SOH ascending
    sorted_candidates = sorted(eligible_candidates, key=lambda c: float(c["soh"]))

    best_window = None
    best_variance = float("inf")
    best_std_dev = float("inf")
    best_mean = 0.0

    # Slide window of size pack_size
    for i in range(len(sorted_candidates) - pack_size + 1):
        window = sorted_candidates[i : i + pack_size]
        soh_values = [float(c["soh"]) for c in window]
        mean_val = sum(soh_values) / pack_size
        variance_val = sum((s - mean_val) ** 2 for s in soh_values) / pack_size
        std_dev_val = math.sqrt(variance_val)

        if variance_val < best_variance:
            best_variance = variance_val
            best_std_dev = std_dev_val
            best_mean = mean_val
            best_window = window

    selected_ids = [c["battery_id"] for c in best_window]
    is_suitable = (best_std_dev <= max_std_dev)
    suitability = "APPROVED_FOR_4S_STORAGE" if is_suitable else "UNSUITABLE_FOR_GROUPING"

    pack_id = f"PACK-4S-{uuid.uuid4().hex[:6].upper()}"

    return {
        "eligible": is_suitable,
        "pack_id": pack_id,
        "chemistry": chemistry,
        "cell_count": pack_size,
        "selected_battery_ids": selected_ids,
        "mean_soh": round(best_mean, 2),
        "soh_variance": round(best_variance, 3),
        "soh_std_dev": round(best_std_dev, 3),
        "max_variance_threshold": max_std_dev,
        "suitability": suitability,
        "target_capacity_ah": target_capacity_ah
    }

