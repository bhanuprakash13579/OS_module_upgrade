from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DrItemBase(BaseModel):
    items_sno: int
    items_desc: Optional[str] = None
    items_qty: float = 0.0
    items_uqc: Optional[str] = None
    items_value: float = 0.0
    items_fa: float = 0.0
    items_release_category: Optional[str] = None

class DrItemCreate(DrItemBase):
    pass

class DrItemOut(DrItemBase):
    id: int
    dr_no: int
    dr_date: date
    # No duty for DR items, only value
    model_config = ConfigDict(from_attributes=True)


class DrMasterBase(BaseModel):
    dr_type: str
    shift: Optional[str] = None
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
    arrived_from: Optional[str] = None
    abroad_stay: Optional[int] = None

class DrMasterCreate(DrMasterBase):
    items: List[DrItemCreate]

class DrMasterOut(DrMasterBase):
    id: int
    dr_no: int
    dr_date: date
    dr_year: int
    total_items_value: float
    total_fa_value: float
    dc_code: Optional[str] = None
    batch_date: Optional[date] = None
    batch_shift: Optional[str] = None
    login_id: Optional[str] = None
    dr_printed: str
    closure_ind: str
    
    items: List[DrItemOut] = []
    model_config = ConfigDict(from_attributes=True)
