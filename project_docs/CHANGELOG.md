# Changelog: ReVolt

All notable technical and architectural changes across the ReVolt platform are documented here chronologically.

---

## [Phase 10] - 2026-11-05: Frontend Implementation
### Added
- Scaffolding and constructed complete responsive React 18 / Vite 6 single-page dashboard application in `frontend/`.
- Implemented `ModeBanner.jsx` supporting dynamic 4-mode provenance switching (`LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`) and backend connection health monitoring.
- Implemented `CustomerTab.jsx`: Diagnostic health gauges, MBCO circularity route recommendations, transparent itemized trade-in credit valuation, and interactive Arrhenius/Wöhler What-If lifetime simulator sliders.
- Implemented `TechnicianTab.jsx`: Asset registration form, multi-variable SVG telemetry graph, safety screening indicators, and formal technician physical inspection sign-off transaction workflow.
- Implemented `RecyclerTab.jsx`: Live retired cell inventory table with status/chemistry filters, and 4-cell series-parallel balanced pack grouping engine ($\sigma_{SOH} \le 3.0\%$).
- Implemented `AuditorTab.jsx`: EU/Global Digital Battery Passport metadata viewer, SVG QR representation, and in-browser cryptographic SHA-256 tamper verification workbench.
- Implemented `TelemetryChart.jsx`: High-performance, zero-dependency multi-variable SVG graph visualizing Voltage, Current, and Temperature time-series.
- Implemented `QRCodeDisplay.jsx`: Deterministic SVG QR pattern generator with one-click clipboard copying.
- Configured Vite development proxy in `vite.config.js` redirecting `/api` requests to FastAPI backend.
- Created `tests/integration/test_frontend_build.py` with 5 integration tests verifying file structure, build artifacts, tab mounting, 4-mode coverage, and 100% frontend-to-backend API contract alignment.
- Appended Phase 10 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 98 passed in 1.12s.
- Vite production build: Successfully transformed 1595 modules in 2.33s into production bundle (`dist/index.html`, `dist/assets/index.css`, `dist/assets/index.js`) with 0 errors.
- Vite preview server: Verified serving HTTP 200 with HTML title and root mount element on `http://localhost:4173`.
- Zero regressions across 93 previous Phase 2, 3, 4, 5, 6, 7, 8 & 9 tests.

---

## [Phase 9] - 2026-11-05: Recycler Inventory and Balanced Pack Grouping
### Added
- Implemented balanced 4-cell grouping algorithm in `backend/pack_grouper.py` using sliding-window variance minimization on sorted cell arrays.
- Guarantees intra-pack SOH standard deviation $\sigma_{SOH} \le 3.0\%$ for second-life 4S battery storage packs, while isolating weak, damaged, or outlier cells as `UNSUITABLE_FOR_GROUPING`.
- Enforced strict chemistry isolation during pack grouping (strictly preventing mixing LFP and NMC cells).
- Enhanced `GET /api/inventory` in `backend/main.py` with optional query filtering by `status` and `chemistry`.
- Exposed `POST /api/inventory/group-cells` in `backend/main.py` with atomic reservation in `inventory_collection` (`status = "RESERVED_FOR_PACK"`, `pack_id = pack_id`) and status update in `batteries_collection` (`status = "PACKED"`).
- Added `CellGroupingRequest` schema in `backend/schemas.py`.
- Created `tests/unit/test_pack_grouper.py` with 6 unit tests.
- Created `tests/integration/test_inventory_grouping_api.py` with 4 integration tests.
- Appended Phase 9 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 93 passed in 1.19s.
- Live Uvicorn socket execution: Verified `GET /api/inventory` filtering, `POST /api/inventory/group-cells` generating pack `PACK-4S-8CA051` ($\sigma_{SOH} = 0.0\%$), atomic reservation of selected cells, and HTTP 400 error rejection when remaining cells fell below the 4-cell threshold.
- Zero regressions across 83 previous Phase 2, 3, 4, 5, 6, 7 & 8 tests.

---

