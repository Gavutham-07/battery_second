# System Architecture: ReVolt

## 1. Architectural Overview
ReVolt is designed as a modular, decoupled platform structured into five discrete tiers. Each tier has strict interface boundaries, enabling independent development and testing across hardware, backend, AI engine, and frontend.

```mermaid
flowchart TD
    subgraph L1 ["Tier 1: Data Acquisition & Modes (Member 1 - Mona)"]
        A1["ESP32 + INA226 + NTC Sensor (LIVE)"] --> BR["Serial / HTTP Telemetry Bridge"]
        A2["Replay File Runner (REPLAY)"] --> BR
        A3["Virtual Signal Generator (VIRTUAL)"] --> BR
        A4["Standardized Battery Data (DATASET - PENDING)"] --> BR
    end

    subgraph L2 ["Tier 2: Backend API & Persistence (Member 2 - Project Owner)"]
        BR -->|"POST /api/live-data"| API["FastAPI Backend Gateway"]
        API --> VAL["Schema Validation & Mode Tagger"]
        VAL --> DB[("MongoDB: revolt_db")]
        DB --- C1["batteries"]
        DB --- C2["tests (telemetry records)"]
        DB --- C3["reports (assessment records)"]
        DB --- C4["exchanges (transactions)"]
        DB --- C5["inventory (recycler cells)"]
    end

    subgraph L3 ["Tier 3: Battery Intelligence & MBCO (Member 3)"]
        API <-->|"Internal Python Package Calls"| AI["AI Engine & Optimizer"]
        AI --> FE["Feature Extractor (dV/dt, Coulomb, ΔT)"]
        FE --> SOH["SOH & Capacity Estimator"]
        FE --> SAFE["Safety Screening Screener"]
        SOH & SAFE --> CONF["Confidence & Data Quality Evaluator"]
        CONF --> GATE{"Safety Precedence Gate"}
        GATE -->|"FAILED / Suspicious"| QUAR["QUARANTINE / SPECIALIST"]
        GATE -->|"UNKNOWN / Sparse"| TEST["FURTHER_TESTING"]
        GATE -->|"PASSED & High Confidence"| MBCO["MBCO Circularity Optimizer"]
        MBCO --> VALU["Indicative Valuation & What-If Simulation"]
    end

    subgraph L4 ["Tier 4: Passport & Cryptography (Member 2 - Project Owner)"]
        API --> DBP["Digital Battery Passport Generator"]
        DBP --> HASH["SHA-256 Canonical JSON Hash"]
        HASH --> QR["QR Code & Integrity Verification API"]
    end

    subgraph L5 ["Tier 5: Presentation & Dashboard (Member 4 - Amrutha)"]
        API <-->|"REST APIs"| UI["React (Vite) Application"]
        UI --> T1["Tab 1: Circularity Matchmaker (Owner)"]
        UI --> T2["Tab 2: Technician Exchange (Technician)"]
        UI --> T3["Tab 3: Recycler Pack Grouping (Recycler)"]
        UI --> T4["Tab 4: Battery Passport Explorer (Public/Audit)"]
    end
```

---

## 2. Tier Details & Responsibilities

### Tier 1: Data Acquisition & Acquisition Modes
- **Owner:** Member 1 (Mona)
- **Functions:**
  - Interfaces physical sensors (INA226 voltage/current monitor and temperature probe via ESP32 I2C).
  - Emits telemetry packets over USB-serial or Wi-Fi HTTP bridge.
  - Generates synthetic and simulated streams for `REPLAY`, `VIRTUAL`, and approved `DATASET` modes.
- **Contract:** All streams deliver telemetry via `POST /api/live-data` conforming to `TelemetryPacket`.

### Tier 2: Gateway & Persistence Layer
- **Owner:** Member 2 (Project Owner)
- **Functions:**
  - High-performance asynchronous FastAPI REST gateway.
  - Validates all incoming payloads against Pydantic models.
  - Enforces database indexes and persists records in MongoDB (`revolt_db`).
  - Manages the five primary collections: `batteries`, `tests`, `reports`, `exchanges`, and `inventory`.
  - Coordinates transactions and audit trails for exchange approvals.

### Tier 3: Battery Intelligence & MBCO Engine
- **Owner:** Member 3
- **Functions:**
  - Deployed as an internal Python package (`ai_engine/`) invoked directly by FastAPI endpoints.
  - Performs feature extraction: internal resistance ($IR$), Coulomb counting, charge/discharge slopes ($dV/dt$), and thermal rise ($\Delta T$).
  - Estimates decoupled $SOH$ ($0.0 - 100.0\%$) and Available Capacity ($Ah$).
  - Applies deterministic safety rules producing `PASSED`, `WARNING`, `FAILED`, or `UNKNOWN`.
  - Calculates confidence score ($0.0 - 100.0\%$) based on data density and measurement variance.
  - Multi-Objective Battery Circularity Optimisation (MBCO) evaluates technical feasibility, safety constraints, economic return, and application matching.

### Tier 4: Digital Battery Passport & Verification
- **Owner:** Member 2 (Project Owner)
- **Functions:**
  - Generates tamper-evident battery passports upon technician approval or assessment completion.
  - Computes deterministic SHA-256 hashes over sorted, canonical JSON strings (`sort_keys=True`, `separators=(',', ':')`).
  - Exposes passport verification endpoint `POST /api/passport/verify` to detect payload alteration.

### Tier 5: Presentation & Stakeholder Dashboards
- **Owner:** Member 4 (Amrutha)
- **Functions:**
  - Single Page Application built with React, Vite, and Tailwind CSS.
  - Provides a 4-mode acquisition selector pill (`LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`).
  - Renders 4 dedicated stakeholder tabs with live telemetry charts, what-if parameter sliders, cell grouping matrices, and passport QR badges.

---

## 3. End-to-End Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant HW as Hardware / Mode Source
    participant API as FastAPI Gateway
    participant DB as MongoDB (revolt_db)
    participant AI as AI & MBCO Engine
    participant UI as React Dashboard

    HW->>API: POST /api/live-data (TelemetryPacket)
    API->>DB: Insert into 'tests' collection
    API-->>HW: 200 OK (Packet Ack)

    UI->>API: POST /api/analysis/evaluate (battery_id)
    API->>DB: Query telemetry time-series from 'tests'
    API->>AI: evaluate_battery(telemetry_series, battery_metadata)
    AI->>AI: Extract features, compute SOH, run safety screening
    AI->>AI: Execute Safety Precedence Gate & MBCO optimization
    AI-->>API: AnalysisReport (SOH, Capacity, Safety, Decision, Confidence)
    API->>DB: Store report in 'reports' collection
    API-->>UI: Return AnalysisReport JSON

    UI->>API: POST /api/passport/generate (battery_id)
    API->>DB: Read battery metadata & latest report
    API->>API: Compute canonical SHA-256 integrity hash
    API->>DB: Save passport record
    API-->>UI: Return Passport JSON + integrity_hash
```

---

## 4. Fallback & Resilience Strategy
1. **Network / Hardware Offline:** When physical ESP32 hardware is disconnected, the system seamlessly transitions to `REPLAY` (pre-recorded bench cycle) or `VIRTUAL` mode to allow continuous demonstration and testing.
2. **Database Resilience:** MongoDB connections utilize `serverSelectionTimeoutMS=5000` with graceful error logging and connection health verification.
3. **Safety Fallback:** If sensor telemetry contains anomalous missing timestamps or incomplete discharge profiles, assessment confidence drops, triggering a mandatory `FURTHER_TESTING` state rather than risking false-positive reuse.

