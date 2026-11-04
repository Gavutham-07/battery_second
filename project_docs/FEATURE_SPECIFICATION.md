# Feature Specification: ReVolt

## 1. Feature Catalog

### Feature 1: Battery Identity & Lifecycle Registration
- **Description:** Registers an incoming EV battery pack or cell into the platform with manufacturer metadata, chemical composition, and nominal ratings.
- **Inputs:** `battery_id`, `chemistry` (e.g., `LFP`, `NMC`), `rated_capacity_ah`, `voltage`, `manufacturer`, `manufacture_date`, `source_vehicle`.
- **Outputs:** Persisted record in `batteries` collection, registration timestamp.
- **Acceptance Criteria:**
  - Duplicate `battery_id` submissions rejected with HTTP 409 Conflict.
  - `rated_capacity_ah` must be strictly positive ($> 0$).
  - Record initialized with `status: "REGISTERED"`.

### Feature 2: High-Frequency Sensor Telemetry Ingestion
- **Description:** Ingests physical or simulated telemetry packets from sensor hardware or runner bridges.
- **Canonical Endpoint:** `POST /api/live-data`
- **Agreed Payload Keys:**
  ```json
  {
    "battery_id": "BAT-101",
    "sec": 15.0,
    "v": 3.842,
    "i": 0.405,
    "t": 29.10,
    "event": "RUNNING"
  }
  ```
- **Acceptance Criteria:**
  - Validates all keys and numeric bounds ($v \ge 0$, $sec \ge 0$).
  - Attaches source mode (`LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`) and timestamp.
  - Persists packet to `tests` collection.
  - Averages $< 20\text{ ms}$ ingestion response time.

### Feature 3: Acquisition Mode Identification (LIVE, REPLAY, VIRTUAL, DATASET)
- **Description:** Ensures every measurement and assessment record explicitly tags the data origin mode.
- **Allowed Values:** `LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`.
- **Acceptance Criteria:**
  - Ingestion headers or packet metadata define the mode.
  - Downstream reports and passports carry this mode explicitly.
  - UI displays an unmistakable mode indicator badge.

### Feature 4: Decoupled Battery Intelligence Assessment
- **Description:** Analytical evaluation extracting electrical features and predicting health metrics.
- **Distinct Outputs:**
  1. State of Health ($SOH$): Float percentage ($0.0 \text{ to } 100.0\%$).
  2. Available Capacity: Float in Ampere-hours ($Ah$).
  3. Safety Status: Categorical enum (`PASSED`, `WARNING`, `FAILED`, `UNKNOWN`).
  4. Assessment Confidence: Float percentage ($0.0 \text{ to } 100.0\%$).
  5. Data Quality Indicators: Flags for missing telemetry, sampling jitter, or thermal sensor drops.
- **Acceptance Criteria:**
  - $SOH$ and Available Capacity must never be merged into a single field.
  - Assessment confidence drops below $70\%$ if test duration is insufficient.

### Feature 5: Safety Precedence Gate & Escalation Workflow
- **Description:** Gating logic that strictly enforces safety supremacy over health ratings.
- **Decision States:** `CONTINUE_EV`, `SECOND_LIFE_STORAGE`, `FURTHER_TESTING`, `QUARANTINE`, `RECYCLE`.
- **Precedence Hierarchy:**
  1. If `safety_status == "FAILED"` $\rightarrow$ `decision = "RECYCLE"`.
  2. If `safety_status == "WARNING"` or thermal anomalies detected $\rightarrow$ `decision = "QUARANTINE"`.
  3. If `safety_status == "UNKNOWN"` or `confidence < 60%` $\rightarrow$ `decision = "FURTHER_TESTING"`.
  4. If `safety_status == "PASSED"` and `soh >= 80%` $\rightarrow$ `decision = "CONTINUE_EV"`.
  5. If `safety_status == "PASSED"` and `60% <= soh < 80%` $\rightarrow$ `decision = "SECOND_LIFE_STORAGE"`.
  6. If `safety_status == "PASSED"` and `soh < 60%` $\rightarrow$ `decision = "RECYCLE"`.
- **Acceptance Criteria:**
  - High $SOH$ ($>90\%$) with `safety_status == "WARNING"` MUST result in `QUARANTINE`, never `CONTINUE_EV`.
  - `safety_status == "UNKNOWN"` must NEVER trigger an approval.

