import csv
import json
import os
import time
import urllib.request
from typing import List, Tuple, Optional


def load_replay_data(file_path: str) -> List[dict]:
    """Loads recorded bench test telemetry from a CSV or JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Replay data file not found: {file_path}")

    packets = []
    if file_path.endswith(".csv"):
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                packets.append({
                    "battery_id": str(row["battery_id"]),
                    "sec": float(row["sec"]),
                    "v": float(row["v"]),
                    "i": float(row["i"]),
                    "t": float(row["t"]),
                    "event": str(row["event"])
                })
    elif file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            for item in raw:
                packets.append({
                    "battery_id": str(item["battery_id"]),
                    "sec": float(item["sec"]),
                    "v": float(item["v"]),
                    "i": float(item["i"]),
                    "t": float(item["t"]),
                    "event": str(item["event"])
                })
    return packets


def run_replay(
    file_path: str,
    endpoint_url: str = "http://127.0.0.1:8000/api/live-data",
    interval_sec: float = 0.0,
    max_packets: Optional[int] = None
) -> Tuple[int, int]:
    """Streams recorded telemetry packets to the backend tagged with mode=REPLAY."""
    packets = load_replay_data(file_path)
    if max_packets:
        packets = packets[:max_packets]

    sent = 0
    acknowledged = 0

    for p in packets:
        payload = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(
            endpoint_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Data-Mode": "REPLAY"
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

