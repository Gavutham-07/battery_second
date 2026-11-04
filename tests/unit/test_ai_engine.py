import pytest
from ai_engine.features import extract_features
from ai_engine.safety_screener import screen_battery_safety
from ai_engine.soh_estimator import estimate_soh_and_capacity
from ai_engine.confidence import evaluate_confidence_and_quality
from ai_engine.evaluator import evaluate_battery


def create_synthetic_telemetry(n=20, temp=28.0, current=0.5, v_start=3.35, v_drop=0.005, dt=1.0):
    packets = []
    for i in range(n):
        packets.append({
            "battery_id": "BAT-AI-TEST",
            "sec": float(i * dt),
            "v": round(v_start - (i * v_drop), 4),
            "i": float(current),
            "t": float(temp + (i * 0.05)),
            "event": "DISCHARGE"
        })
    return packets


def test_feature_extraction():
    tel = create_synthetic_telemetry(n=10)
    features = extract_features(tel)
    assert features["sample_count"] == 10
    assert features["duration_sec"] == 9.0
    assert features["v_initial"] == 3.35
    assert features["v_final"] < 3.35
    assert features["coulomb_ah"] > 0.0
    assert features["t_delta"] >= 0.0


def test_safety_screener_nominal_lfp():
    tel = create_synthetic_telemetry(n=10, temp=28.0, v_start=3.35)
    features = extract_features(tel)
    status, flags = screen_battery_safety(features, chemistry="LFP")
    assert status == "PASSED"
    assert "NOMINAL_OPERATING_ENVELOPE" in flags


def test_safety_screener_nominal_nmc():
    tel = create_synthetic_telemetry(n=10, temp=28.0, v_start=4.10)
    features = extract_features(tel)
    status, flags = screen_battery_safety(features, chemistry="NMC")
    assert status == "PASSED"
    assert "NOMINAL_OPERATING_ENVELOPE" in flags


def test_safety_screener_thermal_warning():
    # Temperature over 45 C triggers WARNING
    tel = create_synthetic_telemetry(n=10, temp=46.5, v_start=3.35)
    features = extract_features(tel)
    status, flags = screen_battery_safety(features, chemistry="LFP")
    assert status == "WARNING"
    assert "ELEVATED_TEMPERATURE_WARNING" in flags


def test_safety_screener_thermal_critical_failure():
    # Temperature over 55 C triggers FAILED
    tel = create_synthetic_telemetry(n=10, temp=56.0, v_start=3.35)
    features = extract_features(tel)
    status, flags = screen_battery_safety(features, chemistry="LFP")
    assert status == "FAILED"
    assert "CRITICAL_OVER_TEMPERATURE" in flags


def test_safety_screener_thermal_runaway_rate():
    # Temperature jumping 1.5 degrees in 1 second triggers FAILED
    tel = create_synthetic_telemetry(n=5, v_start=3.35)
    tel[2]["t"] = tel[1]["t"] + 1.5  # rate 1.5 C/s > 0.5 C/s
    features = extract_features(tel)
    status, flags = screen_battery_safety(features, chemistry="LFP")
    assert status == "FAILED"
    assert "THERMAL_RUNAWAY_RATE_ALERT" in flags


def test_safety_screener_unknown_sparse_data():
    tel = [{"battery_id": "BAT-1", "sec": 1.0, "v": 3.3, "i": 0.5, "t": 25.0, "event": "RUN"}]
    features = extract_features(tel)
    status, flags = screen_battery_safety(features, chemistry="LFP")
    assert status == "UNKNOWN"
    assert "INSUFFICIENT_TELEMETRY" in flags


def test_decoupled_soh_and_capacity():
    tel = create_synthetic_telemetry(n=20, current=0.5, v_start=3.35, v_drop=0.005)
    features = extract_features(tel)
    soh, cap = estimate_soh_and_capacity(features, rated_capacity_ah=2.5, chemistry="LFP")
    assert soh is not None
    assert cap is not None
    assert 0.0 <= soh <= 100.0
    assert 0.0 < cap <= 2.6
    # Verify decoupled fields
    assert isinstance(soh, float)
    assert isinstance(cap, float)


def test_confidence_scoring():
    # Long test (25 samples over 25s) yields high confidence
    dense_tel = create_synthetic_telemetry(n=25, dt=1.0)
    f_dense = extract_features(dense_tel)
    conf_dense, q_dense = evaluate_confidence_and_quality(f_dense)
    assert conf_dense >= 80.0
    assert q_dense["data_sufficiency"] == "SATISFACTORY"

    # Very short test (3 samples over 2s) yields low confidence
    short_tel = create_synthetic_telemetry(n=3, dt=1.0)
    f_short = extract_features(short_tel)
    conf_short, q_short = evaluate_confidence_and_quality(f_short)
    assert conf_short < 60.0
    assert q_short["data_sufficiency"] == "SPARSE"


def test_safety_precedence_high_soh_failed_safety():
    """Rule 4 & 5: High SOH with FAILED safety MUST result in RECYCLE, never reuse."""
    tel = create_synthetic_telemetry(n=20, temp=58.0, v_start=3.35)  # High temp will fail safety
    meta = {"battery_id": "BAT-CRIT-FAIL", "chemistry": "LFP", "rated_capacity_ah": 2.5}
    res = evaluate_battery(tel, meta)
    assert res["safety_status"] == "FAILED"
    assert res["decision"] == "RECYCLE"


def test_safety_precedence_high_soh_warning_safety():
    """Rule 4 & 5: High SOH with WARNING safety MUST result in QUARANTINE."""
    tel = create_synthetic_telemetry(n=20, temp=47.0, v_start=3.35)  # Warning temp
    meta = {"battery_id": "BAT-WARN", "chemistry": "LFP", "rated_capacity_ah": 2.5}
    res = evaluate_battery(tel, meta)
    assert res["safety_status"] == "WARNING"
    assert res["decision"] == "QUARANTINE"


def test_safety_precedence_unknown_triggers_further_testing():
    """Rule: UNKNOWN safety status MUST trigger FURTHER_TESTING."""
    sparse_tel = [{"battery_id": "BAT-SPARSE", "sec": 1.0, "v": 3.3, "i": 0.5, "t": 25.0, "event": "RUN"}]
    meta = {"battery_id": "BAT-SPARSE", "chemistry": "LFP", "rated_capacity_ah": 2.5}
    res = evaluate_battery(sparse_tel, meta)
    assert res["safety_status"] == "UNKNOWN"
    assert res["decision"] == "FURTHER_TESTING"


def test_decision_soh_routing_when_safe():
    meta = {"battery_id": "BAT-SAFE", "chemistry": "LFP", "rated_capacity_ah": 2.5}
    # Healthy cycle -> CONTINUE_EV
    tel_healthy = create_synthetic_telemetry(n=25, current=0.5, v_start=3.35, v_drop=0.002)
    res = evaluate_battery(tel_healthy, meta)
    assert res["safety_status"] == "PASSED"
    assert res["decision"] == "CONTINUE_EV"
