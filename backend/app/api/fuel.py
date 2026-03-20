from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.models.fuel import FuelMaster

router = APIRouter()

class FuelCreate(BaseModel):
    airline_name: str
    flight_no: str
    flight_date: date
    fuel_qty: float
    assessable_value: float
    duty_amount: float

class FuelOut(FuelCreate):
    id: int
    fuel_no: int
    fuel_date: date
    fuel_year: int
    model_config = ConfigDict(from_attributes=True)

@router.post("/", response_model=FuelOut)
def create_fuel(data: FuelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    max_no = db.query(func.max(FuelMaster.fuel_no)).filter(FuelMaster.fuel_year == date.today().year).scalar()
    new_no = (max_no or 0) + 1
    
    obj = FuelMaster(
        fuel_no=new_no,
        fuel_date=date.today(),
        fuel_year=date.today().year,
        login_id=current_user.user_id,
        entry_deleted="N",
        **data.model_dump()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
