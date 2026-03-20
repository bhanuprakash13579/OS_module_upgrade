from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RevenueBase(BaseModel):
    rev_date: date
    baggage_duty: float = 0.0
    addl_duty: float = 0.0
    sadcess_duty: float = 0.0
    gold_duty: float = 0.0
    silver_duty: float = 0.0
    rf_amount: float = 0.0
    ref_amount: float = 0.0
    pp_amount: float = 0.0
    misc_amount: float = 0.0

class RevenueCreate(RevenueBase):
    pass

class RevenueOut(RevenueBase):
    id: int
    total_duty: float
    model_config = ConfigDict(from_attributes=True)


class RevChallansBase(BaseModel):
    rev_date: date
    challan_no: str

class RevChallansCreate(RevChallansBase):
    pass

class RevChallansOut(RevChallansBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ChallanMasterBase(BaseModel):
    sdo_code: str
    sdo_name: str
    challan_no: str
    challan_amount: float = 0.0

class ChallanMasterCreate(ChallanMasterBase):
    pass

class ChallanMasterOut(ChallanMasterBase):
    id: int
    batch_date: date
    batch_shift: str
    model_config = ConfigDict(from_attributes=True)
