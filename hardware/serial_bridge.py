import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Tuple

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SerialBridge")


def scan_esp32_port() -> Optional[str]:
    """Scans system serial ports for typical ESP32 / USB-to-UART bridge controllers."""
    if serial is None:
        return None

    known_keywords = ["cp210", "ch340", "ftdi", "usb serial", "uart", "esp32"]
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = (port.description or "").lower()
        hwid = (port.hwid or "").lower()
        for kw in known_keywords:
            if kw in desc or kw in hwid:
                logger.info(f"Detected potential ESP32 hardware on {port.device}: {port.description}")
                return port.device
    return None


def parse_telemetry_line(raw_line: str) -> Optional[dict]:
    """Parses a serial ASCII line into a validated telemetry packet dictionary."""
    if not raw_line or not raw_line.strip():
        return None

    line = raw_line.strip()
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    required_keys = ["battery_id", "sec", "v", "i", "t", "event"]
    for k in required_keys:
        if k not in data:
            return None

    try:
        return {
            "battery_id": str(data["battery_id"]),
            "sec": float(data["sec"]),
            "v": float(data["v"]),
            "i": float(data["i"]),
            "t": float(data["t"]),
            "event": str(data["event"]),
        }
    except (ValueError, TypeError):
        return None


def post_telemetry(
    packet: dict,
    endpoint_url: str = "http://127.0.0.1:8000/api/live-data",
    mode: str = "LIVE"
) -> Tuple[bool, Optional[dict]]:
    """Transmits a telemetry packet to the ReVolt backend API gateway."""
    payload_bytes = json.dumps(packet).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Data-Mode": mode
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                body = json.loads(response.read().decode("utf-8"))
                return True, body
            return False, None
    except Exception as e:
        logger.error(f"Failed to post telemetry to {endpoint_url}: {e}")
        return False, None


def run_bridge(port: Optional[str] = None, baudrate: int = 115200, max_packets: Optional[int] = None) -> str:
    """Connects to ESP32 serial port and streams live telemetry to backend."""
    selected_port = port or scan_esp32_port()
    if not selected_port:
        logger.warning("No physical ESP32 / USB-UART hardware port detected.")
        return "BLOCKED_NO_PORT"

    try:
        with serial.Serial(selected_port, baudrate, timeout=1.0) as ser:
            logger.info(f"Connected to ESP32 on {selected_port} at {baudrate} baud.")
            packets_processed = 0
            while True:
                line = ser.readline().decode("utf-8", errors="ignore")
                packet = parse_telemetry_line(line)
                if packet:
                    success, ack = post_telemetry(packet, mode="LIVE")
                    if success:
                        packets_processed += 1
                        logger.info(f"Ingested live packet #{packets_processed}: {ack}")
                if max_packets and packets_processed >= max_packets:
                    break
            return "SUCCESS"
    except Exception as e:
        logger.error(f"Serial communication error on {selected_port}: {e}")
        return f"ERROR: {e}"