### Feature 6: Multi-Objective Battery Circularity Optimisation (MBCO)
- **Description:** Decision engine evaluating technical fitness, economic return, safety constraints, and environmental benefit across application routes.
- **Evaluated Routes:** Light EV / Tuk-tuk, Residential Solar BESS, Commercial UPS, Grid Peak Shaver, Direct Material Recycling.
- **Weighting Factors:** Technical ($w_t$), Economic ($w_e$), Safety ($w_s$), Environmental ($w_g$), Traceability ($w_r$). `[PENDING APPROVAL]`
- **Acceptance Criteria:**
  - Returns ranked list of applications with match score and explainability breakdown.

### Feature 7: Transparent Indicative Valuation Breakdown
- **Description:** Generates an itemized economic valuation for the battery trade-in or exchange.
- **Valuation Formula:**
  $$\text{Value} = \text{BaseChemistryValue}(chemistry) \times \frac{SOH}{100} \times \text{Capacity} - \text{DegradationRiskPenalty} - \text{RefurbishCost}$$
  *(Parameters marked `[PENDING APPROVAL]` pending calibration with Member 3)*
- **Acceptance Criteria:**
  - Rejects universal opaque multipliers.
  - Explicitly states: "Indicative prototype estimation, not a certified market quote."

### Feature 8: Conditional What-If Lifetime Simulation
- **Description:** Simulates remaining useful life (RUL) under varying operating scenarios.
- **Inputs:** `daily_hours` ($>0$), `temp_c`, `dod_pct` ($0 < DoD \le 100\%$).
- **Outputs:** Estimated remaining cycle life, projected months to $70\%$ $SOH$ knee, degradation acceleration factor.
- **Acceptance Criteria:**
  - Elevated temperature ($>40^\circ C$) and high DoD ($>90\%$) accelerate degradation rate.

### Feature 9: Digital Battery Passport Generation & Integrity Hash
- **Description:** Creates an immutable, traceable digital record of battery heritage, tests, and assessment.
- **Cryptographic Method:** Canonical JSON serialization (`sort_keys=True`, `separators=(',', ':')`) hashed with SHA-256.
- **Fields:** `battery_id`, `chemistry`, `rated_capacity_ah`, `manufacturer`, `assessment` (soh, safety_status, confidence, decision, mode), `issued_at`, `integrity_hash`.
- **Acceptance Criteria:**
  - Bit-for-bit reproducible hash from valid passport contents.
  - Any modification of a single field causes hash mismatch during verification.

### Feature 10: Passport Integrity Verification Endpoint
- **Description:** Endpoint enabling auditors or buyers to verify a passport's authenticity.
- **Endpoint:** `POST /api/passport/verify`
- **Acceptance Criteria:**
  - Re-computes SHA-256 hash over submitted payload and matches against `integrity_hash`.
  - Returns `valid: true` or `valid: false` with detailed field tamper indicators.

### Feature 11: Technician Approval & Exchange Transactions
- **Description:** Formal sign-off workflow where a certified technician inspects the physical cell and authorizes valuation exchange credit.
- **Inputs:** `battery_id`, `technician_id`, `approved` (boolean), `notes`.
- **Acceptance Criteria:**
  - Persists atomic record to `exchanges` collection.
  - Updates battery status to `"EXCHANGE_APPROVED"` or `"EXCHANGE_REJECTED"`.

### Feature 12: Recycler Inventory & Balanced 4-Cell Pack Grouping
- **Description:** Manages retired cell inventory and computes optimal 4-cell combinations for second-life 4S packs.
- **Grouping Optimization:** Minimizes intra-pack $SOH$ variance ($\sigma_{SOH} \le 3\%$) and internal resistance mismatch. Identifies and isolates weak or degraded cells.
- **Acceptance Criteria:**
  - Groups 4 compatible cells into a virtual pack.
  - Flags any cell with abnormal variance as `UNSUITABLE_FOR_GROUPING`.

### Feature 13: Four Stakeholder Dashboard Tabs
- **Description:** React web interface catering to four primary user personas:
  1. *Customer / Battery Owner:* Evaluation results, circularity options, indicative valuation.
  2. *Technician:* Live diagnostic telemetry stream, safety override triggers, exchange sign-off.
  3. *Recycler:* Available cell inventory, 4-cell grouping generator, scrap routing.
  4. *Public / Auditor:* Digital Battery Passport viewer with interactive QR and SHA-256 integrity verifier.
- **Acceptance Criteria:**
  - Responsive, clean switching between tabs with shared global state.
  - Dynamic 4-mode badge banner (`LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`).