## [Phase 8] - 2026-11-05: Digital Battery Passport and Transactions
### Added
- Upgraded `backend/passport.py` to support deterministic canonical JSON serialization (`sort_keys=True`, `separators=(',', ':')`) and SHA-256 integrity hash calculation.
- Implemented `verify_battery_passport(passport)` verifying passport integrity and providing detailed tampering diagnosis across all identity and assessment dimensions.
- Added QR code reference string generation (`revolt://passport/{battery_id}?hash={integrity_hash[:16]}`).
- Exposed `POST /api/passport/generate` in `backend/main.py` assembling passport from battery identity and latest report, persisting in `reports` collection, and updating battery status to `PASSPORT_ISSUED`.
- Exposed `POST /api/passport/verify` in `backend/main.py` verifying submitted passport payloads.
- Exposed `GET /api/passport/{battery_id}` in `backend/main.py` retrieving latest battery passport.
- Implemented `POST /api/exchanges/approve` in `backend/main.py` recording technician approval/rejection, creating immutable transaction records in `exchanges_collection` with digital signature hashes, updating battery status to `EXCHANGE_APPROVED` or `EXCHANGE_REJECTED`, and auto-indexing approved cells into `inventory_collection` as `AVAILABLE`.
- Created `tests/unit/test_passport.py` with 7 unit tests.
- Created `tests/integration/test_passport_api.py` with 6 integration tests.
- Appended Phase 8 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 83 passed in 0.98s.
- Live Uvicorn socket execution: Verified end-to-end passport issuance (Hash: `575e4350399e02ae`), valid verification, tamper detection on SOH, retrieval, technician signoff (Transaction `TXN-FC1812BC`), exchange history query, and recycler inventory auto-dispatch.
- Zero regressions across 70 previous Phase 2, 3, 4, 5, 6 & 7 tests.

---

## [Phase 7] - 2026-11-05: Valuation and What-If Simulation
### Added
- Implemented transparent itemized battery trade-in valuation engine in `ai_engine/valuation.py`.
- Formulated valuation model with chemistry-specific base rates (LFP ₹120/Ah, NMC ₹160/Ah), gross capacity credit, SOH degradation penalty, safety risk penalties (50% deduction for `WARNING`, drop to scrap floor for `FAILED`), diagnostic processing fee, and guaranteed material scrap floor.
- Implemented conditional remaining useful life (RUL) what-if simulator in `ai_engine/what_if.py` utilizing Arrhenius thermal stress ($E_a/R$), Wöhler depth-of-discharge ($DoD^{1.4}$) power law, and daily usage turnover scaling to project cycle life and calendar months remaining to 70% knee point.
- Exposed `POST /api/analysis/what-if` in `backend/main.py` accepting operating scenarios (`daily_hours`, `temp_c`, `dod_pct`) and returning lifetime projections and recommended DoD limits.
- Exposed `GET /api/analysis/valuation/{battery_id}` in `backend/main.py` retrieving latest assessment metrics, computing transparent valuation, and persisting breakdown into MongoDB `reports` collection.
- Created `tests/unit/test_valuation_and_simulation.py` with 7 unit tests.
- Created `tests/integration/test_valuation_whatif_api.py` with 3 integration tests.
- Appended Phase 7 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 70 passed in 0.98s.
- Live Uvicorn socket execution: Verified `GET /api/analysis/valuation/{id}` returning itemized valuation (Net: ₹119.0) and `POST /api/analysis/what-if` returning cycle and calendar life projections.
- Zero regressions across 60 previous Phase 2, 3, 4, 5 & 6 tests.

---

## [Phase 6] - 2026-11-05: Safety-Constrained Decisions and MBCO
### Added
- Implemented Multi-Objective Battery Circularity Optimisation framework in `ai_engine/mbco_solver.py`.
- Evaluates 5 circularity routes (Light EV, Solar BESS, Commercial UPS, Grid Peak Storage, Direct Recycling) across 5 criteria: technical fitness, safety eligibility, economic index, evidence confidence, and environmental offset.
- Enforced strict Safety Precedence override in MBCO: batteries with `FAILED` or `WARNING` safety status are stripped of second-life reuse eligibility (`safety_eligible: False`, score 0.0), routing directly to recycling or quarantine.
- Integrated `solve_mbco` into `ai_engine/evaluator.py`, embedding ranked route recommendations and explainability breakdowns into every assessment report.
- Implemented `GET /api/analysis/mbco/{battery_id}` endpoint in `backend/main.py` allowing frontend inspection of circularity recommendations.
- Created `tests/unit/test_mbco_solver.py` with 6 unit tests covering healthy, second-life, end-of-life, safety overrides, custom weights, and explainability.
- Created `tests/integration/test_mbco_api.py` verifying full MBCO evaluation and endpoint retrieval flow.
- Appended Phase 6 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 60 passed in 1.87s.
- Live Uvicorn socket execution: Verified `POST /api/analysis/evaluate` generating MBCO recommendations and `GET /api/analysis/mbco/{id}` returning top route `Residential Solar BESS` (Score: 0.95).
- Zero regressions across 53 previous Phase 2, 3, 4 & 5 tests.

