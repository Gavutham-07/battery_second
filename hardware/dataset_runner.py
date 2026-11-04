import json
import os
import time
import urllib.request
from typing import List, Tuple, Optional


def load_dataset_file(file_path: str) -> List[dict]:
    """Loads standardized dataset benchmark telemetry from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset benchmark file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    packets = []
    for item in data:
        packets.append({
            "battery_id": str(item["battery_id"]),
            "sec": float(item["sec"]),
            "v": float(item["v"]),
            "i": float(item["i"]),
            "t": float(item["t"]),
            "event": str(item.get("event", "DATASET_STREAM"))
        })
    return packets


def run_dataset_stream(
    file_path: str,
    endpoint_url: str = "http://127.0.0.1:8000/api/live-data",
    interval_sec: float = 0.0,
    max_packets: Optional[int] = None
) -> Tuple[int, int]:
    """Streams validated dataset benchmark telemetry tagged with mode=DATASET."""
    packets = load_dataset_file(file_path)
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
                "X-Data-Mode": "DATASET"
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

