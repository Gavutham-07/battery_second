# ai_engine/ — Legacy Prototype

> [!WARNING]
> **This directory is a legacy prototype. It is NOT used in any production API route.**
> Do not import from this directory for production assessment, valuation, or decision logic.

## Status

| Item | Status |
|------|--------|
| Production use | **Deprecated** |
| Authoritative engine | `backend/engine.py` (Member 3 implementation) |
| Retained for | Reference, historical comparison, and test compatibility |

## Background

The `ai_engine/` package was an earlier implementation developed during Phases 0–10.
Starting from Phase 11 (integration), all production assessment uses only the
**Member 3 authoritative engine** (`backend.engine.evaluate_battery`).

The Member 3 engine:
- Returns `soh_pct: null` for short-pulse ESP32 data (scientifically correct)
- Uses `backend.ai.mbco` for MBCO circularity decisions
- Uses `backend.ai.safety` for safety screening without fabricated defaults
- Uses `backend.ai.valuation.calculate_route_valuation` with explicit `not_configured` handling
- Uses `backend.ai.lifetime.calculate_lifetime_scenarios` with `not_calibrated` status

## Why retained

Some integration tests reference `ai_engine` module paths. Deleting this directory
would break those tests. This directory is kept as-is to preserve test compatibility
and for academic reference.

**Do not add new features or fix bugs in this directory.** All new work goes in `backend/`.