---

## [Phase 5] - 2026-11-05: Battery Intelligence and Assessment
### Added
- Created `ai_engine/` package owned by Member 3 containing the complete diagnostic and assessment pipeline.
- Implemented `ai_engine/features.py` extracting electrical and thermal metrics (Coulomb counting, $dV/dt$, thermal rate $\Delta T/\Delta t$, estimated $R_{int}$, sampling consistency).
- Implemented `ai_engine/safety_screener.py` enforcing chemistry-specific safety thresholds (over/under-voltage, thermal runaway rate, high impedance) for LFP and NMC cells.
- Implemented `ai_engine/soh_estimator.py` providing decoupled SOH percentage ($0.0-100.0\%$) and Available Capacity ($Ah$) calculations.
- Implemented `ai_engine/confidence.py` evaluating mathematical confidence ($0.0-100.0\%$) and data quality indicators.
- Implemented `ai_engine/evaluator.py` enforcing the Safety Precedence Rule across all assessment dimensions.
- Connected `POST /api/analysis/evaluate` route in `backend/main.py` persisting assessment records in MongoDB `reports` collection.
- Created `tests/unit/test_ai_engine.py` with 13 unit tests.
- Created `tests/integration/test_analysis_api.py` verifying full API and database persistence flow.
- Appended Phase 5 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 53 passed in 1.26s.
- Live Uvicorn socket execution: Verified `POST /api/analysis/evaluate` returning decoupled SOH/capacity and enforced safety precedence routing.
- Zero regressions across 39 previous Phase 2, 3 & 4 tests.

---

## [Phase 4] - 2026-11-05: Hardware Acquisition and Data Modes
### Added
- Created `hardware/` package supporting physical and simulated battery data acquisition modes.
- Implemented `hardware/serial_bridge.py`: Serial port scanner, ASCII JSON packet validator, and HTTP streaming bridge.
- Implemented `hardware/replay_runner.py`: CSV/JSON bench cycle loader and `REPLAY` mode HTTP streaming runner.
- Implemented `hardware/virtual_generator.py`: Electro-thermal physics simulator generating realistic 18650 cell data in `VIRTUAL` mode.
- Implemented `hardware/dataset_runner.py`: Benchmark profile loader and `DATASET` mode HTTP streaming runner.
- Created `hardware/data/sample_bench_cycle.csv` with 29 recorded test bench points.
- Created `hardware/data/reference_discharge_profile.json` with 10 benchmark reference discharge points.
- Added `pyserial>=3.5` to `backend/requirements.txt`.
- Created `tests/unit/test_hardware_acquisition.py` with 7 unit tests.
- Created `tests/integration/test_hardware_modes_integration.py` with 5 integration tests.
- Appended Phase 4 test execution evidence to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Automated test suite: 39 passed in 1.12s.
- Live Uvicorn HTTP streaming: `REPLAY` (5/5 acks), `VIRTUAL` (5/5 acks), `DATASET` (5/5 acks) verified over network.
- Physical port scan: Correctly detected lack of physical USB-UART device; marked physical hardware test as `BLOCKED` with fallback operational.
- Zero regressions across 27 previous Phase 2 & 3 tests.

---

