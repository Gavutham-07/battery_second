import os
import pytest
from hardware.serial_bridge import parse_telemetry_line, scan_esp32_port, run_bridge
from hardware.replay_runner import load_replay_data
from hardware.virtual_generator import simulate_ocv, generate_virtual_cycle
from hardware.dataset_runner import load_dataset_file


def test_parse_valid_telemetry_line():
    raw_line = '{"battery_id": "BAT-101", "sec": 15.0, "v": 3.842, "i": 0.405, "t": 29.10, "event": "RUNNING"}\r\n'
    packet = parse_telemetry_line(raw_line)
    assert packet is not None
    assert packet["battery_id"] == "BAT-101"
    assert packet["sec"] == 15.0
    assert packet["v"] == 3.842
    assert packet["i"] == 0.405
    assert packet["t"] == 29.10
    assert packet["event"] == "RUNNING"


def test_parse_invalid_telemetry_lines():
    assert parse_telemetry_line("") is None
    assert parse_telemetry_line("NOT_JSON") is None
    # Missing required keys
    assert parse_telemetry_line('{"battery_id": "BAT-101", "v": 3.8}') is None
    # Invalid numeric conversion
    assert parse_telemetry_line('{"battery_id": "BAT-101", "sec": "ABC", "v": 3.8, "i": 0.5, "t": 25.0, "event": "RUNNING"}') is None


def test_scan_esp32_port_behavior():
    # Returns a string if port detected, or None if no hardware attached
    port = scan_esp32_port()
    assert port is None or isinstance(port, str)


def test_run_bridge_no_port():
    # When no port is explicitly available, run_bridge should gracefully report BLOCKED_NO_PORT
    status = run_bridge(port=None)
    assert status in ["BLOCKED_NO_PORT", "SUCCESS"]


def test_load_replay_csv():
    csv_path = os.path.join("hardware", "data", "sample_bench_cycle.csv")
    assert os.path.exists(csv_path)
    packets = load_replay_data(csv_path)
    assert len(packets) >= 20
    assert packets[0]["battery_id"] == "BAT-101"
    assert packets[0]["sec"] == 0.0
    assert packets[-1]["event"] == "STOP"


def test_generate_virtual_cycle():
    packets = generate_virtual_cycle(battery_id="BAT-VIRTUAL-TEST", chemistry="LFP", duration_sec=10, step_sec=1.0)
    assert len(packets) == 10
    # Voltages within physical LFP cell window (2.0V to 3.8V)
    for p in packets:
        assert 2.0 <= p["v"] <= 3.8
        assert p["battery_id"] == "BAT-VIRTUAL-TEST"
        assert p["sec"] >= 0.0
    # Temperature should slightly increase or remain steady under load
    assert packets[-1]["t"] >= packets[0]["t"]


def test_load_dataset_benchmark():
    json_path = os.path.join("hardware", "data", "reference_discharge_profile.json")
    assert os.path.exists(json_path)
    packets = load_dataset_file(json_path)
    assert len(packets) >= 10
    assert packets[0]["battery_id"] == "BAT-REF-001"
    assert packets[0]["v"] == 4.200

