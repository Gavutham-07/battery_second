# Architectural Decision Log: ReVolt

## 1. Approved Decisions

### [DEC-001] SOH & Confidence Standardization
- **Date:** 2026-11-04
- **Decision:** SOH and assessment confidence are standardized as floating-point percentages strictly bounded between $0.0$ and $100.0\%$.
- **Rationale:** Ensures arithmetic consistency across valuation calculations, Pydantic validation, AI outputs, and frontend progress indicators.
- **Approved By:** Project Owner

---

### [DEC-002] Categorical Enumerations for Safety & Circularity
- **Date:** 2026-11-04
- **Decision:**
  - `safety_status`: `["PASSED", "WARNING", "FAILED", "UNKNOWN"]`
  - `decision`: `["CONTINUE_EV", "SECOND_LIFE_STORAGE", "FURTHER_TESTING", "QUARANTINE", "RECYCLE"]`
  - Safety and decision are maintained as separate fields.
  - `UNKNOWN` must never be treated as `PASSED`.
- **Rationale:** Prevents arbitrary string typos and enforces the Safety Precedence Rule.
- **Approved By:** Project Owner

---

### [DEC-003] Canonical Telemetry Ingestion Endpoint
- **Date:** 2026-11-04
- **Decision:** Retain original `POST /api/live-data` with payload keys `battery_id`, `sec`, `v`, `i`, `t`, `event`. Reject `/telemetry/packet` renaming. Batch ingestion endpoint marked `[PENDING APPROVAL]`.
- **Rationale:** Preserves compatibility with existing hardware firmware developed by Mona (Member 1).
- **Approved By:** Project Owner

---

### [DEC-004] Internal Python Package for AI Engine
- **Date:** 2026-11-04
- **Decision:** Member 3's AI/decision engine will be integrated as an internal Python package within the monorepo (`ai_engine/`) rather than an external microservice.
- **Rationale:** Minimizes network overhead, avoids complex deployment orchestration during the hackathon, and simplifies local development.
- **Approved By:** Project Owner

---

### [DEC-005] Reference Documents Preservation
- **Date:** 2026-11-04
- **Decision:** Establish `docs/reference/` in repository root to preserve original PDF/DOCX master execution and design documents without modification.
- **Rationale:** Ensures historical reference baseline is retained alongside living Markdown documentation.
- **Approved By:** Project Owner

---

### [DEC-006] Five Core MongoDB Collections
- **Date:** 2026-11-04
- **Decision:** Limit database to exactly five primary collections: `batteries`, `tests`, `reports`, `exchanges`, and `inventory`.
- **Rationale:** Prevents schema fragmentation; audit trails and MBCO vectors are embedded cleanly as subdocuments.
- **Approved By:** Project Owner

---

## 2. Pending Decisions

| Decision ID | Item | Proposed Options | Current Status | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **PEND-001** | MBCO Objective Weights | Balanced ($0.2$ each) vs Safety-Weighted ($0.4$ safety, $0.2$ others) | `PENDING APPROVAL` | Member 3 / Project Owner |
| **PEND-002** | Valuation Base Rates | Fixed INR per residual Ah by chemistry | `PENDING APPROVAL` | Member 3 / Project Owner |
| **PEND-003** | Public Benchmark Datasets | NASA Ames, Oxford, MIT, Sandia | `PENDING APPROVAL` | Project Owner |
| **PEND-004** | Batch Telemetry Ingestion | `POST /api/telemetry/batch` | `PENDING APPROVAL` | Member 1 / Member 2 |

