from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.models.warehouse import WhMaster, WhItems, ValuablesMaster, ValuablesItems
from app.models.detention import DrMaster
import app.schemas.warehouse as schemas

router = APIRouter()

def generate_wh_no(db: Session, model) -> int:
    max_no = db.query(func.max(model.wh_no)).filter(model.wh_year == date.today().year).scalar()
    return (max_no or 0) + 1

@router.post("/general", response_model=schemas.WhMasterOut)
def create_wh(data: schemas.WhMasterCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Verify DR exist
    dr = db.query(DrMaster).filter(DrMaster.dr_no == data.dr_no, DrMaster.dr_year == data.dr_year, DrMaster.dr_type == data.dr_type).first()
    if not dr:
        raise HTTPException(status_code=404, detail="Parent D.R. not found")

    wh_no = generate_wh_no(db, WhMaster)
    
    wh_obj = WhMaster(
        wh_no=wh_no,
        wh_date=date.today(),
        wh_year=date.today().year,
        dr_type=data.dr_type,
        dr_no=data.dr_no,
        dr_year=data.dr_year,
        storage_location=data.storage_location,
        login_id=current_user.user_id,
        closure_ind="N",
        pax_name=dr.pax_name,
        passport_no=dr.passport_no
    )
    db.add(wh_obj)
    db.commit()
    db.refresh(wh_obj)
    
    for c_item in data.items:
        db_item = WhItems(
            wh_no=wh_no,
            wh_date=wh_obj.wh_date,
            wh_year=wh_obj.wh_year,
            balance_qty=c_item.warehoused_qty,
            released_qty=0.0,
            **c_item.model_dump()
        )
        db.add(db_item)
        
    db.commit()
    return wh_obj

@router.post("/valuables")
def create_valuables(data: schemas.ValuablesMasterCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Similar logic for valuables tracking
    dr = db.query(DrMaster).filter(DrMaster.dr_no == data.dr_no, DrMaster.dr_year == data.dr_year, DrMaster.dr_type == data.dr_type).first()
    if not dr:
        raise HTTPException(status_code=404, detail="Parent D.R. not found")

    wh_no = generate_wh_no(db, ValuablesMaster)
    
    wh_obj = ValuablesMaster(
        wh_no=wh_no,
        wh_date=date.today(),
        wh_year=date.today().year,
        dr_type=data.dr_type,
        dr_no=data.dr_no,
        dr_year=data.dr_year,
        storage_location=data.storage_location,
        login_id=current_user.user_id,
        closure_ind="N"
    )
    db.add(wh_obj)
    db.commit()
    
    for c_item in data.items:
        db_item = ValuablesItems(
            wh_no=wh_no,
            wh_date=wh_obj.wh_date,
            wh_year=wh_obj.wh_year,
            balance_qty=c_item.warehoused_qty,
            released_qty=0.0,
            **c_item.model_dump()
        )
        db.add(db_item)
        
    db.commit()
    return {"message": "Valuables stored successfully", "wh_no": wh_no}
