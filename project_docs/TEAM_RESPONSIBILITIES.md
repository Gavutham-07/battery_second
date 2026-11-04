# Team Responsibilities & Ownership Boundaries: ReVolt

## 1. Team Allocation Matrix

| Role / Identifier | Name | Domain Ownership | Primary Deliverables | Strict Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **Member 1** | **Mona** | Hardware & Data Acquisition | ESP32 firmware, INA226 voltage/current sensor, NTC thermistor, serial-to-HTTP bridge, hardware test bench. | Must emit standard `TelemetryPacket` payloads to `POST /api/live-data`. Cannot alter backend schemas. |
| **Member 2** | **Project Owner** | Backend, Database & Transactions | FastAPI application, MongoDB (`revolt_db`) schemas and persistence, API gateway, passport cryptographic engine, exchange transactions. | Coordinates overall architecture and approves all phase transitions. Does not rewrite AI calculations. |
| **Member 3** | **Member 3** | AI, Data Science & Decision Logic | Internal Python package `ai_engine/`: feature extraction, decoupled $SOH$/capacity estimators, safety screener, MBCO optimization solver. | Delivers clean Python function interfaces. Does not manage HTTP routes or database connections directly. |
| **Member 4** | **Amrutha** | Frontend & Stakeholder Dashboards | React/Vite SPA, Tailwind CSS UI components, Recharts telemetry charts, 4-mode selector, 4 stakeholder tab views. | Consumes backend REST API contracts. Does not alter backend contracts or duplicate backend business logic. |

---

## 2. Interaction & Handoff Protocols

### Handoff A: Hardware to Backend (Member 1 $\rightarrow$ Member 2)
- **Interface:** HTTP `POST /api/live-data`
- **Contract Agreement:** Hardware streams JSON packets conforming exactly to:
  `{"battery_id": str, "sec": float, "v": float, "i": float, "t": float, "event": str}`.
- **Rule:** Member 1 will not alter key names or units ($V$, $A$, $^\circ C$) without prior agreement and documentation update in `DATA_DICTIONARY.md`.

### Handoff B: Backend to AI Engine (Member 2 $\leftrightarrow$ Member 3)
- **Interface:** Internal Python module call:
  `ai_engine.evaluate(telemetry_series: list[dict], metadata: dict) -> dict`
- **Contract Agreement:** Backend passes array of preprocessed telemetry; AI engine returns structured evaluation containing decoupled $SOH$ ($0.0-100.0\%$), Available Capacity ($Ah$), Safety Status (`PASSED`/`WARNING`/`FAILED`/`UNKNOWN`), and Confidence ($0.0-100.0\%$).
- **Rule:** Member 2 integrates Member 3's package as a dependency and will not independently re-implement or modify algorithmic logic.

### Handoff C: Backend to Frontend (Member 2 $\rightarrow$ Member 4)
- **Interface:** REST JSON APIs documented in `API_CONTRACTS.md`.
- **Contract Agreement:** Endpoints return predictable HTTP status codes ($200, 201, 400, 404, 409, 500$) and standardized JSON error structures.
- **Rule:** Member 4 can develop UI components using mock fixtures derived directly from `API_CONTRACTS.md` prior to live backend integration.

---

## 3. Governance & Change Control Rules
1. **No Domain Crossing:** No team member or AI assistant may refactor or replace another member's codebase without explicit consultation and Project Owner approval.
2. **Contract Freeze:** Once an interface contract is marked as `FROZEN`, breaking changes require a formal RFC entry in `DECISION_LOG.md`.
3. **Dispute Resolution:** In the event of technical conflicts between requirements, Member 2 (Project Owner) makes the final binding architectural decision.

