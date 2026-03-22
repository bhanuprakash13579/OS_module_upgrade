from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from collections import defaultdict

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.models.baggage import BrMaster, BrItems
from app.models.config import BatchMaster
from app.models.masters import BrNoLimits
import app.schemas.baggage as schemas
from app.services.duty_calculator import DutyCalculator
from app.services.rules_engine import BusinessRulesEngine

router = APIRouter()

def get_next_br_no(db: Session, br_type: str) -> int:
    """Generate the next B.R. number based on BrNoLimits configuration."""
    limit = db.query(BrNoLimits).filter(BrNoLimits.br_type == br_type).first()
    if not limit:
        # Fallback
        max_no = db.query(func.max(BrMaster.br_no)).filter(BrMaster.br_type == br_type).scalar()
        return (max_no or 0) + 1
        
    max_no = db.query(func.max(BrMaster.br_no)).filter(BrMaster.br_type == br_type).scalar()
    
    if not max_no or max_no < limit.br_series_from:
        return limit.br_series_from
    if max_no >= limit.br_series_to:
        raise HTTPException(status_code=400, detail=f"B.R. limits exhausted for type {br_type}")
    return max_no + 1


def get_current_batch(db: Session):
    batch = db.query(BatchMaster).first()
    if not batch or not batch.current_batch_date:
        return date.today(), "Day"
    return batch.current_batch_date, batch.current_batch_shift


@router.post("/", response_model=schemas.BrMasterOut)
def create_br(data: schemas.BrMasterCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Create a new Baggage Receipt with items, auto-calculating duties and BR number."""
    
    rules = BusinessRulesEngine(db)
    batch_date, batch_shift = get_current_batch(db)
    
    # ── Rules Engine Validations ──
    data.passport_no = rules.normalize_passport(data.passport_no)
    
    if data.flight_date:
        rules.validate_flight_date(data.flight_date, batch_date)
        
    rules.validate_pax_dates(data.pax_date_of_birth, data.departure_date, batch_date)

    # Note: For strict legacy flow, we warn on duplicate passports if required (handled on frontend via /passport/{no} endpoint)

    # Calculate Duty
    calculator = DutyCalculator(db)
    item_dicts = [item.model_dump() for item in data.items]
    t_val, t_fa, t_duty, compiled_items = calculator.process_br_items(item_dicts)
    
    # Rule: Free Allowance Usage limit
    if data.passport_no not in ["DOMESTIC", "UNCLAIMED"]:
        rules.validate_fa_availability(data.passport_no, data.flight_date or batch_date, t_fa)
    
    # Compute BR Amount (Payable)
    br_amount = t_duty + data.rf_amount - data.ref_amount + data.pp_amount + data.wh_amount + data.other_amount
    
    br_no = get_next_br_no(db, data.br_type)
    
    # Special Handling: DOMESTIC/UNCLAIMED
    passport = data.passport_no
    if passport in ["DOMESTIC", "UNCLAIMED"]:
        pass # Logic handled: UI will lock field. Server accepts it.

    br_obj = BrMaster(
        br_no=br_no,
        br_date=date.today(),
        br_type=data.br_type,
        actual_br_type=data.br_type,
        br_year=date.today().year,
        batch_date=batch_date,
        batch_shift=batch_shift,
        login_id=current_user.user_id,
        
        total_items_value=t_val,
        total_fa_value=t_fa,
        total_duty_amount=t_duty,
        br_amount=br_amount,
        total_payable=br_amount,
        
        # Flattened fields
        **data.model_dump(exclude={"items"})
    )
    
    db.add(br_obj)
    db.commit()
    db.refresh(br_obj)
    
    # Insert items
    for c_item in compiled_items:
        db_item = BrItems(
            br_no=br_no,
            br_date=br_obj.br_date,
            br_type=br_obj.br_type,
            batch_date=batch_date,
            batch_shift=batch_shift,
            login_id=current_user.user_id,
            **c_item
        )
        db.add(db_item)
        
    db.commit()
    return br_obj


@router.get("/", response_model=List[schemas.BrMasterOut])
def get_all_brs(db: Session = Depends(get_db)):
    """Retrieve recent Baggage Receipts for the datagrid."""
    records = db.query(BrMaster).filter(
        BrMaster.entry_deleted == "N"
    ).order_by(BrMaster.id.desc()).limit(100).all()

    if records:
        # Bulk-load items in ONE query (N+1 fix)
        keys = list({(r.br_no, r.br_date) for r in records})
        pair_filter = or_(*[and_(BrItems.br_no == no, BrItems.br_date == dt) for no, dt in keys])
        all_items = db.query(BrItems).filter(pair_filter, BrItems.entry_deleted == "N").all()
        items_map: dict = defaultdict(list)
        for item in all_items:
            items_map[(item.br_no, item.br_date)].append(item)
        for r in records:
            r.items = items_map.get((r.br_no, r.br_date), [])
    return records


@router.get("/{br_no}/{br_year}", response_model=schemas.BrMasterOut)
def get_br(br_no: int, br_year: int, db: Session = Depends(get_db)):
    """Retrieve full BR Data + Items."""
    br = db.query(BrMaster).filter(BrMaster.br_no == br_no, BrMaster.br_year == br_year, BrMaster.entry_deleted == "N").first()
    if not br:
        raise HTTPException(status_code=404, detail="B.R. not found")
        
    items = db.query(BrItems).filter(BrItems.br_no == br_no, BrItems.br_date == br.br_date, BrItems.entry_deleted == "N").all()
    br.items = items
    return br


@router.get("/passport/{passport_no}")
def get_previous_brs_by_passport(passport_no: str, db: Session = Depends(get_db)):
    """Legacy feature: Previous B/R Details Retrieval by Passport."""
    brs = db.query(BrMaster).filter(BrMaster.passport_no == passport_no, BrMaster.entry_deleted == "N").order_by(BrMaster.br_date.desc()).limit(50).all()
    if not brs:
        raise HTTPException(status_code=404, detail="Previous B/R Details Could not be retrieved from Database...")
    return brs


@router.put("/{br_no}/{br_year}/print")
def lock_br_for_print(br_no: int, br_year: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Locks BR on print (br_printed='Y')."""
    br = db.query(BrMaster).filter(BrMaster.br_no == br_no, BrMaster.br_year == br_year).first()
    if not br:
        raise HTTPException(status_code=404, detail="B.R. not found")
    br.br_printed = "Y"
    db.commit()
    return {"message": "B.R. Locked"}
