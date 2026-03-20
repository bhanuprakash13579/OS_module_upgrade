from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.models.appeal import AppealMaster
from app.models.offence import CopsMaster

router = APIRouter()

class AppealCreate(BaseModel):
    os_no: str
    os_year: int
    adj_offr_name: str
    adj_offr_designation: str
    adjn_offr_remarks: str

@router.post("/")
def create_appeal(data: AppealCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Create an appeal from an existing ADJUDICATED OS."""
    os = db.query(CopsMaster).filter(CopsMaster.os_no == data.os_no, CopsMaster.os_year == data.os_year).first()
    if not os or os.online_adjn != "Y":
        raise HTTPException(status_code=400, detail="Cannot appeal un-adjudicated O.S.")
        
    obj = AppealMaster(
        os_no=data.os_no,
        os_date=os.os_date,
        os_year=os.os_year,
        pax_name=os.pax_name,
        passport_no=os.passport_no,
        total_items_value=os.total_items_value,
        total_duty_amount=os.total_duty_amount,
        adjudication_date=date.today(),
        adj_offr_name=data.adj_offr_name,
        adj_offr_designation=data.adj_offr_designation,
        adjn_offr_remarks=data.adjn_offr_remarks,
        online_adjn="Y",
        entry_deleted="N"
    )
    db.add(obj)
    db.commit()
    return {"message": "Appeal Adjudication successful, OS shadowed to Appeal table."}
