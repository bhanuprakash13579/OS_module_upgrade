from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user, get_adjn_user
from app.models.revenue import Revenue, RevChallans, ChallanMaster
from app.models.config import BatchMaster
import app.schemas.revenue as schemas

router = APIRouter()

def get_current_batch(db: Session):
    batch = db.query(BatchMaster).first()
    if not batch or not batch.current_batch_date:
        return date.today(), "Day"
    return batch.current_batch_date, batch.current_batch_shift

@router.post("/", response_model=schemas.RevenueOut)
def record_revenue(data: schemas.RevenueCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    """Record daily revenue entry. Admin only."""
    total = (data.baggage_duty + data.addl_duty + data.sadcess_duty + 
             data.gold_duty + data.silver_duty + data.rf_amount + 
             data.pp_amount + data.misc_amount) - data.ref_amount
             
    obj = Revenue(
        total_duty=total,
        **data.model_dump()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/challans", response_model=schemas.RevChallansOut)
def record_challan(data: schemas.RevChallansCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    obj = RevChallans(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/sdo_challan", response_model=schemas.ChallanMasterOut)
def record_sdo_challan(data: schemas.ChallanMasterCreate, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    batch_date, batch_shift = get_current_batch(db)
    
    obj = ChallanMaster(
        batch_date=batch_date,
        batch_shift=batch_shift,
        **data.model_dump()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
