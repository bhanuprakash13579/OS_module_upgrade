from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ── DC Master ────────────────────────────────────────────────────
class DcMasterBase(BaseModel):
    dc_code: str
    dc_name: str
    dc_status: str = "Active"

class DcMasterOut(DcMasterBase):
    id: int
    class Config:
        from_attributes = True

class DcMasterCreate(DcMasterBase): pass


# ── Airlines Master ──────────────────────────────────────────────
class AirlinesMastBase(BaseModel):
    airline_name: str
    airline_code: str

class AirlinesMastOut(AirlinesMastBase):
    id: int
    class Config:
        from_attributes = True

class AirlinesMastCreate(AirlinesMastBase): pass


# ── Flight Master ────────────────────────────────────────────────
class ArrivalFlightMasterBase(BaseModel):
    flight_no: str
    airline_code: str

class ArrivalFlightMasterOut(ArrivalFlightMasterBase):
    id: int
    class Config:
        from_attributes = True

class ArrivalFlightMasterCreate(ArrivalFlightMasterBase): pass


# ── Airport Master ───────────────────────────────────────────────
class AirportMasterBase(BaseModel):
    airport_name: Optional[str] = None
    airport_status: str = "Active"

class AirportMasterOut(AirportMasterBase):
    id: int
    class Config:
        from_attributes = True

class AirportMasterUpdate(BaseModel):
    airport_status: str


# ── Nationality Master ───────────────────────────────────────────
class NationalityMasterBase(BaseModel):
    nationality: str

class NationalityMasterOut(NationalityMasterBase):
    id: int
    class Config:
        from_attributes = True

class NationalityMasterCreate(NationalityMasterBase): pass


# ── Port Master ──────────────────────────────────────────────────
class PortMasterBase(BaseModel):
    port_of_departure: str

class PortMasterOut(PortMasterBase):
    id: int
    class Config:
        from_attributes = True

class PortMasterCreate(PortMasterBase): pass


# ── Item Category Master ─────────────────────────────────────────
class ItemCatMasterBase(BaseModel):
    category_code: str
    category_desc: str
    active_ind: str = "A"
    dri_cus_10_desc: Optional[str] = None
    dri_cus_10_sno: Optional[str] = None
    dri_cus_11_desc: Optional[str] = None
    dri_cus_11_sno: Optional[str] = None
    bcd_adv_rate: float = 0.0
    cvd_adv_rate: float = 0.0
    bcd_specific_rate: float = 0.0
    bcd_specific_uqc: Optional[str] = None
    cvd_specific_rate: float = 0.0
    cvd_specific_uqc: Optional[str] = None

class ItemCatMasterOut(ItemCatMasterBase):
    id: int
    class Config:
        from_attributes = True

class ItemCatMasterCreate(ItemCatMasterBase): pass

class ItemCatMasterUpdate(BaseModel):
    active_ind: str


# ── Duty Rate Master ─────────────────────────────────────────────
class DutyRateMasterBase(BaseModel):
    duty_category: str
    from_date: date
    to_date: Optional[date] = None
    active_ind: str = "A"
    bcd_rate: float = 0.0
    cvd_rate: float = 0.0

class DutyRateMasterOut(DutyRateMasterBase):
    id: int
    class Config:
        from_attributes = True

class DutyRateMasterCreate(DutyRateMasterBase): pass

class DutyRateMasterUpdate(BaseModel):
    active_ind: str
    to_date: date


# ── B.R. Number Limits ───────────────────────────────────────────
class BrNoLimitsBase(BaseModel):
    br_type: str
    br_series_from: int
    br_series_to: int

class BrNoLimitsOut(BrNoLimitsBase):
    id: int
    class Config:
        from_attributes = True

class BrNoLimitsCreate(BrNoLimitsBase): pass
class BrNoLimitsUpdate(BrNoLimitsCreate): pass
