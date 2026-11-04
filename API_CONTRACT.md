# API CONTRACT — REVOLT
## Smart EV Battery Second-Life Platform

This document defines the interface between Member 2 (Backend & Database), Member 3 (AI Engine), and Member 4 (Frontend Integration).
All frontend requests use the central API service with `baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'`.

---

### 1. Battery Registration
- **Endpoint**: `POST /api/register-battery`
- **Owner**: Member 2 (Backend)
- **Description**: Registers an EV battery submitted by an EV owner.
- **Request Body**:
```json
{
  "battery_id": "BAT-101",
  "chemistry": "LFP",          // "LFP" | "NMC" | "NCA"
  "rated_capacity_ah": 50.0,
  "owner_name": "John Doe",    // Optional
  "vehicle_model": "Tata Nexon EV" // Optional
}
```
- **Response `201 Created` / `200 OK`**:
```json
{
  "status": "success",
  "message": "Battery registered successfully",
  "battery": {
    "battery_id": "BAT-101",
    "chemistry": "LFP",
    "rated_capacity_ah": 50.0,
    "registration_date": "2026-11-04T10:30:00Z",
    "status": "Awaiting Screening"
  }
}
```

---

### 2. Battery Queue & Listing
- **Endpoint**: `GET /api/batteries`
- **Owner**: Member 2 (Backend)
- **Query Params**: `?status=all` or `?owner_id=...`
- **Description**: Retrieves all registered batteries for Owner status view and Technician queue.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "batteries": [
    {
      "battery_id": "BAT-101",
      "chemistry": "LFP",
      "rated_capacity_ah": 50.0,
      "registration_date": "2026-11-04T10:30:00Z",
      "status": "Awaiting Screening", // "Awaiting Screening" | "Testing in Progress" | "Assessed" | "Approved"
      "soh_estimate": null,
      "recommended_action": null
    }
  ]
}
```

---

### 3. Start Live Telemetry / Stream Simulation
- **Endpoint**: `POST /api/simulate-stream`
- **Owner**: Member 2 (Backend) & Member 1 (Hardware / Sim)
- **Description**: Triggers a 90-second streaming session for a given battery using the selected data source mode.
- **Request Body**:
```json
{
  "battery_id": "BAT-101",
  "data_source": "virtual_circuit", // "live_hardware" | "replay_recorded" | "virtual_circuit" | "lab_dataset"
  "test_profile": "healthy"         // "healthy" | "moderately_aged" | "thermally_unsafe"
}
```
- **Response `200 OK`**:
```json
{
  "status": "started",
  "battery_id": "BAT-101",
  "duration_seconds": 90,
  "message": "Screening stream initialized"
}
```

---

### 4. Fetch Live Screening Telemetry
- **Endpoint**: `GET /api/live-data/{battery_id}`
- **Owner**: Member 2 (Backend)
- **Description**: Polled every ~1 second during the active 90s screening test.
- **Response `200 OK`**:
```json
{
  "battery_id": "BAT-101",
  "timestamp": 1730739000,
  "elapsed_seconds": 45,
  "remaining_seconds": 45,
  "is_complete": false,
  "data_source": "virtual_circuit",
  "current_reading": {
    "voltage": 3.28,       // Volts
    "current": 10.15,      // Amperes
    "temperature": 29.4    // °C
  },
  "history": [
    { "time": 0, "voltage": 3.35, "current": 10.0, "temperature": 25.0 },
    { "time": 1, "voltage": 3.34, "current": 10.1, "temperature": 25.1 }
  ]
}
```

---

### 5. Run AI Assessment
- **Endpoint**: `POST /api/analyze`
- **Owner**: Member 3 (AI & ML) & Member 2 (Backend)
- **Description**: Evaluates the 90-second screening data to predict SOH, safety flags, and second-life matching.
- **Request Body**:
```json
{
  "battery_id": "BAT-101"
}
```
- **Response `200 OK`**:
```json
{
  "battery_id": "BAT-101",
  "soh_estimate": 84.5,
  "confidence_score": 0.94,
  "confidence_level": "High",           // "High" | "Medium" | "Low"
  "safety_status": "Safe",              // "Safe" | "Warning" | "Critical Danger"
  "safety_flags": [],                   // e.g. ["Elevated Thermal Drift", "Internal Resistance Spike"]
  "plain_english_explanation": "Cell demonstrates stable voltage curves with minimal degradation under load. SOH is well within the 80%+ threshold suitable for stationary and light EV secondary use.",
  "recommended_action": "Repurpose",    // "Direct Reuse" | "Repurpose" | "Recycle"
  "remaining_capacity_ah": 42.25,
  "residual_life_years": 4.8,
  "exchange_credit_inr": 28500,
  "second_life_matches": [
    {
      "application": "Home Solar Storage",
      "suitability": "Optimal",         // "Optimal" | "Good" | "Not Recommended"
      "predicted_lifetime_years": 5.2,
      "reason": "Stable discharge plateau matches daily solar charge cycles."
    },
    {
      "application": "E-Rickshaw / Light EV",
      "suitability": "Good",
      "predicted_lifetime_years": 3.4,
      "reason": "Capable of moderate peak discharge bursts."
    },
    {
      "application": "UPS / Telecom Backup",
      "suitability": "Good",
      "predicted_lifetime_years": 6.0,
      "reason": "Low duty cycle preserves remaining capacity."
    },
    {
      "application": "Solar Streetlight",
      "suitability": "Optimal",
      "predicted_lifetime_years": 5.5,
      "reason": "Low C-rate requirement ensures prolonged operational life."
    }
  ]
}
```

---

### 6. What-If Simulator
- **Endpoint**: `POST /api/what-if`
- **Owner**: Member 3 (AI Engine)
- **Description**: Simulates residual lifetime under customizable operating conditions.
- **Request Body**:
```json
{
  "battery_id": "BAT-101",
  "daily_usage_hours": 6.0,         // Slider: 1 to 16 hours
  "ambient_temperature_c": 30.0,    // Slider: 15 to 45 °C
  "depth_of_discharge_pct": 70.0    // Slider: 20 to 100%
}
```
- **Response `200 OK`**:
```json
{
  "battery_id": "BAT-101",
  "baseline_residual_life_years": 4.8,
  "simulated_residual_life_years": 4.1,
  "cycle_life_projection": 1650,
  "thermal_stress_factor": "Moderate",
  "recommendation_note": "Limiting Depth of Discharge to 70% extends battery second life by ~1.2 years."
}
```

---

### 7. Technician Approval & QR Passport Minting
- **Endpoint**: `POST /api/approve-and-exchange`
- **Owner**: Member 2 (Backend)
- **Description**: Technician approves assessment, sets approved second-life route, mints QR Battery Passport with SHA-256 hash.
- **Request Body**:
```json
{
  "battery_id": "BAT-101",
  "technician_id": "TECH-04",
  "technician_notes": "Passed visual inspection. Cell terminal integrity confirmed.",
  "approved_route": "Home Solar Storage",
  "exchange_credit_inr": 28500
}
```
- **Response `200 OK`**:
```json
{
  "status": "approved",
  "battery_id": "BAT-101",
  "passport_id": "PASSPORT-BAT-101-2026",
  "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "minted_at": "2026-11-04T11:45:00Z",
  "verification_url": "http://localhost:5173/verify/BAT-101"
}
```

---

### 8. Verify QR Battery Passport
- **Endpoint**: `GET /api/verify/{battery_id}`
- **Owner**: Member 2 (Backend)
- **Description**: Public verification endpoint called by scanning the QR code.
- **Response `200 OK`**:
```json
{
  "verification_status": "Valid", // "Valid" | "Invalid" | "Not Found" | "Tampered"
  "battery_id": "BAT-101",
  "soh_estimate": 84.5,
  "safety_status": "Safe",
  "approved_route": "Home Solar Storage",
  "technician_id": "TECH-04",
  "minted_at": "2026-11-04T11:45:00Z",
  "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "hash_integrity_verified": true
}
```

---

### 9. Owner Preference Submission
- **Endpoint**: `POST /api/owner-preference`
- **Owner**: Member 2 (Backend)
- **Description**: EV Owner submits preference (Reuse / Repurpose / Sell & Exchange).
- **Request Body**:
```json
{
  "battery_id": "BAT-101",
  "owner_preference": "Sell / Exchange" // "Reuse" | "Repurpose" | "Sell / Exchange"
}
```
- **Response `200 OK`**:
```json
{
  "status": "updated",
  "battery_id": "BAT-101",
  "owner_preference": "Sell / Exchange",
  "note": "Preference stored separately from AI technical recommendation."
}
```

---

### 10. Recycler Batch Sorting & Inventory
- **Endpoint**: `GET /api/recycler-batch`
- **Owner**: Member 2 (Backend)
- **Description**: Retrieves assessed batteries categorized into Reuse, Repurpose, or Recycle batches.
- **Response `200 OK`**:
```json
{
  "summary": {
    "total_batteries": 124,
    "total_waste_diverted_kg": 4350,
    "total_co2_avoided_kg": 9820,
    "total_recovered_value_inr": 2840000
  },
  "batches": {
    "reuse": [
      { "battery_id": "BAT-101", "soh": 84.5, "chemistry": "LFP", "safety": "Safe", "status": "Ready for Pack" }
    ],
    "repurpose": [
      { "battery_id": "BAT-103", "soh": 72.0, "chemistry": "NMC", "safety": "Safe", "status": "Stationary Storage Batch" }
    ],
    "recycle": [
      { "battery_id": "BAT-108", "soh": 46.2, "chemistry": "NCA", "safety": "Critical Danger", "status": "Material Hydrometallurgy" }
    ]
  }
}
```

---

### 11. Cell Inventory & Pack Grouping Algorithm
- **Endpoint**: `GET /api/cells-inventory` and `POST /api/group-cells`
- **Owner**: Member 3 (AI Engine) & Member 2 (Backend)
- **Description**: Cell-level grouping based on chemistry, capacity, and SOH delta tolerance.
- **Request Body (`POST /api/group-cells`)**:
```json
{
  "cell_ids": ["CELL-001", "CELL-002", "CELL-003", "CELL-004"],
  "target_chemistry": "LFP",
  "max_soh_delta": 3.0
}
```
- **Response `200 OK`**:
```json
{
  "group_id": "PACK-MOD-A",
  "cells": [
    { "cell_id": "CELL-001", "soh": 84.2 },
    { "cell_id": "CELL-002", "soh": 84.8 },
    { "cell_id": "CELL-003", "soh": 83.9 },
    { "cell_id": "CELL-004", "soh": 84.5 }
  ],
  "average_soh": 84.35,
  "soh_spread": 0.9,
  "compatibility": "Excellent",
  "weak_cell_warnings": []
}
```

