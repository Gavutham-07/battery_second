import pytest
from pydantic import ValidationError
from backend.schemas import (
    BatteryRegistration,
    TelemetryPacket,
    AnalysisRequest,
    AnalysisReport,
    ExchangeApproval,
    WhatIfRequest,
    InventoryItem,
)


def test_battery_registration_valid():
    reg = BatteryRegistration(
        battery_id="BAT-101",
        chemistry="LFP",
        rated_capacity_ah=2.5,
        voltage=3.2,
        manufacturer="EVE Energy",
        source_vehicle="Ola S1 Pro"
    )
    assert reg.battery_id == "BAT-101"
    assert reg.rated_capacity_ah == 2.5


def test_battery_registration_invalid_capacity():
    with pytest.raises(ValidationError):
        BatteryRegistration(
            battery_id="BAT-101",
            chemistry="LFP",
            rated_capacity_ah=0.0  # Must be gt 0
        )


def test_telemetry_packet_valid():
    packet = TelemetryPacket(
        battery_id="BAT-101",
        sec=15.0,
        v=3.842,
        i=0.405,
        t=29.10,
        event="RUNNING"
    )
    assert packet.sec == 15.0
    assert packet.v == 3.842


def test_telemetry_packet_invalid_sec():
    with pytest.raises(ValidationError):
        TelemetryPacket(
            battery_id="BAT-101",
            sec=-1.0,  # Must be ge 0
            v=3.8,
            i=0.4,
            t=25.0,
            event="RUNNING"
        )


def test_analysis_report_valid_enums():
    for status in ["PASSED", "WARNING", "FAILED", "UNKNOWN"]:
        for decision in ["CONTINUE_EV", "SECOND_LIFE_STORAGE", "FURTHER_TESTING", "QUARANTINE", "RECYCLE"]:
            report = AnalysisReport(
                battery_id="BAT-101",
                soh=85.0,
                available_capacity_ah=2.1,
                safety_status=status,
                confidence=95.0,
                decision=decision,
                mode="LIVE"
            )
            assert report.safety_status == status
            assert report.decision == decision


def test_analysis_report_invalid_safety_status():
    with pytest.raises(ValidationError):
        AnalysisReport(
            battery_id="BAT-101",
            soh=85.0,
            safety_status="SAFE",  # Invalid enum: must be PASSED/WARNING/FAILED/UNKNOWN
            decision="CONTINUE_EV",
            mode="LIVE"
        )


def test_analysis_report_invalid_decision():
    with pytest.raises(ValidationError):
        AnalysisReport(
            battery_id="BAT-101",
            soh=85.0,
            safety_status="PASSED",
            decision="REUSE_ARBITRARY",  # Invalid decision enum
            mode="LIVE"
        )


def test_analysis_report_soh_bounds():
    # Valid bounds
    r1 = AnalysisReport(
        battery_id="BAT-101",
        soh=0.0,
        safety_status="PASSED",
        decision="RECYCLE",
        mode="LIVE"
    )
    assert r1.soh == 0.0

    r2 = AnalysisReport(
        battery_id="BAT-101",
        soh=100.0,
        safety_status="PASSED",
        decision="CONTINUE_EV",
        mode="LIVE"
    )
    assert r2.soh == 100.0

    # Invalid > 100.0
    with pytest.raises(ValidationError):
        AnalysisReport(
            battery_id="BAT-101",
            soh=105.0,
            safety_status="PASSED",
            decision="CONTINUE_EV",
            mode="LIVE"
        )

    # Invalid < 0.0
    with pytest.raises(ValidationError):
        AnalysisReport(
            battery_id="BAT-101",
            soh=-5.0,
            safety_status="FAILED",
            decision="RECYCLE",
            mode="LIVE"
        )


def test_analysis_report_confidence_bounds():
    with pytest.raises(ValidationError):
        AnalysisReport(
            battery_id="BAT-101",
            soh=80.0,
            confidence=101.0,  # Invalid > 100.0
            safety_status="PASSED",
            decision="CONTINUE_EV",
            mode="LIVE"
        )


def test_what_if_request_bounds():
    valid = WhatIfRequest(
        battery_id="BAT-101",
        daily_hours=4.0,
        temp_c=25.0,
        dod_pct=80.0
    )
    assert valid.dod_pct == 80.0

    with pytest.raises(ValidationError):
        WhatIfRequest(
            battery_id="BAT-101",
            daily_hours=0.0,  # Must be gt 0
            temp_c=25.0,
            dod_pct=80.0
        )

    with pytest.raises(ValidationError):
        WhatIfRequest(
            battery_id="BAT-101",
            daily_hours=4.0,
            temp_c=25.0,
            dod_pct=105.0  # Must be le 100
        )

