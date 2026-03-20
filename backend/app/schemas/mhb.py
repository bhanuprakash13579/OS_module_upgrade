from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class MhbMasterOut(BaseModel):
    id: int
    mhb_no: int
    mhb_date: date
    mhb_year: int
    pax_name: Optional[str] = None
    passport_no: Optional[str] = None
    flight_no: Optional[str] = None
    flight_date: Optional[date] = None
    aoc_tag_no: str
    model_config = ConfigDict(from_attributes=True)

class MhbCreate(BaseModel):
    pax_name: str
    passport_no: Optional[str] = None
    flight_no: Optional[str] = None
    flight_date: Optional[date] = None
    aoc_tag_no: str
