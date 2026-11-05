import mongomock, pymongo
pymongo.MongoClient = mongomock.MongoClient

# Member B test mock for hardware.pulse_stream (until hardware member completes B2)
import sys
import types
import math
import random

PROFILES = {
    "healthy": {
        "chemistry": "NMC",
        "source_cell_id": "02LCC02100101A87Y0178524",
        "measured_soh_pct": 97.8,
        "temp_start_c": 28.0,
        "temp_rise_c": 0.6,
        "u_points_v": [3.6879, 3.7072, 3.717, 3.6979, 3.69, 3.6707, 3.6605, 3.68,
                       3.6886, 3.7277, 3.7472, 3.7084, 3.6912, 3.6519, 3.6324, 3.6717, 3.6881]
    },
    "moderately_aged": {
        "chemistry": "NMC",
        "source_cell_id": "02LCC02100101A8BC0104122",
        "measured_soh_pct": 74.6,
        "temp_start_c": 28.0,
        "temp_rise_c": 1.4,
        "u_points_v": [3.8482, 3.8766, 3.8898, 3.8617, 3.8522, 3.8236, 3.8101, 3.8387,
                       3.8492, 3.9066, 3.9326, 3.8759, 3.8541, 3.7964, 3.7699, 3.8278, 3.8478]
    },
    "end_of_life": {
        "chemistry": "LMO",
        "source_cell_id": "PIP15829A00218550",
        "measured_soh_pct": 55.4,
        "temp_start_c": 28.0,
        "temp_rise_c": 2.0,
        "u_points_v": [3.9986, 4.0329, 4.1361, 4.1026, 4.0047, 3.9718, 3.8879, 3.9219,
                       4.0025, 4.0721, 4.2515, 4.1853, 4.0093, 3.941, 3.8085, 3.8757, 4.0029]
    },
    "thermally_unsafe": {
        "chemistry": "NMC",
        "source_cell_id": "02LCC02100101A87Y0178524",
        "measured_soh_pct": 97.8,
        "temp_start_c": 28.0,
        "temp_rise_c": 35.5,
        "u_points_v": [3.6879, 3.7072, 3.717, 3.6979, 3.69, 3.6707, 3.6605, 3.68,
                       3.6886, 3.7277, 3.7472, 3.7084, 3.6912, 3.6519, 3.6324, 3.6717, 3.6881]
    }
}

def load_profile(name):
    key = str(name).lower()
    if key not in PROFILES:
        raise KeyError(f"Invalid profile name '{name}'. Valid profiles: {list(PROFILES.keys())}")
    return PROFILES[key]

def source_note(profile_name, mode):
    prof = load_profile(profile_name)
    cid = prof["source_cell_id"]
    m = str(mode).upper()
    if m == "DATASET":
        return f"Voltage response from PulseBat cell {cid}; measured at 25 °C"
    elif m == "HYBRID":
        return f"Voltage response from PulseBat cell {cid}; temperature measured live by DS18B20"
    else:
        return f"Voltage response from PulseBat cell {cid}; test sequence and temperature simulated"

def generate_p17_stream(profile_name, battery_id, rated_capacity_ah, mode):
    prof = load_profile(profile_name)
    u = prof["u_points_v"]
    c = float(rated_capacity_ah)
    m = str(mode).upper()

    rng = random.Random(str(battery_id))
    turning_points = {10, 14, 15, 29, 30, 34, 35, 49, 50, 54, 55, 69, 70, 74, 75, 89}

    def _relax(start, end, x):
        denom = 1.0 - math.exp(-4.0)
        return start + (end - start) * (1.0 - math.exp(-4.0 * x)) / denom

    readings = []
    temp_start = prof.get("temp_start_c", 28.0)
    temp_rise = prof.get("temp_rise_c", 0.6)
    is_unsafe = (profile_name.lower() == "thermally_unsafe")

    for sec in range(90):
        # Event & current & base voltage
        if sec <= 9:
            event = "REST"
            curr = 0.0
            v = u[0]
        elif 10 <= sec <= 14:
            event = "PULSE_POS_05C"
            curr = 0.5 * c
            frac = (sec - 10) / 4.0
            v = u[1] + (u[2] - u[1]) * frac
        elif 15 <= sec <= 29:
            event = "RELAX"
            curr = 0.0
            frac = (sec - 15) / 14.0
            v = _relax(u[3], u[4], frac)
        elif 30 <= sec <= 34:
            event = "PULSE_NEG_05C"
            curr = -0.5 * c
            frac = (sec - 30) / 4.0
            v = u[5] + (u[6] - u[5]) * frac
        elif 35 <= sec <= 49:
            event = "RELAX"
            curr = 0.0
            frac = (sec - 35) / 14.0
            v = _relax(u[7], u[8], frac)
        elif 50 <= sec <= 54:
            event = "PULSE_POS_1C"
            curr = 1.0 * c
            frac = (sec - 50) / 4.0
            v = u[9] + (u[10] - u[9]) * frac
        elif 55 <= sec <= 69:
            event = "RELAX"
            curr = 0.0
            frac = (sec - 55) / 14.0
            v = _relax(u[11], u[12], frac)
        elif 70 <= sec <= 74:
            event = "PULSE_NEG_1C"
            curr = -1.0 * c
            frac = (sec - 70) / 4.0
            v = u[13] + (u[14] - u[13]) * frac
        else: # 75 <= sec <= 89
            event = "RELAX"
            curr = 0.0
            frac = (sec - 75) / 14.0
            v = _relax(u[15], u[16], frac)

        # Noise in VIRTUAL and HYBRID
        if m in ("VIRTUAL", "HYBRID"):
            if sec not in turning_points and sec > 9:
                noise = rng.uniform(-0.0015, 0.0015)
                v += noise

        # Temperature
        if m == "DATASET":
            t = 25.0
        elif is_unsafe:
            if sec <= 10:
                t = temp_start
            else:
                t = temp_start + 0.45 * (sec - 10)
        else:
            t = temp_start + temp_rise * ((sec / 89.0) ** 1.5)

        readings.append({
            "battery_id": battery_id,
            "sec": float(sec),
            "v": round(v, 4),
            "i": round(curr, 3),
            "t": round(t, 2),
            "event": event,
            "mode": m,
        })

    return readings

# Register module into sys.modules if hardware.pulse_stream not on disk
try:
    import hardware.pulse_stream
except ImportError:
    mod = types.ModuleType("hardware.pulse_stream")
    mod.PROFILES = PROFILES
    mod.load_profile = load_profile
    mod.source_note = source_note
    mod.generate_p17_stream = generate_p17_stream
    sys.modules["hardware.pulse_stream"] = mod
