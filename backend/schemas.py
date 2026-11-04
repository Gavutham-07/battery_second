from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class BatteryRegistration(BaseModel):
    battery_id: str
    chemistry: str
    rated_capacity_ah: float = Field(gt=0)
    voltage: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    source_vehicle: Optional[str] = None


class TelemetryPacket(BaseModel):
    battery_id: str
    sec: float = Field(ge=0.0)
    v: float
    i: float
    t: float
    event: str


class AnalysisRequest(BaseModel):
    battery_id: str
    chemistry: str
    rated_capacity_ah: float = Field(gt=0)


class AnalysisReport(BaseModel):
    battery_id: str
    soh: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    available_capacity_ah: Optional[float] = Field(default=None, gt=0.0)
    safety_status: Literal["PASSED", "WARNING", "FAILED", "UNKNOWN"]
    confidence: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    decision: Literal["CONTINUE_EV", "SECOND_LIFE_STORAGE", "FURTHER_TESTING", "QUARANTINE", "RECYCLE"]
    mode: Literal["LIVE", "REPLAY", "VIRTUAL", "DATASET"]


class ExchangeApproval(BaseModel):
    battery_id: str
    technician_id: str
    approved: bool
    notes: Optional[str] = None


class PassportGenerateRequest(BaseModel):
    battery_id: str


class WhatIfRequest(BaseModel):
    battery_id: str
    daily_hours: float = Field(gt=0)
    temp_c: float
    dod_pct: float = Field(gt=0, le=100)


class InventoryItem(BaseModel):
    battery_id: str
    chemistry: str
    soh: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    status: str
    quantity: int = Field(default=1, ge=0)


class CellGroupingRequest(BaseModel):
    chemistry: str = "LFP"
    target_capacity_ah: Optional[float] = None
    pack_size: int = Field(default=4, ge=2)
    max_soh_variance: float = Field(default=3.0, gt=0.0)
    reserve_cells: bool = Field(default=True)


class RegisterBatteryRequest(BaseModel):
    battery_id: str
    chemistry: str = "LFP"
    rated_capacity_ah: float = Field(default=50.0, gt=0)
    voltage: Optional[float] = None
    owner_name: Optional[str] = None
    vehicle_model: Optional[str] = None


class SimulateStreamRequest(BaseModel):
    battery_id: str
    data_source: str = "virtual_circuit"
    test_profile: str = "healthy"


class AnalyzeRequest(BaseModel):
    battery_id: str


class FlexibleWhatIfRequest(BaseModel):
    battery_id: str
    daily_usage_hours: Optional[float] = None
    ambient_temperature_c: Optional[float] = None
    depth_of_discharge_pct: Optional[float] = None
    daily_hours: Optional[float] = None
    temp_c: Optional[float] = None
    dod_pct: Optional[float] = None


class ApproveAndExchangeRequest(BaseModel):
    battery_id: str
    technician_id: str = "TECH-01"
    technician_notes: Optional[str] = "Passed visual and technical screening"
    approved_route: Optional[str] = "Home Solar Storage"
    exchange_credit_inr: Optional[float] = None


class OwnerPreferenceRequest(BaseModel):
    battery_id: str
    owner_preference: str


class CellPackGroupRequest(BaseModel):
    cell_ids: Optional[list] = None
    target_chemistry: Optional[str] = "LFP"
    max_soh_delta: Optional[float] = 3.0
    pack_size: Optional[int] = 4

