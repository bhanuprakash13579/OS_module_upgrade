from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from collections import defaultdict

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.models.detention import DrMaster, DrItems
from app.models.config import BatchMaster
import app.schemas.detention as schemas
from app.services.rules_engine import BusinessRulesEngine

router = APIRouter()

def get_current_batch(db: Session):
    batch = db.query(BatchMaster).first()
    if not batch or not batch.current_batch_date:
        return date.today(), "Day"
    return batch.current_batch_date, batch.current_batch_shift

def generate_dr_number(db: Session, dr_type: str) -> int:
    """Generate sequential D.R. number based on type for current year."""
    max_no = db.query(func.max(DrMaster.dr_no)).filter(
        DrMaster.dr_type == dr_type,
        DrMaster.dr_year == date.today().year
    ).scalar()
    return (max_no or 0) + 1


@router.post("/", response_model=schemas.DrMasterOut)
def create_dr(data: schemas.DrMasterCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    rules = BusinessRulesEngine(db)
    batch_date, batch_shift = get_current_batch(db)
    
    # ── Rules Engine Validations ──
    data.passport_no = rules.normalize_passport(data.passport_no)
    
    if data.flight_date:
        rules.validate_flight_date(data.flight_date, batch_date)
        
    rules.validate_pax_dates(data.pax_date_of_birth, data.departure_date, batch_date)
    
    dr_no = generate_dr_number(db, data.dr_type)
    dr_year = date.today().year
    
    total_val = sum([item.items_value for item in data.items])
    total_fa = sum([item.items_fa for item in data.items])
    
    dr_obj = DrMaster(
        dr_no=dr_no,
        dr_date=date.today(),
        dr_year=dr_year,
        dr_type=data.dr_type,
        shift=data.shift or batch_shift,
        batch_date=batch_date,
        batch_shift=batch_shift,
        login_id=current_user.user_id,
        total_items_value=total_val,
        total_fa_value=total_fa,
        closure_ind="N",
        dr_printed="N",
        **data.model_dump(exclude={"items"})
    )
    
    db.add(dr_obj)
    db.commit()
    db.refresh(dr_obj)
    
    for c_item in data.items:
        db_item = DrItems(
            dr_no=dr_no,
            dr_date=dr_obj.dr_date,
            dr_type=dr_obj.dr_type,
            **c_item.model_dump()
        )
        db.add(db_item)
        
    db.commit()
    return dr_obj


@router.get("/", response_model=List[schemas.DrMasterOut])
def get_all_drs(db: Session = Depends(get_db)):
    """Retrieve recent Detention Receipts for the datagrid."""
    records = db.query(DrMaster).filter(
        DrMaster.entry_deleted == "N"
    ).order_by(DrMaster.id.desc()).limit(100).all()
    
    if records:
        # Bulk-load items in ONE query (N+1 fix) — key is (dr_no, dr_date, dr_type)
        keys = list({(r.dr_no, r.dr_date, r.dr_type) for r in records})
        pair_filter = or_(*[
            and_(DrItems.dr_no == no, DrItems.dr_date == dt, DrItems.dr_type == tp)
            for no, dt, tp in keys
        ])
        all_items = db.query(DrItems).filter(pair_filter, DrItems.entry_deleted == "N").all()
        items_map: dict = defaultdict(list)
        for item in all_items:
            items_map[(item.dr_no, item.dr_date, item.dr_type)].append(item)
        for r in records:
            r.items = items_map.get((r.dr_no, r.dr_date, r.dr_type), [])
    return records


@router.get("/{dr_no}/{dr_year}", response_model=schemas.DrMasterOut)
def get_dr(dr_no: int, dr_year: int, db: Session = Depends(get_db)):
    dr_obj = db.query(DrMaster).filter(
        DrMaster.dr_no == dr_no, 
        DrMaster.dr_year == dr_year,
        DrMaster.entry_deleted == "N"
    ).first()
    
    if not dr_obj:
        raise HTTPException(status_code=404, detail="D.R. not found.")
        
    items = db.query(DrItems).filter(
        DrItems.dr_no == dr_no, 
        DrItems.dr_date == dr_obj.dr_date,
        DrItems.dr_type == dr_obj.dr_type,
        DrItems.entry_deleted == "N"
    ).all()
    
    dr_obj.items = items
    return dr_obj


@router.put("/{dr_no}/{dr_year}/print")
def lock_dr_for_print(dr_no: int, dr_year: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Locks DR on print (dr_printed='Y')."""
    dr = db.query(DrMaster).filter(DrMaster.dr_no == dr_no, DrMaster.dr_year == dr_year).first()
    if not dr:
        raise HTTPException(status_code=404, detail="D.R. not found")
    dr.dr_printed = "Y"
    db.commit()
    return {"message": "D.R. Locked"}
