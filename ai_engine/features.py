from typing import List, Dict, Any
import statistics


def extract_features(telemetry: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts electrical, thermal, and operational features from a chronologically
    sorted series of telemetry packets.
    """
    if not telemetry or len(telemetry) < 2:
        return {
            "sample_count": len(telemetry) if telemetry else 0,
            "duration_sec": 0.0,
            "v_initial": None,
            "v_min": None,
            "v_max": None,
            "v_final": None,
            "i_mean": 0.0,
            "i_max": 0.0,
            "t_initial": None,
            "t_max": None,
            "t_delta": 0.0,
            "t_rate_max": 0.0,
            "coulomb_ah": 0.0,
            "dv_dt": 0.0,
            "estimated_ir_ohm": 0.040,
            "missing_intervals": 0,
            "thermal_variance": 0.0,
        }

    sample_count = len(telemetry)
    secs = [float(p["sec"]) for p in telemetry]
    volts = [float(p["v"]) for p in telemetry]
    currents = [float(p["i"]) for p in telemetry]
    temps = [float(p["t"]) for p in telemetry]

    duration_sec = max(secs) - min(secs)
    v_initial = volts[0]
    v_final = volts[-1]
    v_min = min(volts)
    v_max = max(volts)

    i_mean = statistics.mean(currents)
    i_max = max(currents)

    t_initial = temps[0]
    t_max = max(temps)
    t_delta = round(t_max - t_initial, 2)
    thermal_variance = round(statistics.variance(temps), 4) if len(temps) > 1 else 0.0

    # Calculate max thermal rate (dT/dt)
    t_rates = []
    for i in range(1, len(telemetry)):
        dt = secs[i] - secs[i - 1]
        if dt > 0.001:
            rate = abs(temps[i] - temps[i - 1]) / dt
            t_rates.append(rate)
    t_rate_max = round(max(t_rates), 4) if t_rates else 0.0

    # Coulomb counting integration: sum(I * dt) / 3600
    coulomb_as = 0.0
    for i in range(1, len(telemetry)):
        dt = secs[i] - secs[i - 1]
        if dt > 0:
            avg_i = (currents[i] + currents[i - 1]) / 2.0
            if avg_i > 0:  # discharge current
                coulomb_as += avg_i * dt
    coulomb_ah = round(coulomb_as / 3600.0, 4)

    # Voltage slope during discharge
    dv = v_final - v_initial
    dv_dt = round(dv / duration_sec, 6) if duration_sec > 0 else 0.0

    # Internal resistance estimation on initial load step
    estimated_ir = 0.040
    for i in range(1, min(5, len(telemetry))):
        di = abs(currents[i] - currents[0])
        dv_step = abs(volts[0] - volts[i])
        if di > 0.1:
            estimated_ir = round(dv_step / di, 4)
            break

    # Detect abnormal sampling gaps (> 2.5x median dt)
    intervals = [secs[i] - secs[i - 1] for i in range(1, len(secs)) if secs[i] > secs[i - 1]]
    missing_intervals = 0
    if len(intervals) >= 3:
        med_dt = statistics.median(intervals)
        for dt in intervals:
            if dt > 2.5 * med_dt and med_dt > 0:
                missing_intervals += 1

    return {
        "sample_count": sample_count,
        "duration_sec": round(duration_sec, 2),
        "v_initial": v_initial,
        "v_min": v_min,
        "v_max": v_max,
        "v_final": v_final,
        "i_mean": round(i_mean, 3),
        "i_max": round(i_max, 3),
        "t_initial": t_initial,
        "t_max": t_max,
        "t_delta": t_delta,
        "t_rate_max": t_rate_max,
        "coulomb_ah": coulomb_ah,
        "dv_dt": dv_dt,
        "estimated_ir_ohm": estimated_ir,
        "missing_intervals": missing_intervals,
        "thermal_variance": thermal_variance,
    }

