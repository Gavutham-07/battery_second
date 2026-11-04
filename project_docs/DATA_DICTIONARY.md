# Data Dictionary & Canonical Naming Registry: ReVolt

## 1. Permanent Canonical Identifiers

| Canonical Identifier | Permitted Values / Type | Canonical Units | Definition & System Role |
| :--- | :--- | :--- | :--- |
| `project_name` | `"ReVolt"` | N/A | Official platform name. |
| `database_name` | `"revolt_db"` | N/A | MongoDB database instance. |
| `battery_id` | String (e.g. `"BAT-101"`) | N/A | Primary unique asset tracking identifier. |
| `sec` | Float ($\ge 0.0$) | Seconds ($s$) | Elapsed measurement test time. |
| `v` | Float ($\ge 0.0$) | Volts ($V$) | Cell terminal voltage. |
| `i` | Float | Amperes ($A$) | Current flowing through cell (positive: discharge, negative: charge). |
| `t` | Float | Celsius ($^\circ C$) | Physical cell surface temperature. |
| `event` | String (`"RUNNING"`, etc.) | N/A | Telemetry test phase state. |
| `soh` | Float ($0.0 \text{ to } 100.0$) | Percentage ($\%$) | State of Health relative to nominal rated capacity. |
| `available_capacity_ah`| Float ($> 0.0$) | Ampere-hours ($Ah$) | Estimated remaining extractable charge capacity. |
| `safety_status` | Enum | N/A | Diagnostic safety condition: `PASSED`, `WARNING`, `FAILED`, `UNKNOWN`. |
| `confidence` | Float ($0.0 \text{ to } 100.0$) | Percentage ($\%$) | Confidence score in assessment based on data quality. |
| `decision` | Enum | N/A | Gated circularity routing state. |
| `mode` | Enum | N/A | Data source provenance: `LIVE`, `REPLAY`, `VIRTUAL`, `DATASET`. |
| `integrity_hash` | String (64-char Hex) | SHA-256 | Canonical JSON hash for Digital Battery Passport verification. |
| `technician_id` | String (e.g. `"TECH-409"`) | N/A | Certified inspector identifier. |
| `pack_id` | String (e.g. `"PACK-4S-01"`)| N/A | Identifier for grouped 4-cell second-life assembly. |

---

## 2. Canonical Enumeration Sets

### Safety Status (`safety_status`)
1. `PASSED`: Electrical, thermal, and impedance readings within nominal safety envelopes.
2. `WARNING`: Elevated temperature slope, moderate voltage imbalance, or suspicious impedance.
3. `FAILED`: Thermal threshold violation, severe internal short indicators, or mechanical drop.
4. `UNKNOWN`: Incomplete telemetry, sensor fault, or missing readings. *(Must never be treated as PASSED)*.

### Decision States (`decision`)
1. `CONTINUE_EV`: Eligible for continued use in original or secondary light-EV application ($SOH \ge 80\%$, safety `PASSED`).
2. `SECOND_LIFE_STORAGE`: Eligible for stationary energy storage / BESS repurposing ($60\% \le SOH < 80\%$, safety `PASSED`).
3. `FURTHER_TESTING`: Inconclusive data or low confidence ($<60\%$); requires longer bench testing.
4. `QUARANTINE`: Suspicious safety anomaly or `WARNING` status; requires specialist physical inspection.
5. `RECYCLE`: Irreversible degradation ($SOH < 60\%$) or `FAILED` safety status; routed to material recovery.

### Data Acquisition Modes (`mode`)
1. `LIVE`: Real-time streaming from physical ESP32/INA226 bench sensor.
2. `REPLAY`: Real-time playback of pre-recorded physical bench test cycles.
3. `VIRTUAL`: Mathematically simulated battery profile with synthetic noise.
4. `DATASET`: Ingestion from validated experimental laboratory datasets `[PENDING APPROVAL]`.

