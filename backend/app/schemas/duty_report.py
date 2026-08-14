"""
Pydantic schemas for the Duty Collection Report (DR) module.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict


# ── Tariff ────────────────────────────────────────────────────────────────────

class DrTariffCreate(BaseModel):
    effective_from: date
    label: Optional[str] = None
    baggage_rate: float = 0.35
    liquor_duty_rate: float = 0.50
    aidc_liquor_rate: float = 1.0
    gold_bcd_rate: float = 0.35
    aidc_gold_rate: float = 0.05
    gold_cons_bcd_rate: float = 0.10
    aidc_gold_cons_rate: float = 0.05
    silver_bcd_rate: float = 0.35
    aidc_silver_rate: float = 0.05
    silver_cons_rate: float = 0.05
    aidc_silver_cons_rate: float = 0.05


class DrTariffOut(DrTariffCreate):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Item Types ────────────────────────────────────────────────────────────────

class DrItemTypeCreate(BaseModel):
    name: str
    is_system: bool = False


class DrItemTypeOut(BaseModel):
    id: int
    name: str
    usage_count: int
    is_system: bool
    model_config = ConfigDict(from_attributes=True)


# ── Session ───────────────────────────────────────────────────────────────────

class DrSessionCreate(BaseModel):
    report_date: date
    shift: str           # 'DAY' or 'NIGHT'
    batch_name: Optional[str] = None
    created_by: Optional[str] = None


class DrSessionOut(BaseModel):
    id: int
    report_date: date
    shift: str
    batch_name: Optional[str] = None
    challan_no: Optional[str] = None   # bank deposit challan for offline BRs
    tariff_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[str] = None
    tariff: Optional[DrTariffOut] = None
    model_config = ConfigDict(from_attributes=True)


class SetChallanRequest(BaseModel):
    challan_no: str


# ── Entries ───────────────────────────────────────────────────────────────────

class DrEntryIn(BaseModel):
    sort_order: int
    sl_no: Optional[int] = None
    br_no: Optional[str] = None
    os_ref: Optional[str] = None
    item_desc: Optional[str] = None
    dutiable_value: float = 0
    gold_weight_gms: float = 0
    baggage_duty: float = 0
    liquor_duty: float = 0
    cigarette_duty: float = 0
    sw_sc: float = 0
    gold_duty_bcd: float = 0
    gold_duty_cons: float = 0
    silver_duty_cons: float = 0
    sws_on_gold: float = 0
    aidc_gold_silver: float = 0
    sws_on_silver: float = 0
    aidc_on_liquor: float = 0
    redemption_fine: float = 0
    reexport_fine: float = 0
    personal_penalty: float = 0
    other_charges: float = 0
    fuel_duty: float = 0
    cess_on_cig: float = 0
    total_duty: float = 0
    flight_no: Optional[str] = None
    is_sbi_challan: bool = False
    is_offline_br: bool = False         # offline (manual) BR — shown in red in Excel
    overrides: Optional[str] = None     # JSON text


class DrEntryOut(DrEntryIn):
    id: int
    session_id: int
    model_config = ConfigDict(from_attributes=True)


class DrDrEntryIn(BaseModel):
    sort_order: int
    dr_no: Optional[str] = None
    amount: float = 0
    item_desc: Optional[str] = None
    remarks: Optional[str] = None


class DrDrEntryOut(DrDrEntryIn):
    id: int
    session_id: int
    model_config = ConfigDict(from_attributes=True)


class DrOsEntryIn(BaseModel):
    sort_order: int
    os_no: Optional[str] = None
    amount: float = 0
    item_desc: Optional[str] = None
    remarks: Optional[str] = None


class DrOsEntryOut(DrOsEntryIn):
    id: int
    session_id: int
    model_config = ConfigDict(from_attributes=True)


# ── Settings ──────────────────────────────────────────────────────────────────

class DrSettingsIn(BaseModel):
    greeting_recipients: str = "Sir"


class DrSettingsOut(BaseModel):
    id: int
    greeting_recipients: str
    model_config = ConfigDict(from_attributes=True)


# ── Composite ─────────────────────────────────────────────────────────────────

class SessionWithEntries(DrSessionOut):
    entries: List[DrEntryOut] = []
    dr_entries: List[DrDrEntryOut] = []
    os_entries: List[DrOsEntryOut] = []


class BulkSaveRequest(BaseModel):
    entries: List[DrEntryIn] = []
    dr_entries: List[DrDrEntryIn] = []
    os_entries: List[DrOsEntryIn] = []


# ── Formula Rules ────────────────────────────────────────────────────────────

class DrFormulaRuleIn(BaseModel):
    sort_order: int = 0
    target_column: str                  # DrEntry field key, e.g. "baggage_duty"
    column_label: Optional[str] = None  # display label
    condition_type: str = "all"         # "all" | "only" | "except"
    condition_items: str = ""           # comma-separated item names
    expression: str = ""               # e.g. "value * baggage_rate"; empty = manual
    is_active: bool = True
    notes: Optional[str] = None
    lineage_id: Optional[int] = None
    effective_from: Optional[date] = None


class DrFormulaRuleOut(DrFormulaRuleIn):
    id: int
    created_at: Optional[datetime] = None
    # Which rule this descends from, the day it took effect, and who wrote it.
    lineage_id: Optional[int] = None
    effective_from: Optional[date] = None
    changed_by: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class DrFormulaRuleRevision(BaseModel):
    """A new formula for one column, signed by the officer making the change.

    The username and password are the officer's own, typed again. A formula sets
    what every passenger is charged, and the menu that opens this dialog sits one
    click from the sheet; asking for the password makes the change deliberate.
    """
    expression: str = ""
    username: str
    password: str


class SubmitSessionRequest(BaseModel):
    submitted_by: Optional[str] = None


# ── Duty computation ──────────────────────────────────────────────────────────

class ComputeDutiesRequest(BaseModel):
    tariff_id: int
    item_desc: str
    dutiable_value: float = 0
    gold_weight_gms: float = 0


class ComputeDutiesResponse(BaseModel):
    baggage_duty: float = 0
    liquor_duty: float = 0
    gold_duty_bcd: float = 0
    gold_duty_cons: float = 0
    silver_duty_cons: float = 0
    aidc_gold_silver: float = 0
    aidc_on_liquor: float = 0
    total_duty: float = 0
    auto_fields: List[str] = []
