import json
import math
import time
import urllib.request
from typing import List, Tuple, Optional


def simulate_ocv(soc: float, chemistry: str = "LFP") -> float:
    """Computes Open-Circuit Voltage (OCV) as a function of State of Charge (0.0 to 1.0)."""
    soc = max(0.0, min(1.0, soc))
    if chemistry.upper() == "LFP":
        # Flat plateau characteristic of LiFePO4 cells (3.2V nominal, 2.5V-3.65V envelope)
        if soc > 0.95:
            return 3.35 + (soc - 0.95) * 6.0
        elif soc < 0.10:
            return 2.50 + soc * 7.0
        else:
            return 3.20 + (soc - 0.10) * (0.15 / 0.85)
    else:
        # Linear slope typical of NMC / NCA cells (3.7V nominal, 3.0V-4.2V envelope)
        return 3.00 + soc * 1.20


def generate_virtual_cycle(
    battery_id: str = "BAT-VIRTUAL-01",
    chemistry: str = "LFP",
    duration_sec: int = 20,
    step_sec: float = 1.0,
    current_a: float = 0.5,
    ambient_temp_c: float = 26.0,
    internal_resistance: float = 0.040
) -> List[dict]:
    """Generates a physically realistic virtual time-series test cycle."""
    packets = []
    nominal_capacity_as = 2.5 * 3600.0  # 2.5 Ah in Ampere-seconds
    charge_remaining_as = nominal_capacity_as * 0.90  # start at 90% SOC
    temp_c = ambient_temp_c

    for step in range(int(duration_sec / step_sec)):
        elapsed_sec = round(step * step_sec, 2)
        soc = charge_remaining_as / nominal_capacity_as
        ocv = simulate_ocv(soc, chemistry)

        # Terminal voltage: V = OCV - I * R_int
        i_actual = current_a if soc > 0.05 else 0.0
        v_terminal = round(max(2.0, ocv - (i_actual * internal_resistance)), 4)

        # Thermal dissipation: dT = (I^2 * R - heat_loss) / C_th
        joule_heat = (i_actual ** 2) * internal_resistance * 0.08
        cooling = (temp_c - ambient_temp_c) * 0.02
        temp_c = round(temp_c + (joule_heat - cooling) * step_sec, 2)

        # Coulomb depletion
        charge_remaining_as = max(0.0, charge_remaining_as - (i_actual * step_sec))

        event = "DISCHARGE" if i_actual > 0 else "STOP"

        packets.append({
            "battery_id": battery_id,
            "sec": float(elapsed_sec),
            "v": float(v_terminal),
            "i": float(round(i_actual, 3)),
            "t": float(temp_c),
            "event": event
        })

    return packets


def run_virtual_stream(
    battery_id: str = "BAT-VIRTUAL-01",
    endpoint_url: str = "http://127.0.0.1:8000/api/live-data",
    count: int = 15,
    interval_sec: float = 0.0
) -> Tuple[int, int]:
    """Generates virtual battery measurements and streams them with mode=VIRTUAL."""
    packets = generate_virtual_cycle(battery_id=battery_id, duration_sec=count, step_sec=1.0)
    sent = 0
    acknowledged = 0

    for p in packets:
        payload = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(
            endpoint_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Data-Mode": "VIRTUAL"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    acknowledged += 1
            sent += 1
        except Exception:
            sent += 1

        if interval_sec > 0:
            time.sleep(interval_sec)

    return sent, acknowledged

