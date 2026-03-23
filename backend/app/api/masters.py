from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
import time

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user, get_adjn_user, get_dc_ac_user
from app.models.masters import (
    DcMaster, AirlinesMast, ArrivalFlightMaster, AirportMaster,
    NationalityMaster, PortMaster, ItemCatMaster, DutyRateMaster, BrNoLimits
)
import app.schemas.masters as schemas

router = APIRouter()

# ── Simple in-process TTL cache for read-only master data ────────────────────
# Master tables (airlines, DCs, nationalities, etc.) rarely change during a
# session. Caching for 10 minutes eliminates redundant DB hits every time a
# form opens — especially noticeable when LAN clients hit the server.
_TTL = 600  # seconds
_master_cache: dict = {}  # key → (data, expiry_timestamp)

def _cache_get(key: str):
    entry = _master_cache.get(key)
    if entry and time.monotonic() < entry[1]:
        return entry[0]
    return None

def _cache_set(key: str, data):
    _master_cache[key] = (data, time.monotonic() + _TTL)

def _cache_bust(key: str):
    _master_cache.pop(key, None)

def bust_all_master_caches():
    """Call after any bulk import / restore that touches master tables."""
    _master_cache.clear()

# ── Dependency ──
# Anyone active can read, but standard creates/updates require admin or DC/AC based on legacy rules.

# ── DC Master ────────────────────────────────────────────────────
@router.get("/dc", response_model=List[schemas.DcMasterOut])
def get_dcs(db: Session = Depends(get_db)):
    cached = _cache_get("dc")
    if cached is not None:
        return cached
    rows = db.query(DcMaster).filter(DcMaster.dc_status == "Active").all()
    result = [schemas.DcMasterOut.model_validate(r) for r in rows]
    _cache_set("dc", result)
    return result

