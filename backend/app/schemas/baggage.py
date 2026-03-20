from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class BrItemBase(BaseModel):
    items_sno: int
    items_desc: Optional[str] = None
    items_qty: float = 0.0
    items_uqc: Optional[str] = None
    items_value: float = 0.0
    items_fa: float = 0.0
    items_duty_type: Optional[str] = None
    items_category: Optional[str] = None
    items_release_category: Optional[str] = None

class BrItemCreate(BrItemBase):
    pass

class BrItemOut(BrItemBase):
    id: int
    br_no: int
    items_bcd: float
    items_cvd: float
    items_cess: float
    items_hec: float
    items_duty: float
    items_dr_no: int
    items_dr_year: int
    model_config = ConfigDict(from_attributes=True)


class BrMasterBase(BaseModel):
    br_type: str
    br_shift: Optional[str] = None
    flight_no: Optional[str] = None
    flight_date: Optional[date] = None
    pax_name: Optional[str] = None
    pax_nationality: Optional[str] = None
    passport_no: Optional[str] = None
    passport_date: Optional[date] = None
    passport_issue_place: Optional[str] = None
    pax_address1: Optional[str] = None
    pax_address2: Optional[str] = None
    pax_address3: Optional[str] = None
    pax_date_of_birth: Optional[date] = None
    pax_status: Optional[str] = None
    residence_at: Optional[str] = None
    country_of_departure: Optional[str] = None
    departure_date: Optional[date] = None
    os_no: Optional[str] = None
    os_date: Optional[date] = None
    dr_no: Optional[str] = None
    dr_date: Optional[date] = None
    rf_amount: float = 0.0
    pp_amount: float = 0.0
    ref_amount: float = 0.0
    wh_amount: float = 0.0
    other_amount: float = 0.0
    dc_code: Optional[str] = None
    ff_ind: Optional[str] = None
    arrived_from: Optional[str] = None
    abroad_stay: Optional[int] = None

class BrMasterCreate(BrMasterBase):
    items: List[BrItemCreate]

class BrMasterOut(BrMasterBase):
    id: int
    br_no: int
    br_date: date
    br_year: int
    total_items_value: float
    total_fa_value: float
    total_duty_amount: float
    br_amount: float
    batch_date: Optional[date] = None
    batch_shift: Optional[str] = None
    login_id: Optional[str] = None
    br_printed: str
    br_amount_str: Optional[str] = None
    total_fa_availed: float
    actual_br_type: Optional[str] = None
    total_payable: float
    items: List[BrItemOut] = []
    
    model_config = ConfigDict(from_attributes=True)

class BrTransferRequest(BaseModel):
    source_type: str  # 'OS' or 'DR' or 'Appeal'
    source_no: str
    source_date: date
