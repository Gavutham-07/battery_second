# API Contracts: ReVolt

## 1. Global Standards & Conventions
- **Base URL:** `http://localhost:8000`
- **Data Exchange Format:** `application/json`
- **Authentication:** Development/Hackathon mode (header `X-Technician-Id` used for technician identification).
- **Unit Standards:**
  - Voltage: Volts ($V$)
  - Current: Amperes ($A$)
  - Temperature: Degrees Celsius ($^\circ C$)
  - Capacity: Ampere-hours ($Ah$)
  - SOH & Confidence: Percentage ($0.0 \text{ to } 100.0\%$)
- **Canonical Enums:**
  - `safety_status`: `"PASSED"`, `"WARNING"`, `"FAILED"`, `"UNKNOWN"`
  - `decision`: `"CONTINUE_EV"`, `"SECOND_LIFE_STORAGE"`, `"FURTHER_TESTING"`, `"QUARANTINE"`, `"RECYCLE"`
  - `mode`: `"LIVE"`, `"REPLAY"`, `"VIRTUAL"`, `"DATASET"`

---

## 2. Core Endpoint Specifications

### 2.1 System Health Check
- **Route:** `GET /api/health`
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "database_name": "revolt_db",
  "timestamp": "2026-11-04T22:00:00Z"
}
```

---

### 2.2 Battery Registration & Management

#### Register Battery
- **Route:** `POST /api/batteries`
- **Request Body:**
```json
{
  "battery_id": "BAT-101",
  "chemistry": "LFP",
  "rated_capacity_ah": 2.5,
  "voltage": 3.2,
  "manufacturer": "EVE Energy",
  "manufacture_date": "2023-01-15",
  "source_vehicle": "Ola S1 Pro"
}
```
- **Response (201 Created):**
```json
{
  "message": "Battery registered successfully",
  "battery_id": "BAT-101",
  "status": "REGISTERED",
  "created_at": "2026-11-04T22:00:00Z"
}
```
- **Error (409 Conflict):** `{"detail": "Battery ID 'BAT-101' already registered"}`

#### Get Battery Details
- **Route:** `GET /api/batteries/{battery_id}`
- **Response (200 OK):**
```json
{
  "battery_id": "BAT-101",
  "chemistry": "LFP",
  "rated_capacity_ah": 2.5,
  "voltage": 3.2,
  "manufacturer": "EVE Energy",
  "manufacture_date": "2023-01-15",
  "source_vehicle": "Ola S1 Pro",
  "status": "REGISTERED",
  "created_at": "2026-11-04T22:00:00Z"
}
```

---

### 2.3 Telemetry Ingestion (Canonical)

#### Ingest Live Telemetry Packet
- **Route:** `POST /api/live-data`
- **Request Body:**
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
- **Request Headers (Optional):**
  - `X-Data-Mode`: `LIVE` | `REPLAY` | `VIRTUAL` | `DATASET` (Default: `LIVE`)
- **Response (200 OK):**
```json
{
  "status": "acknowledged",
  "battery_id": "BAT-101",
  "sec": 15.0,
  "mode": "LIVE"
}
```
- **Notice on Batch Ingestion:** `POST /api/telemetry/batch` is `[PENDING APPROVAL - NOT IMPLEMENTED]`.

#### Get Telemetry History
- **Route:** `GET /api/live-data/{battery_id}?limit=100`
- **Response (200 OK):**
```json
{
  "battery_id": "BAT-101",
  "count": 1,
  "telemetry": [
    {
      "sec": 15.0,
      "v": 3.842,
      "i": 0.405,
      "t": 29.10,
      "event": "RUNNING",
      "mode": "LIVE",
      "timestamp": "2026-11-04T22:00:15Z"
    }
  ]
}
```

---

### 2.4 Battery Intelligence, Assessment & Simulation

#### Trigger Assessment Evaluation
- **Route:** `POST /api/analysis/evaluate`
- **Request Body:**
```json
{
  "battery_id": "BAT-101",
  "chemistry": "LFP",
  "rated_capacity_ah": 2.5
}
```
- **Response (200 OK):**
```json
{
  "battery_id": "BAT-101",
  "soh": 84.5,
  "available_capacity_ah": 2.11,
  "safety_status": "PASSED",
  "confidence": 92.0,
  "decision": "SECOND_LIFE_STORAGE",
  "mode": "LIVE",
  "data_quality": {
    "sample_count": 120,
    "missing_values": 0,
    "thermal_variance": 0.4
  },
  "mbco_recommendations": [
    {
      "route": "Residential Solar BESS",
      "suitability_score": 0.88,
      "technical_fit": true,
      "safety_eligible": true,
      "indicative_valuation_inr": 450.00
    }
  ],
  "created_at": "2026-11-04T22:01:00Z"
}
```

#### What-If Lifetime Simulation
- **Route:** `POST /api/analysis/what-if`
- **Request Body:**
```json
{
  "battery_id": "BAT-101",
  "daily_hours": 4.0,
  "temp_c": 28.0,
  "dod_pct": 80.0
}
```
- **Response (200 OK):**
```json
{
  "battery_id": "BAT-101",
  "projected_cycle_life": 1850,
  "projected_months_remaining": 38,
  "acceleration_factor": 1.15,
  "recommended_dod_limit": 75.0
}
```

---

### 2.5 Digital Battery Passport & Cryptography

#### Generate Passport
- **Route:** `POST /api/passport/generate`
- **Request Body:**
```json
{
  "battery_id": "BAT-101"
}
```
- **Response (201 Created):**
```json
{
  "battery_id": "BAT-101",
  "chemistry": "LFP",
  "rated_capacity_ah": 2.5,
  "manufacturer": "EVE Energy",
  "source_vehicle": "Ola S1 Pro",
  "assessment": {
    "soh": 84.5,
    "available_capacity_ah": 2.11,
    "safety_status": "PASSED",
    "confidence": 92.0,
    "decision": "SECOND_LIFE_STORAGE",
    "mode": "LIVE"
  },
  "issued_at": "2026-11-04T22:02:00Z",
  "integrity_hash": "4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b"
}
```

#### Verify Passport Integrity
- **Route:** `POST /api/passport/verify`
- **Request Body:** Full passport payload including `integrity_hash`.
- **Response (200 OK):**
```json
{
  "valid": true,
  "battery_id": "BAT-101",
  "computed_hash": "4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b",
  "matched": true,
  "verified_at": "2026-11-04T22:05:00Z"
}
```

---

### 2.6 Technician Approval & Exchange Transactions

#### Submit Technician Approval
- **Route:** `POST /api/exchanges/approve`
- **Request Body:**
```json
{
  "battery_id": "BAT-101",
  "technician_id": "TECH-409",
  "approved": true,
  "notes": "Terminal contact clean, no swelling detected."
}
```
- **Response (200 OK):**
```json
{
  "transaction_id": "TXN-88291",
  "battery_id": "BAT-101",
  "status": "APPROVED",
  "indicative_credit_inr": 450.00,
  "timestamp": "2026-11-04T22:03:00Z"
}
```

---

### 2.7 Recycler Inventory & Pack Grouping

#### List Recycler Inventory
- **Route:** `GET /api/inventory`
- **Response (200 OK):**
```json
[
  {
    "battery_id": "BAT-101",
    "chemistry": "LFP",
    "soh": 84.5,
    "status": "AVAILABLE",
    "quantity": 1
  }
]
```

#### Group Cells into Balanced 4-Cell Pack
- **Route:** `POST /api/inventory/group-cells`
- **Request Body:**
```json
{
  "chemistry": "LFP",
  "target_capacity_ah": 2.5
}
```
- **Response (200 OK):**
```json
{
  "pack_id": "PACK-4S-01",
  "chemistry": "LFP",
  "cell_count": 4,
  "selected_battery_ids": ["BAT-101", "BAT-104", "BAT-109", "BAT-112"],
  "mean_soh": 84.2,
  "soh_variance": 0.45,
  "suitability": "APPROVED_FOR_4S_STORAGE"
}
```