## [Phase 3] - 2026-11-04: Backend and Database Foundation
### Added
- Added `init_indexes()` in `backend/db.py` initializing unique index on `batteries.battery_id`, compound index on `tests.battery_id + sec`, and collection indexes on `reports`, `exchanges`, and `inventory`.
- Implemented battery registration routes in `backend/main.py`: `POST /api/batteries` (with 409 conflict detection), `GET /api/batteries` (listing), and `GET /api/batteries/{id}` (404-aware retrieval).
- Implemented canonical telemetry ingestion route `POST /api/live-data` in `backend/main.py` with `X-Data-Mode` header handling (`LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`) and time-series persistence.
- Implemented telemetry query route `GET /api/live-data/{battery_id}` with chronological sorting and limit controls.
- Implemented retrieval endpoints for reports (`GET /api/analysis/reports/{id}`), exchanges (`GET /api/exchanges/{id}`), and recycler inventory (`GET /api/inventory`).
- Added FastAPI `lifespan` handler replacing deprecated startup events.
- Created `tests/integration/test_batteries_api.py` with 5 integration tests.
- Created `tests/integration/test_telemetry_api.py` with 3 integration tests.
- Created `tests/integration/test_retrieval_api.py` with 4 integration tests.
- Appended Phase 3 test results to `project_docs/PHASE_TEST_RESULTS.md`.

### Verified
- Executed full pytest suite: 27 passed, 0 failed in 1.04s.
- Executed live Uvicorn socket verification: 4 live HTTP tests against running server, all passed (HTTP 200/201).
- Total tests executed for Phase 3: 31 tests, all passed.

---

## [Phase 2] - 2026-11-04: Development Environment & Integration Foundation
### Added
- Created `tests/` directory structure with unit and integration test suites.
- Created `tests/unit/test_schemas.py` with 10 validation tests covering DEC-001 and DEC-002 constraints.
- Created `tests/integration/test_api_health.py` covering root metadata, `/api/health`, and CORS headers.
- Created `tests/integration/test_db_persistence.py` verifying collection handles and live MongoDB CRUD transactions.
- Created `project_docs/PHASE_TEST_RESULTS.md` as the permanent phase-wise testing log.
- Added `pytest` and `httpx` to `backend/requirements.txt` and local virtual environment.

### Changed
- Configured `backend/.env` with verified parameters for `APP_NAME`, `APP_ENV`, `PORT`, `HOST`, `MONGO_URI`, `MONGO_DB_NAME`, and `CORS_ORIGINS`.
- Updated `backend/db.py` to read `MONGO_DB_NAME` from environment variables.
- Updated `backend/schemas.py` to enforce DEC-001 (SOH and confidence bounds: $0.0-100.0\%$) and DEC-002 (safety status and decision enums).
- Replaced placeholder command in `backend/main.py` with complete FastAPI application, CORS middleware, root metadata route, and `/api/health` system check.

### Verified
- Executed 15 automated pytest tests: 15 passed, 0 failed.
- Executed live Uvicorn server socket test: `GET /` and `GET /api/health` returned HTTP 200 with `status: healthy` and `database: connected`.
- Executed live MongoDB read/write verification in `revolt_db`.

---

## [Phase 1] - 2026-11-04: Architecture & Documentation Freeze
### Added
- Created `docs/reference/` for original master planning documents.
- Created `project_docs/` containing the complete 18-document governance suite:
  - `PROJECT_MASTER_CONTEXT.md`
  - `SYSTEM_ARCHITECTURE.md`
  - `FEATURE_SPECIFICATION.md`
  - `IMPLEMENTATION_ROADMAP.md`
  - `TEAM_RESPONSIBILITIES.md`
  - `API_CONTRACTS.md`
  - `DATABASE_SCHEMA.md`
  - `DATA_DICTIONARY.md`
  - `TECH_STACK.md`
  - `INTEGRATION_CONTRACTS.md`
  - `SAFETY_AND_DECISION_RULES.md`
  - `TEST_STRATEGY.md`
  - `DEVELOPMENT_RULES.md`
  - `DECISION_LOG.md`
  - `CHANGELOG.md`
  - `CURRENT_PROGRESS.md`
  - `ISSUE_REGISTER.md`
  - `HANDOVER.md`

### Verified
- Zero code files, package manifests, or configurations modified during Phase 1.
- Existing files (`backend/db.py`, `backend/schemas.py`, `backend/passport.py`, `backend/requirements.txt`, `backend/.env`, `backend/main.py`) preserved intact.

---

## [Phase 0] - 2026-11-04: Repository Baseline & Audit
### Added
- Completed initial repository audit.
- Identified Python `3.12.10`, Node `v24.13.0`, and active branch `feat-backend`.
- Discovered placeholder state in `backend/main.py` (`notepad passport.py`) and empty `backend/.env`.
- Audited PyMongo database connection to `revolt_db`.
