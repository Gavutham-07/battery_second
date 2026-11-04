import pytest
from backend.main import ingest_live_data, get_live_data
from backend.schemas import TelemetryPacket
from backend.db import test_connection as check_mongo_connection, tests_collection


def setup_module(module):
    if check_mongo_connection():
        tests_collection.delete_many({"battery_id": "BAT-P3-TEL-01"})


def teardown_module(module):
    if check_mongo_connection():
        tests_collection.delete_many({"battery_id": "BAT-P3-TEL-01"})


def test_ingest_live_data_default_mode():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    packet = TelemetryPacket(
        battery_id="BAT-P3-TEL-01",
        sec=1.0,
        v=3.85,
        i=0.50,
        t=28.5,
        event="RUNNING"
    )

    ack = ingest_live_data(packet, x_data_mode="LIVE")
    assert ack["status"] == "acknowledged"
    assert ack["battery_id"] == "BAT-P3-TEL-01"
    assert ack["sec"] == 1.0
    assert ack["mode"] == "LIVE"


def test_ingest_live_data_replay_mode():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    packet = TelemetryPacket(
        battery_id="BAT-P3-TEL-01",
        sec=2.0,
        v=3.84,
        i=0.51,
        t=28.6,
        event="RUNNING"
    )

    ack = ingest_live_data(packet, x_data_mode="REPLAY")
    assert ack["status"] == "acknowledged"
    assert ack["battery_id"] == "BAT-P3-TEL-01"
    assert ack["sec"] == 2.0
    assert ack["mode"] == "REPLAY"


def test_get_live_data_history():
    if not check_mongo_connection():
        pytest.skip("MongoDB connection unavailable in current environment")

    history = get_live_data("BAT-P3-TEL-01", limit=10)
    assert history["battery_id"] == "BAT-P3-TEL-01"
    assert history["count"] >= 2
    assert len(history["telemetry"]) >= 2
    # Check chronological ordering by sec
    assert history["telemetry"][0]["sec"] == 1.0
    assert history["telemetry"][1]["sec"] == 2.0

