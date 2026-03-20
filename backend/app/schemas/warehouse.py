from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

# ── General Warehouse ──
class WhItemBase(BaseModel):
    items_sno: int
    items_desc: Optional[str] = None
    items_qty: float = 0.0
    items_uqc: Optional[str] = None
    items_value: float = 0.0
    warehoused_qty: float = 0.0

class WhItemCreate(WhItemBase): pass

class WhItemOut(WhItemBase):
    id: int
    wh_no: int
    balance_qty: float
    released_qty: float
    model_config = ConfigDict(from_attributes=True)

class WhMasterBase(BaseModel):
    dr_type: str
    dr_no: int
    dr_year: int
    storage_location: Optional[str] = None
    
class WhMasterCreate(WhMasterBase):
    items: List[WhItemCreate]

class WhMasterOut(WhMasterBase):
    id: int
    wh_no: int
    wh_date: date
    wh_year: int
    pax_name: Optional[str] = None
    passport_no: Optional[str] = None
    closure_ind: str
    items: List[WhItemOut] = []
    model_config = ConfigDict(from_attributes=True)

# ── Valuables Warehouse ──
class ValuablesItemCreate(WhItemBase): pass

class ValuablesMasterCreate(WhMasterBase):
    items: List[ValuablesItemCreate]
