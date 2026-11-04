"""REVOLT Member 3 — Assessment Engine.

Module: backend/ai/assessment.py
Author: Member 3 (AI, Assessment, Confidence, Safety and MBCO)

Responsibilities:
- Ingest and validate sensor telemetry from ESP32 or test logs.
- Detect missing, corrupted, negative, duplicate, or non-monotonic readings.
- Extract basic statistical features (voltage, current, temperature, duration).
- Extract pulse-response features (CALCE / REVOLT protocol) when test sequence supports it.
- Never invent missing values. Missing features must remain None.
- Enforce research constraint: NASA full-discharge XGBoost model cannot be fed
  short-duration ESP32 pulse readings. Return 'not_available_for_this_protocol'.
- Ensure all outputs are strictly JSON-serializable (native Python types).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union


def _to_python_type(val: Any) -> Any:
    """Recursively convert NumPy scalars/arrays to native Python types."""
    if val is None:
        return None
    if isinstance(val, (bool, str)):
        return val
    if hasattr(val, "item"):
        try:
            val = val.item()
        except Exception:
            pass
    if isinstance(val, (int,)):
        return int(val)
    if isinstance(val, (float,)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, dict):
        return {k: _to_python_type(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_to_python_type(v) for v in val]
    return val


def _extract_reading_fields(raw: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], str, Optional[str]]:
    """Extract (sec, voltage, current, temperature, event, battery_id) from telemetry dict.

    Supports aliases:
      - sec: 'sec', 'timestamp', 'time', 't_sec'
      - voltage: 'v', 'voltage', 'volts'
      - current: 'i', 'current', 'amps'
      - temperature: 't', 'temp', 'temperature'
      - event: 'event', 'phase', 'state'
      - battery_id: 'battery_id', 'cell_id', 'id'
    """
    sec = None
    for k in ("sec", "timestamp", "time", "t_sec"):
        if k in raw and raw[k] is not None:
            try:
                sec = float(raw[k])
                break
            except (ValueError, TypeError):
                pass

    v = None
    for k in ("v", "voltage", "volts"):
        if k in raw and raw[k] is not None:
            try:
                v = float(raw[k])
                break
            except (ValueError, TypeError):
                pass

    i = None
    for k in ("i", "current", "amps"):
        if k in raw and raw[k] is not None:
            try:
                i = float(raw[k])
                break
            except (ValueError, TypeError):
                pass

    t = None
    for k in ("t", "temp", "temperature"):
        if k in raw and raw[k] is not None:
            try:
                t = float(raw[k])
                break
            except (ValueError, TypeError):
                pass

    event = "RUNNING"
    for k in ("event", "phase", "state"):
        if k in raw and raw[k] is not None:
            event = str(raw[k]).strip().upper()
            break

    battery_id = None
    for k in ("battery_id", "cell_id", "id"):
        if k in raw and raw[k] is not None:
            battery_id = str(raw[k]).strip()
            break

    return sec, v, i, t, event, battery_id


def validate_readings(
    readings: Any,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Validate sensor telemetry list or DataFrame.

    Checks:
    - Empty readings detection.
    - Missing required fields (sec, v, i, t).
    - Non-numeric or NaN/Inf values.
    - Physical bounds:
      * Voltage: 0.0 < v <= 6.0 V (single-cell Li-ion physical bounds).
      * Temperature: -40.0 <= t <= 100.0 °C.
      * Timestamp: sec >= 0.0.
    - Duplicate timestamps detection.
    - Non-monotonic timestamps detection.

    Returns:
        (valid_readings, quality_summary)
    """
    quality: Dict[str, Any] = {
        "status": "PASSED",
        "total_readings": 0,
        "valid_readings": 0,
        "missing_readings": 0,
        "invalid_readings": 0,
        "duplicate_timestamps": 0,
        "non_monotonic_timestamps": 0,
        "errors": [],
        "warnings": [],
        "battery_id": None,
    }

    if readings is None:
        quality["status"] = "EMPTY"
        quality["errors"].append("Readings input is None.")
        return [], quality

    # Convert pandas DataFrame to list of dicts if provided
    if hasattr(readings, "to_dict"):
        try:
            readings = readings.to_dict(orient="records")
        except Exception as ex:
            quality["status"] = "INVALID"
            quality["errors"].append(f"Failed to convert DataFrame to records: {ex}")
            return [], quality

    if not isinstance(readings, (list, tuple)):
        quality["status"] = "INVALID"
        quality["errors"].append(f"Expected list of telemetry dicts, got {type(readings).__name__}.")
        return [], quality

    total = len(readings)
    quality["total_readings"] = total

    if total == 0:
        quality["status"] = "EMPTY"
        quality["warnings"].append("Telemetry reading sequence is empty.")
        return [], quality

    valid_list: List[Dict[str, Any]] = []
    seen_timestamps = set()
    prev_time = -1.0

    for idx, raw in enumerate(readings):
        if not isinstance(raw, dict):
            quality["invalid_readings"] += 1
            quality["errors"].append(f"Record {idx}: not a dictionary.")
            continue

        sec, v, i, t, event, b_id = _extract_reading_fields(raw)

        if quality["battery_id"] is None and b_id:
            quality["battery_id"] = b_id

        # Missing values check
        missing_fields = []
        if sec is None:
            missing_fields.append("sec")
        if v is None:
            missing_fields.append("v")
        if i is None:
            missing_fields.append("i")
        if t is None:
            missing_fields.append("t")

        if missing_fields:
            quality["missing_readings"] += 1
            quality["errors"].append(
                f"Record {idx}: Missing field(s): {', '.join(missing_fields)}."
            )
            continue

        # Physical sanity checks
        invalid_reasons = []
        if math.isnan(sec) or math.isinf(sec) or sec < 0:
            invalid_reasons.append(f"Invalid timestamp sec={sec}")

        if math.isnan(v) or math.isinf(v):
            invalid_reasons.append("Voltage is NaN or Inf")
        elif v <= 0.0:
            invalid_reasons.append(f"Non-positive voltage v={v} V (possible sensor fault / reverse polarity)")
        elif v > 6.0:
            invalid_reasons.append(f"Voltage v={v} V exceeds single-cell ceiling (6.0 V)")

        if math.isnan(i) or math.isinf(i):
            invalid_reasons.append("Current is NaN or Inf")

        if math.isnan(t) or math.isinf(t):
            invalid_reasons.append("Temperature is NaN or Inf")
        elif t < -40.0 or t > 100.0:
            invalid_reasons.append(f"Temperature t={t} °C outside physical operating range (-40 to 100 °C)")

        if invalid_reasons:
            quality["invalid_readings"] += 1
            quality["errors"].append(f"Record {idx}: {'; '.join(invalid_reasons)}.")
            continue

        # Check duplicate timestamp
        rounded_sec = round(sec, 4)
        if rounded_sec in seen_timestamps:
            quality["duplicate_timestamps"] += 1
            quality["warnings"].append(f"Record {idx}: Duplicate timestamp sec={sec} detected.")
        else:
            seen_timestamps.add(rounded_sec)

        # Check monotonicity
        if prev_time >= 0 and sec < prev_time:
            quality["non_monotonic_timestamps"] += 1
            quality["warnings"].append(
                f"Record {idx}: Non-monotonic timestamp (prev={prev_time}, current={sec})."
            )
        prev_time = sec

        valid_list.append({
            "sec": float(sec),
            "v": float(v),
            "i": float(i),
            "t": float(t),
            "event": event,
            "battery_id": b_id or quality["battery_id"] or "UNKNOWN",
        })

    quality["valid_readings"] = len(valid_list)

    # Determine overall data quality status
    if quality["valid_readings"] == 0:
        quality["status"] = "INVALID"
    elif quality["invalid_readings"] > 0 or quality["missing_readings"] > 0 or quality["duplicate_timestamps"] > 0:
        quality["status"] = "DEGRADED"
    else:
        quality["status"] = "PASSED"

    return valid_list, quality


