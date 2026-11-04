# Database Schema: revolt_db (MongoDB)

## 1. Overview & Strategy
- **Database Engine:** MongoDB Community Server (v6.0+ / v7.0+)
- **Database Name:** `revolt_db`
- **Architectural Policy:** Exactly five (5) core collections are maintained to satisfy all platform features, preventing schema sprawl while preserving rich document embedding for audit trails and MBCO vectors.

---

## 2. Collection Specifications

### 2.1 Collection: `batteries`
Stores immutable physical asset identity and lifecycle states.

```json
{
  "_id": "ObjectId",
  "battery_id": "String (Unique, Indexed)",
  "chemistry": "String (e.g., 'LFP', 'NMC')",
  "rated_capacity_ah": "Double (> 0.0)",
  "voltage": "Double (Optional)",
  "manufacturer": "String (Optional)",
  "manufacture_date": "String (Optional, ISO Date format)",
  "source_vehicle": "String (Optional)",
  "status": "String ('REGISTERED' | 'TESTING' | 'EVALUATED' | 'EXCHANGED' | 'PACKED' | 'RECYCLED')",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```
- **Indexes:**
  - `{ "battery_id": 1 }` (Unique)
  - `{ "status": 1 }`

---

### 2.2 Collection: `tests`
Stores high-frequency sensor readings and time-series telemetry packets.

```json
{
  "_id": "ObjectId",
  "battery_id": "String (Indexed)",
  "sec": "Double (>= 0.0)",
  "v": "Double (Volts)",
  "i": "Double (Amperes)",
  "t": "Double (Degrees Celsius)",
  "event": "String (e.g., 'RUNNING', 'REST', 'CHARGE', 'DISCHARGE', 'STOP')",
  "mode": "String ('LIVE' | 'REPLAY' | 'VIRTUAL' | 'DATASET')",
  "created_at": "ISODate (Timestamp of ingestion)"
}
```
- **Indexes:**
  - `{ "battery_id": 1, "sec": 1 }` (Compound index for fast timeseries retrieval)
  - `{ "mode": 1 }`

---

### 2.3 Collection: `reports`
Stores analytical evaluations, decoupled SOH/capacity, safety screenings, and MBCO outputs.

```json
{
  "_id": "ObjectId",
  "battery_id": "String (Indexed)",
  "soh": "Double (0.0 to 100.0)",
  "available_capacity_ah": "Double (> 0.0)",
  "safety_status": "String ('PASSED' | 'WARNING' | 'FAILED' | 'UNKNOWN')",
  "confidence": "Double (0.0 to 100.0)",
  "decision": "String ('CONTINUE_EV' | 'SECOND_LIFE_STORAGE' | 'FURTHER_TESTING' | 'QUARANTINE' | 'RECYCLE')",
  "mode": "String ('LIVE' | 'REPLAY' | 'VIRTUAL' | 'DATASET')",
  "data_quality": {
    "sample_count": "Integer",
    "missing_values": "Integer",
    "thermal_variance": "Double"
  },
  "mbco": {
    "status": "String ('COMPUTED' | 'BYPASSED')",
    "selected_route": "String",
    "scores": "Object (Route-wise suitability scores)",
    "weights_used": "Object (Weights PENDING APPROVAL)"
  },
  "indicative_valuation": {
    "amount_inr": "Double",
    "breakdown": "Object"
  },
  "created_at": "ISODate"
}
```
- **Indexes:**
  - `{ "battery_id": 1, "created_at": -1 }`
  - `{ "decision": 1 }`
  - `{ "safety_status": 1 }`

---

### 2.4 Collection: `exchanges`
Stores formal technician approvals, trade-in valuations, and change-of-custody transactions.

```json
{
  "_id": "ObjectId",
  "transaction_id": "String (Unique, Indexed)",
  "battery_id": "String (Indexed)",
  "technician_id": "String (Indexed)",
  "approved": "Boolean",
  "notes": "String (Optional)",
  "indicative_credit_inr": "Double",
  "signature_hash": "String (Technician signoff verification)",
  "timestamp": "ISODate"
}
```
- **Indexes:**
  - `{ "transaction_id": 1 }` (Unique)
  - `{ "battery_id": 1 }`
  - `{ "technician_id": 1 }`

---

### 2.5 Collection: `inventory`
Tracks cell units available for recycler cell-to-pack grouping or second-life dispatch.

```json
{
  "_id": "ObjectId",
  "battery_id": "String (Unique, Indexed)",
  "chemistry": "String",
  "soh": "Double (0.0 to 100.0)",
  "status": "String ('AVAILABLE' | 'RESERVED_FOR_PACK' | 'DISPATCHED_RECYCLING')",
  "pack_id": "String (Nullable, populated when grouped)",
  "quantity": "Integer (Default: 1)",
  "updated_at": "ISODate"
}
```
- **Indexes:**
  - `{ "battery_id": 1 }` (Unique)
  - `{ "chemistry": 1, "status": 1, "soh": 1 }` (Fast pack-matching query)