@router.post("/dc", response_model=schemas.DcMasterOut)
def create_dc(data: schemas.DcMasterCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    db_obj = DcMaster(**data.model_dump())
    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        _cache_bust("dc")
        return db_obj
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data Already Available or Error")


# ── Airlines Master ──────────────────────────────────────────────
@router.get("/airlines", response_model=List[schemas.AirlinesMastOut])
def get_airlines(db: Session = Depends(get_db)):
    cached = _cache_get("airlines")
    if cached is not None:
        return cached
    rows = db.query(AirlinesMast).all()
    result = [schemas.AirlinesMastOut.model_validate(r) for r in rows]
    _cache_set("airlines", result)
    return result

@router.post("/airlines", response_model=schemas.AirlinesMastOut)
def create_airline(data: schemas.AirlinesMastCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    db_obj = AirlinesMast(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    _cache_bust("airlines")
    return db_obj


# ── Flight Master ────────────────────────────────────────────────
@router.get("/flights", response_model=List[schemas.ArrivalFlightMasterOut])
def get_flights(db: Session = Depends(get_db)):
    cached = _cache_get("flights")
    if cached is not None:
        return cached
    rows = db.query(ArrivalFlightMaster).all()
    result = [schemas.ArrivalFlightMasterOut.model_validate(r) for r in rows]
    _cache_set("flights", result)
    return result

@router.post("/flights", response_model=schemas.ArrivalFlightMasterOut)
def create_flight(data: schemas.ArrivalFlightMasterCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    db_obj = ArrivalFlightMaster(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    _cache_bust("flights")
    return db_obj


# ── Airport Master ───────────────────────────────────────────────
@router.get("/airport", response_model=List[schemas.AirportMasterOut])
def get_airports(db: Session = Depends(get_db)):
    return db.query(AirportMaster).all()

@router.post("/airport/close_all")
def close_all_airports(db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    """Legacy feature: update airport_master set airport_status='Closed' where airport_status='Active'"""
    db.query(AirportMaster).filter(AirportMaster.airport_status == 'Active').update({"airport_status": "Closed"})
    db.commit()
    return {"message": "All airports closed successfully"}


# ── Nationality Master (Server-Only capability) ──────────────────
@router.get("/nationalities", response_model=List[schemas.NationalityMasterOut])
def get_nationalities(db: Session = Depends(get_db)):
    cached = _cache_get("nationalities")
    if cached is not None:
        return cached
    rows = db.query(NationalityMaster).all()
    result = [schemas.NationalityMasterOut.model_validate(r) for r in rows]
    _cache_set("nationalities", result)
    return result

@router.post("/nationalities", response_model=schemas.NationalityMasterOut)
def create_nationality(data: schemas.NationalityMasterCreate, db: Session = Depends(get_db), _: User = Depends(get_dc_ac_user)):
    """Server-only capability requires DC/AC or Admin."""
    db_obj = NationalityMaster(**data.model_dump())
    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        _cache_bust("nationalities")
        return db_obj
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Nationality already exists")


# ── Item Category Master ─────────────────────────────────────────
@router.get("/item_categories", response_model=List[schemas.ItemCatMasterOut])
def get_item_categories(db: Session = Depends(get_db)):
    cached = _cache_get("item_categories")
    if cached is not None:
        return cached
    rows = db.query(ItemCatMaster).filter(ItemCatMaster.active_ind == "A").all()
    result = [schemas.ItemCatMasterOut.model_validate(r) for r in rows]
    _cache_set("item_categories", result)
    return result

@router.post("/item_categories", response_model=schemas.ItemCatMasterOut)
def create_item_category(data: schemas.ItemCatMasterCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    db_obj = ItemCatMaster(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    _cache_bust("item_categories")
    return db_obj

@router.put("/item_categories/{category_code}/deactivate")
def deactivate_item_category(category_code: str, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    item = db.query(ItemCatMaster).filter(ItemCatMaster.category_code == category_code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    item.active_ind = "C"
    db.commit()
    _cache_bust("item_categories")
    return {"message": "Category deactivated"}


# ── Duty Rate Master ─────────────────────────────────────────────
@router.get("/duty_rates", response_model=List[schemas.DutyRateMasterOut])
def get_duty_rates(db: Session = Depends(get_db)):
    cached = _cache_get("duty_rates")
    if cached is not None:
        return cached
    rows = db.query(DutyRateMaster).filter(DutyRateMaster.active_ind == "A").all()
    result = [schemas.DutyRateMasterOut.model_validate(r) for r in rows]
    _cache_set("duty_rates", result)
    return result

@router.post("/duty_rates", response_model=schemas.DutyRateMasterOut)
def create_duty_rate(data: schemas.DutyRateMasterCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    db_obj = DutyRateMaster(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    _cache_bust("duty_rates")
    return db_obj

@router.put("/duty_rates/{id}/deactivate")
def deactivate_duty_rate(id: int, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    dr = db.query(DutyRateMaster).filter(DutyRateMaster.id == id).first()
    if not dr:
        raise HTTPException(status_code=404, detail="Duty rate not found")
    dr.active_ind = "C"
    dr.to_date = date.today()
    db.commit()
    _cache_bust("duty_rates")
    return {"message": "Duty rate deactivated"}


# ── BR Limits Master ─────────────────────────────────────────────
@router.get("/br_limits", response_model=List[schemas.BrNoLimitsOut])
def get_br_limits(db: Session = Depends(get_db)):
    cached = _cache_get("br_limits")
    if cached is not None:
        return cached
    rows = db.query(BrNoLimits).all()
    result = [schemas.BrNoLimitsOut.model_validate(r) for r in rows]
    _cache_set("br_limits", result)
    return result

@router.post("/br_limits", response_model=schemas.BrNoLimitsOut)
def create_br_limit(data: schemas.BrNoLimitsCreate, db: Session = Depends(get_db), _: User = Depends(get_adjn_user)):
    db_obj = BrNoLimits(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    _cache_bust("br_limits")
    return db_obj
