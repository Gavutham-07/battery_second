# Project Master Context: ReVolt

## 1. Project Identity & Overview
- **Project Name:** ReVolt: Smart EV Battery Assessment, Valuation and Circularity Platform
- **Repository:** `https://github.com/Gavutham-07/battery_second.git`
- **Active Backend Branch:** `feat-backend`
- **Core Purpose:** An end-to-end platform for circular EV battery lifecycle management—integrating physical sensor telemetry acquisition, decoupled battery intelligence assessment, multi-objective circularity optimization, indicative valuation, verifiable Digital Battery Passports, and recycler cell-to-pack grouping.

## 2. Problem Statement & Mission
Decommissioned electric vehicle (EV) battery packs are frequently disposed of prematurely or routed directly to destructive recycling without rigorous, multi-criteria assessment of their residual utility. Conversely, repurposing batteries into stationary energy storage systems (BESS) or light electric vehicles without stringent safety gating risks catastrophic failure.

ReVolt bridges the gap between battery retirement and circular second-life utilization by:
1. Providing verifiable, multi-mode health and safety screening.
2. Formulating second-life routing via Multi-Objective Battery Circularity Optimisation (MBCO).
3. Ensuring end-to-end data provenance and cryptographic traceability through Digital Battery Passports.

## 3. Core Architectural Principles (Non-Negotiables)
1. **Separation of Intelligence Metrics:** State of Health ($SOH$), Available Capacity ($Ah$), Safety Status, and Assessment Confidence ($0.0 - 100.0\%$) are strictly separate outputs. They must never be collapsed into an ambiguous single score.
2. **Safety Precedence Rule:** Safety screening strictly overrides $SOH$-based reuse recommendations. A cell with $95\%$ $SOH$ exhibiting thermal anomalies or voltage instability must be routed to `QUARANTINE` or `RECYCLE`, never to reuse.
3. **Conservative Safety Default:** An `UNKNOWN` safety status must never be treated as `PASSED`. It mandates escalation to `FURTHER_TESTING` or `QUARANTINE`.
4. **Data Mode Provenance:** Every measurement, test record, and assessment report must be tagged with its originating acquisition mode: `LIVE`, `REPLAY`, `VIRTUAL`, or `DATASET`. Synthetic and virtual data must never be presented as physical experimental results.
5. **Cryptographic Traceability:** Digital Battery Passports rely on canonical JSON SHA-256 integrity hashing to detect tampering across the custody chain.
6. **Transparent Valuation:** Valuation models must show clear, component-level breakdowns rather than opaque linear $SOH$ multipliers.

## 4. Scope & Prototype Boundaries
- **Screening vs. Certification:** ReVolt performs diagnostic screening and preliminary evaluation. It does not replace ISO, UL, or UN 38.3 full automotive pack safety certification.
- **Physical Demonstration Scope:** The physical hardware bench uses an 18650 lithium-ion cell with an ESP32 and INA226 power monitor as a proof of concept, demonstrating the architecture that scales to multi-cell modules.
- **Valuation Status:** Valuations and exchange credits generated are *indicative prototype estimations*, not binding financial or bank-guaranteed market offers.

## 5. Team Allocation & Operational Ownership
- **Member 1 (Mona):** Hardware acquisition, ESP32 firmware, sensor telemetry streaming via `POST /api/live-data`.
- **Member 2 (Project Owner):** Backend API (FastAPI), MongoDB persistence (`revolt_db`), transactions, exchange workflows, and Digital Battery Passport engine.
- **Member 3:** AI/ML intelligence engine, feature extraction, decoupled $SOH$/capacity estimation, safety screening logic, and MBCO optimization.
- **Member 4 (Amrutha):** Frontend application (React/Vite), real-time charts, 4-mode selector, and 4 stakeholder dashboards.

## 6. Status of Unresolved Decisions
- **MBCO Objective Weights:** `[PENDING APPROVAL]` — Exact weighting factors for technical, safety, economic, environmental, and traceability objectives to be finalized between Member 3 and Project Owner.
- **Valuation Formula Constants:** `[PENDING APPROVAL]` — Base market rates per chemistry and degradation penalty coefficients to be calibrated with Member 3.
- **Reference Datasets:** `[PENDING APPROVAL]` — NASA, Oxford, MIT, and Sandia datasets are not assumed to be available until formally verified and approved.
- **Telemetry Batch Ingestion:** `[PENDING APPROVAL]` — Canonical single-packet endpoint `POST /api/live-data` is locked; batch ingestion endpoint deferred until explicitly requested.

