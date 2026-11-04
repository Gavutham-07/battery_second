# Integration Contracts & Cross-Domain Interfaces: ReVolt

## 1. Interface 1: Hardware to Backend (Member 1 $\rightarrow$ Member 2)

### Protocol & Endpoint
- **Transport:** HTTP `POST` over local Wi-Fi or Serial-to-HTTP Gateway
- **Target URL:** `http://localhost:8000/api/live-data`
- **Sampling Frequency:** $1.0\text{ Hz}$ to $5.0\text{ Hz}$

### Exact Ingestion Contract
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

### Constraints & Edge Handling
- If Wi-Fi is lost, ESP32 buffers up to 50 packets locally or serial bridge logs to CSV for subsequent `REPLAY` ingestion.
- Missing sensor values must be represented as `null` or handled gracefully; packets with invalid JSON syntax are dropped with HTTP 422.

---

## 2. Interface 2: Backend to AI Engine (Member 2 $\leftrightarrow$ Member 3)

### Invocation Architecture
- Member 3's engine is packaged as an internal Python module: `ai_engine`.
- Member 2's FastAPI route calls the evaluation interface synchronously in an executor or asynchronously:

```python
from ai_engine.evaluator import evaluate_battery

# Function Signature:
def evaluate_battery(
    telemetry_records: list[dict],
    battery_metadata: dict
) -> dict:
    ...
```

### Input Contract
1. `telemetry_records`: Chronologically sorted list of `TelemetryPacket` dictionaries.
2. `battery_metadata`: `{"battery_id": str, "chemistry": str, "rated_capacity_ah": float}`.

### Output Contract
The AI engine must return a dictionary conforming to:
```python
{
    "battery_id": str,
    "soh": float,                      # 0.0 to 100.0%
    "available_capacity_ah": float,    # > 0.0 Ah
    "safety_status": str,              # "PASSED" | "WARNING" | "FAILED" | "UNKNOWN"
    "confidence": float,               # 0.0 to 100.0%
    "decision": str,                   # "CONTINUE_EV" | "SECOND_LIFE_STORAGE" | "FURTHER_TESTING" | "QUARANTINE" | "RECYCLE"
    "mode": str,                       # "LIVE" | "REPLAY" | "VIRTUAL" | "DATASET"
    "data_quality": {
        "sample_count": int,
        "missing_values": int,
        "thermal_variance": float
    },
    "mbco_recommendations": list[dict] # Ranked second-life routes
}
```

---

## 3. Interface 3: Backend to Frontend (Member 2 $\rightarrow$ Member 4)

### Transport & Headers
- JSON payloads over standard REST HTTP.
- Cross-Origin Resource Sharing (CORS) enabled for `http://localhost:3000` and `http://localhost:5173`.
- Error responses standardize on:
  ```json
  {
    "detail": "Error description message",
    "error_code": "ERR_SPECIFIC_CODE",
    "timestamp": "2026-11-04T22:00:00Z"
  }
  ```

### Mock Development Support
Member 4 can consume mock JSON responses matching `API_CONTRACTS.md` directly, allowing UI development to proceed in parallel with backend construction.