def compute_basic_statistics(valid_readings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Compute basic statistical summary features from validated readings."""
    if not valid_readings:
        return None

    n = len(valid_readings)
    voltages = [r["v"] for r in valid_readings]
    currents = [r["i"] for r in valid_readings]
    temps = [r["t"] for r in valid_readings]
    times = [r["sec"] for r in valid_readings]

    def _mean_std_min_max(arr: List[float]) -> Tuple[float, float, float, float]:
        mean_val = sum(arr) / len(arr)
        if len(arr) > 1:
            variance = sum((x - mean_val) ** 2 for x in arr) / (len(arr) - 1)
            std_val = math.sqrt(max(0.0, variance))
        else:
            std_val = 0.0
        return mean_val, std_val, min(arr), max(arr)

    v_mean, v_std, v_min, v_max = _mean_std_min_max(voltages)
    i_mean, i_std, i_min, i_max = _mean_std_min_max(currents)
    t_mean, t_std, t_min, t_max = _mean_std_min_max(temps)

    duration_s = max(0.0, max(times) - min(times))
    t_change = temps[-1] - temps[0]

    return {
        "sample_count": n,
        "duration_s": round(duration_s, 3),
        "voltage_mean": round(v_mean, 5),
        "voltage_std": round(v_std, 5),
        "voltage_min": round(v_min, 5),
        "voltage_max": round(v_max, 5),
        "current_mean": round(i_mean, 5),
        "current_std": round(i_std, 5),
        "current_min": round(i_min, 5),
        "current_max": round(i_max, 5),
        "temperature_mean": round(t_mean, 3),
        "temperature_std": round(t_std, 3),
        "temperature_min": round(t_min, 3),
        "temperature_max": round(t_max, 3),
        "temperature_change_c": round(t_change, 3),
    }


def extract_pulse_features(
    valid_readings: List[Dict[str, Any]],
    rated_capacity_ah: float = 2.5,
) -> Tuple[Dict[str, Any], List[str], Dict[str, bool]]:
    """Extract pulse-response features matching CALCE / REVOLT protocol.

    Identifies rest, 0.5C pulse, 1C pulse, and recovery phases.
    Missing features are retained as None. Never fabricated.
    Apparent resistance is documented as apparent pulse resistance,
    not electrochemical impedance spectroscopy.

    Returns:
        (pulse_features, available_feature_names, availability_indicators)
    """
    features: Dict[str, Any] = {
        "rest_voltage_v": None,
        "rest_current_a": None,
        "pulse_05c_voltage_mean_v": None,
        "pulse_05c_voltage_min_v": None,
        "pulse_05c_voltage_last_v": None,
        "pulse_05c_current_mean_a": None,
        "pulse_05c_voltage_drop_v": None,
        "pulse_05c_resistance_est_ohm": None,
        "pulse_05c_duration_est_s": None,
        "pulse_05c_voltage_slope_v_per_s": None,
        "pulse_1c_voltage_mean_v": None,
        "pulse_1c_voltage_min_v": None,
        "pulse_1c_voltage_last_v": None,
        "pulse_1c_current_mean_a": None,
        "pulse_1c_voltage_drop_v": None,
        "pulse_1c_resistance_est_ohm": None,
        "pulse_1c_duration_est_s": None,
        "pulse_1c_voltage_slope_v_per_s": None,
        "temperature_mean_c": None,
        "temperature_max_c": None,
        "temperature_change_c": None,
        "recovery_voltage_v": None,
        "recovery_voltage_change_v": None,
        "recovery_duration_s": None,
        "complete_pulse_sequence": False,
        "pulse_quality": "insufficient",
    }

    if not valid_readings or rated_capacity_ah <= 0:
        return features, [], {k: False for k in features}

    # Group readings by event or current profile
    rest_samples: List[Dict[str, Any]] = []
    pulse_05c_samples: List[Dict[str, Any]] = []
    pulse_1c_samples: List[Dict[str, Any]] = []
    recovery_samples: List[Dict[str, Any]] = []

    # Thresholds for classification:
    # 0.5C nominal current = -0.5 * rated_capacity_ah (discharge is negative or load)
    c_05 = 0.5 * rated_capacity_ah
    c_1 = 1.0 * rated_capacity_ah

    for r in valid_readings:
        event = r.get("event", "").upper()
        i = r["i"]

        # Classification precedence: explicit event tag > current threshold
        if "REST" in event:
            rest_samples.append(r)
        elif "0.5C" in event or "05C" in event or "HALF" in event:
            pulse_05c_samples.append(r)
        elif "1C" in event or "ONE" in event:
            pulse_1c_samples.append(r)
        elif "RECOVERY" in event:
            recovery_samples.append(r)
        else:
            # Current-based detection
            if abs(i) <= 0.05 * rated_capacity_ah or abs(i) < 0.05:
                # If pulse has not occurred yet, treat as rest; if pulse already occurred, recovery
                if not pulse_05c_samples and not pulse_1c_samples:
                    rest_samples.append(r)
                else:
                    recovery_samples.append(r)
            elif (0.25 * c_05) <= abs(i) <= (1.35 * c_05):
                pulse_05c_samples.append(r)
            elif (0.75 * c_1) <= abs(i) <= (1.45 * c_1):
                pulse_1c_samples.append(r)

    # 1. Rest Phase Features
    if rest_samples:
        v_rest = sum(s["v"] for s in rest_samples) / len(rest_samples)
        i_rest = sum(s["i"] for s in rest_samples) / len(rest_samples)
        features["rest_voltage_v"] = round(v_rest, 5)
        features["rest_current_a"] = round(i_rest, 5)

    # Helper for pulse statistics
    def _process_pulse(samples: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
        if not samples:
            return None, None, None, None, None, None
        v_list = [s["v"] for s in samples]
        i_list = [s["i"] for s in samples]
        t_list = [s["sec"] for s in samples]
        v_mean = sum(v_list) / len(v_list)
        v_min = min(v_list)
        v_last = v_list[-1]
        i_mean = sum(i_list) / len(i_list)
        dur = max(0.0, t_list[-1] - t_list[0]) if len(t_list) > 1 else 0.0

        if len(t_list) > 1 and dur > 0:
            slope = (v_last - v_list[0]) / dur
        else:
            slope = 0.0

        return v_mean, v_min, v_last, i_mean, dur, slope

    # 2. 0.5C Pulse Features
    if pulse_05c_samples:
        v_m, v_min, v_last, i_m, dur, slope = _process_pulse(pulse_05c_samples)
        features["pulse_05c_voltage_mean_v"] = round(v_m, 5) if v_m is not None else None
        features["pulse_05c_voltage_min_v"] = round(v_min, 5) if v_min is not None else None
        features["pulse_05c_voltage_last_v"] = round(v_last, 5) if v_last is not None else None
        features["pulse_05c_current_mean_a"] = round(i_m, 5) if i_m is not None else None
        features["pulse_05c_duration_est_s"] = round(dur, 3) if dur is not None else None
        features["pulse_05c_voltage_slope_v_per_s"] = round(slope, 6) if slope is not None else None

        if features["rest_voltage_v"] is not None and v_m is not None:
            drop = features["rest_voltage_v"] - v_m
            features["pulse_05c_voltage_drop_v"] = round(drop, 5)
            if i_m is not None and abs(i_m) > 1e-4:
                # Apparent pulse resistance in Ohms
                features["pulse_05c_resistance_est_ohm"] = round(abs(drop / i_m), 6)

    # 3. 1C Pulse Features
    if pulse_1c_samples:
        v_m, v_min, v_last, i_m, dur, slope = _process_pulse(pulse_1c_samples)
        features["pulse_1c_voltage_mean_v"] = round(v_m, 5) if v_m is not None else None
        features["pulse_1c_voltage_min_v"] = round(v_min, 5) if v_min is not None else None
        features["pulse_1c_voltage_last_v"] = round(v_last, 5) if v_last is not None else None
        features["pulse_1c_current_mean_a"] = round(i_m, 5) if i_m is not None else None
        features["pulse_1c_duration_est_s"] = round(dur, 3) if dur is not None else None
        features["pulse_1c_voltage_slope_v_per_s"] = round(slope, 6) if slope is not None else None

        if features["rest_voltage_v"] is not None and v_m is not None:
            drop = features["rest_voltage_v"] - v_m
            features["pulse_1c_voltage_drop_v"] = round(drop, 5)
            if i_m is not None and abs(i_m) > 1e-4:
                features["pulse_1c_resistance_est_ohm"] = round(abs(drop / i_m), 6)

    # 4. Temperature Features during sequence
    all_temps = [r["t"] for r in valid_readings]
    if all_temps:
        features["temperature_mean_c"] = round(sum(all_temps) / len(all_temps), 3)
        features["temperature_max_c"] = round(max(all_temps), 3)
        features["temperature_change_c"] = round(all_temps[-1] - all_temps[0], 3)

    # 5. Recovery Phase Features
    if recovery_samples:
        v_rec_list = [s["v"] for s in recovery_samples]
        t_rec_list = [s["sec"] for s in recovery_samples]
        v_rec_mean = sum(v_rec_list) / len(v_rec_list)
        features["recovery_voltage_v"] = round(v_rec_mean, 5)
        features["recovery_voltage_change_v"] = round(v_rec_list[-1] - v_rec_list[0], 5)
        features["recovery_duration_s"] = round(max(0.0, t_rec_list[-1] - t_rec_list[0]), 3)

    # 6. Completeness evaluation
    has_rest = features["rest_voltage_v"] is not None
    has_05c = features["pulse_05c_voltage_mean_v"] is not None
    has_1c = features["pulse_1c_voltage_mean_v"] is not None

    if has_rest and has_05c and has_1c:
        features["complete_pulse_sequence"] = True
        features["pulse_quality"] = "complete"
    elif has_05c or has_1c:
        features["complete_pulse_sequence"] = False
        features["pulse_quality"] = "partial"
    else:
        features["complete_pulse_sequence"] = False
        features["pulse_quality"] = "insufficient"

    available_keys = [k for k, v in features.items() if v is not None and k not in ("complete_pulse_sequence", "pulse_quality")]
    indicators = {k: (v is not None) for k, v in features.items()}

    return features, available_keys, indicators


def assess_telemetry(
    readings: Any,
    chemistry: str = "NMC",
    rated_capacity_ah: float = 2.5,
    nominal_voltage_v: float = 3.7,
) -> Dict[str, Any]:
    """Ingest, validate, and extract features from battery telemetry.

    Adheres strictly to research constraints:
    - Incompatible short ESP32 pulse readings return SOH status 'not_available_for_this_protocol'.
    - Missing measurements remain None (never fabricated).
    - Output is clean, structured, and strictly JSON-serializable.
    """
    valid_readings, quality = validate_readings(readings)

    basic_stats = compute_basic_statistics(valid_readings) if valid_readings else None
    pulse_feats, available_pulse_feats, pulse_indicators = extract_pulse_features(
        valid_readings, rated_capacity_ah=rated_capacity_ah
    )

    # SOH Status & Remaining Capacity Determination
    # Research constraint: NASA XGBoost requires full discharge cycles (~3000s, ~2A CC).
    # ESP32 short pulse readings are protocol-incompatible.
    is_full_discharge = False
    if basic_stats is not None:
        dur = basic_stats.get("duration_s", 0.0)
        curr_mean = basic_stats.get("current_mean", 0.0)
        # NASA discharge is ~3000s continuous negative discharge
        if dur >= 2000.0 and curr_mean < -0.5:
            is_full_discharge = True

    if is_full_discharge:
        soh_status = "model_compatible_full_discharge"
        soh_pct = None  # Handled in engine if offline NASA benchmark invoked
        rem_ah = None
        soh_message = "Full discharge cycle profile detected. Compatible with NASA offline research benchmark."
    else:
        soh_status = "not_available_for_this_protocol"
        soh_pct = None
        rem_ah = None
        soh_message = (
            "NASA XGBoost model was trained on full discharge cycles. ESP32 pulse / short-duration "
            "readings are protocol-incompatible. Direct SOH prediction withheld to prevent invalid inference."
        )

    out = {
        "battery_id": quality.get("battery_id") or "UNKNOWN",
        "chemistry": str(chemistry).upper(),
        "rated_capacity_ah": float(rated_capacity_ah),
        "nominal_voltage_v": float(nominal_voltage_v),
        "data_quality": quality,
        "extracted_features": {
            "basic_stats": basic_stats,
            "pulse_features": pulse_feats,
        },
        "available_pulse_features": available_pulse_feats,
        "feature_availability_indicators": pulse_indicators,
        "soh_assessment": {
            "status": soh_status,
            "soh_pct": soh_pct,
            "remaining_capacity_ah": rem_ah,
            "message": soh_message,
        },
    }

    return _to_python_type(out)


def evaluate_battery(
    readings: Any,
    chemistry: str = "NMC",
    rated_capacity_ah: float = 2.5,
) -> Dict[str, Any]:
    """Module 1 evaluation entrypoint as specified in instructions."""
    return assess_telemetry(readings, chemistry=chemistry, rated_capacity_ah=rated_capacity_ah)
