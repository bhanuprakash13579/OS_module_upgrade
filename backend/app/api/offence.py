from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, cast, Integer as SAInteger, exists, not_, text
from collections import defaultdict

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user, get_dc_ac_user, get_sdo_user, get_adjn_user
from app.models.offence import CopsMaster, CopsItems, OsMaster
from app.models.audit import CopsMasterDeleted
from app.models.config import BatchMaster
import app.schemas.offence as schemas
from app.config import settings
from app.services.rules_engine import BusinessRulesEngine

router = APIRouter()


# ── Free-allowance helper ─────────────────────────────────────────────────────
def _eff_fa(item_value: float, item) -> float:
    """
    Effective monetary FA deduction for an item.
    - qty-mode: proportional deduction = (fa_qty / total_qty) * item_value
    - value-mode: direct monetary FA stored in items_fa
    FA applies to 'Under Duty' items (reduces dutiable value) and
    'Under OS' items (reduces the total seized value shown in the OS).
    """
    cat = (getattr(item, 'items_release_category', None) or '').upper()
    if cat not in ('UNDER DUTY', 'UNDER OS', 'RF', 'REF'):
        return 0.0
    if (getattr(item, 'items_fa_type', None) or 'value') == 'qty':
        total_qty = float(getattr(item, 'items_qty', 0) or 0)
        fa_qty    = float(getattr(item, 'items_fa_qty', 0) or 0)
        return min((fa_qty / total_qty) * item_value, item_value) if total_qty > 0 else 0.0
    return float(getattr(item, 'items_fa', 0) or 0)


# ── Smart item classifier ─────────────────────────────────────────────────────
from app.services.classifier import classify as _classify

@router.get("/classify-item")
def classify_item(description: str):
    """
    Given a free-text item description, return the best-matching duty_type
    string and a suggested UQC. No auth required (read-only intelligence).
    """
    return _classify(description)


# ── Item description autocomplete ─────────────────────────────────────────────
import threading as _threading
import time as _time
_item_desc_cache: list[str] = []
_item_desc_cache_ts: float = 0.0
_item_desc_lock = _threading.Lock()

@router.get("/item-descriptions")
def get_item_descriptions(db: Session = Depends(get_db)):
    """
    Return a deduplicated, frequency-sorted list of item descriptions from the
    database for use as autocomplete suggestions in the frontend.
    Results are cached in-process for 5 minutes to avoid repeated DB hits.
    No auth required (read-only, no sensitive data).
    """
    global _item_desc_cache, _item_desc_cache_ts
    now = _time.time()
    with _item_desc_lock:
        if _item_desc_cache and (now - _item_desc_cache_ts) < 300:
            return _item_desc_cache

    rows = (
        db.query(
            CopsItems.items_desc,
            func.count(CopsItems.items_desc).label("cnt")
        )
        .filter(CopsItems.items_desc.isnot(None), CopsItems.items_desc != '')
        .group_by(func.upper(CopsItems.items_desc))
        .order_by(func.count(CopsItems.items_desc).desc())
        .limit(300)
        .all()
    )

    seen: set[str] = set()
    result: list[str] = []
    for row in rows:
        val = (row[0] or '').strip().upper()
        if val and val not in seen:
            seen.add(val)
            result.append(val)

    with _item_desc_lock:
        _item_desc_cache = result
        _item_desc_cache_ts = now
    return result


def _attach_items(records: list, db: Session) -> list:
    """
    Bulk-load CopsItems for a list of CopsMaster records in ONE query (N+1 fix).
    Uses a JOIN on master IDs to avoid SQLite's expression-tree depth limit (max 1000)
    that was hit when building a huge OR chain over 2000+ (os_no, os_year) pairs.
    """
    if not records:
        return records
    master_ids = list({r.id for r in records})
    # Chunk IN clause to stay well under SQLite's variable limit (~999)
    _CHUNK = 900
    all_items: list = []
    for i in range(0, len(master_ids), _CHUNK):
        chunk = master_ids[i:i + _CHUNK]
        rows = (
            db.query(CopsItems)
            .join(CopsMaster, and_(CopsItems.os_no == CopsMaster.os_no,
                                   CopsItems.os_year == CopsMaster.os_year))
            .filter(CopsMaster.id.in_(chunk))
            .all()
        )
        all_items.extend(rows)
    items_map: dict = defaultdict(list)
    for item in all_items:
        items_map[(item.os_no, item.os_year)].append(item)
    for r in records:
        r.items = items_map.get((r.os_no, r.os_year), [])
    return records


def get_current_batch(db: Session):
    batch = db.query(BatchMaster).first()
    if not batch or not batch.current_batch_date:
        return date.today(), "Day"
    return batch.current_batch_date, batch.current_batch_shift

def generate_os_number(db: Session, os_date: date) -> str:
    """
    Legacy helper retained for compatibility with OsMaster.
    Not used anymore because O.S. No. is now fully user-entered.
    """
    max_no = (
        db.query(func.max(OsMaster.osnumber))
        .filter(func.extract('year', OsMaster.osdate) == os_date.year)
        .scalar()
    )
    new_no = (max_no or 0) + 1
    db.add(OsMaster(osdate=os_date, osnumber=new_no))
    db.commit()
    return str(new_no)


# ── SDO: Check O/S No. uniqueness per year ───────────────────────────────────
@router.get("/check-os-no/{os_no}/{os_year}")
def check_os_no(
    os_no: str,
    os_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sdo_user)
):
    """Check if an O.S. No. already exists for the given year."""
    existing = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()
    return {"exists": existing is not None}

# ── SDO: Create O/S Case ─────────────────────────────────────────────────────
@router.post("/", response_model=schemas.CopsMasterOut)
def create_os(
    data: schemas.CopsMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sdo_user)   # SDO module only
):
    """SDO Module: Register a new Offence / Seizure case."""
    rules = BusinessRulesEngine(db)
    batch_date, batch_shift = get_current_batch(db)

    data.passport_no = rules.normalize_passport(data.passport_no)

    if data.is_draft != "Y":
        if data.flight_date:
            rules.validate_flight_date(data.flight_date, batch_date)
        rules.validate_pax_dates(data.pax_date_of_birth, data.flight_date, batch_date)

    # Determine effective O.S. date:
    # - if user supplied an os_date, honor it (after validation),
    # - otherwise fall back to current batch date.
    os_date = data.os_date or batch_date

    # O.S. No is now fully user-entered; validate and ensure uniqueness per year
    if not data.os_no or not str(data.os_no).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O.S. No. is required and must be entered by the user."
        )

    os_no = str(data.os_no).strip()
    if not os_no.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O.S. No. must contain digits only."
        )

    os_year = os_date.year

    existing = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O.S. No. {os_no}/{os_year} already exists."
        )

    # Recalculate item duties on the backend for consistency and security
    # Free allowance applies to "Under Duty" goods (reduces dutiable value) and "Under OS" goods (reduces seized value)
    total_val = 0.0
    total_duty = 0.0
    for item in data.items:
        item_value = float(item.items_value or 0.0)
        fa = _eff_fa(item_value, item)
        rate = float(item.cumulative_duty_rate or 0.0)
        duty = max(0.0, (item_value - fa)) * rate / 100.0
        total_val += item_value
        total_duty += duty
    total_items = len(data.items)

    # NOTE: os_no and os_year are passed explicitly, so exclude them from the Pydantic dump
    os_obj = CopsMaster(
        os_no=os_no,
        os_date=os_date,
        os_year=os_year,
        total_items=total_items,
        total_items_value=total_val,
        total_duty_amount=total_duty,
        total_payable=total_duty,
        # Exclude fields we set explicitly above
        **data.model_dump(exclude={"items", "os_no", "os_year", "os_date"})
    )

    db.add(os_obj)
    db.commit()
    db.refresh(os_obj)

    for c_item in data.items:
        item_value = float(c_item.items_value or 0.0)
        fa = _eff_fa(item_value, c_item)
        rate = float(c_item.cumulative_duty_rate or 0.0)
        duty = max(0.0, (item_value - fa)) * rate / 100.0

        db_item = CopsItems(
            os_no=os_no,
            os_date=os_obj.os_date,
            os_year=os_year,
            items_duty=duty,
            **c_item.model_dump(exclude={"items_duty"})
        )
        db.add(db_item)

    db.commit()
    return os_obj


# ── Search Old Passports ──────────────────────────────────────────────────────
@router.get("/passports/search")
def search_old_passports(
    name: str,
    dob: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find all passport numbers ever associated with this passenger.

    Uses the same two-step strategy as the APIS→COPS matcher:
      1. Exact DOB filter  — narrows to a tiny candidate set cheaply
      2. Fuzzy name match  — token-overlap ≥ 60% handles spelling
                             variations, initials, reversed name order

    This catches cases where the same passenger has renewed their
    passport (new number, same DOB, same/similar name).
    """
    from app.services.apis_match import _name_score, _NAME_THRESHOLD

    # Step 1 — exact DOB (cheap, uses date column); cap at 500 to bound
    # the fuzzy-name loop in Step 2 on pathological data (e.g. DOB = 01-01-1990)
    candidates = db.query(CopsMaster).filter(
        CopsMaster.pax_date_of_birth == dob,
        CopsMaster.entry_deleted == "N"
    ).limit(500).all()

    # Step 2 — fuzzy name score on the small candidate set (in Python, no extra DB hit)
    found_passports = set()
    for rec in candidates:
        if _name_score(name, rec.pax_name or '') >= _NAME_THRESHOLD:
            if rec.passport_no:
                found_passports.add(rec.passport_no.strip())
            if rec.old_passport_no:
                for op in rec.old_passport_no.split(";"):
                    if op.strip():
                        found_passports.add(op.strip())

    return {"passports": list(found_passports)}


# ── SDO: List All O/S Cases ───────────────────────────────────────────────────
@router.get("/", response_model=schemas.CopsMasterPagedOut)
def get_all_os(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query('', max_length=200),
    year: int = Query(None),
    status: str = Query(None),
):
    """All active users: OS case list with server-side pagination, search, and filters."""
    q = db.query(CopsMaster).filter(CopsMaster.entry_deleted == "N")
    if search.strip():
        s = f"%{search.strip()}%"
        q = q.filter(or_(
            CopsMaster.os_no.ilike(s),
            CopsMaster.pax_name.ilike(s),
            CopsMaster.passport_no.ilike(s),
            CopsMaster.flight_no.ilike(s),
        ))
    if year:
        q = q.filter(CopsMaster.os_year == year)
    if status:
        sl = status.lower()
        if sl == 'draft':
            q = q.filter(CopsMaster.is_draft == 'Y')
        elif sl == 'adjudicated':
            # Adjudicated = any case that officially has an adjudication_date, 
            # OR (for legacy MDB cases) has no items awaiting adjudication.
            pending_items_subq = exists().where(
                and_(
                    CopsItems.os_no == CopsMaster.os_no,
                    CopsItems.os_year == CopsMaster.os_year,
                    CopsItems.items_release_category.in_(['Under OS', 'Under Duty'])
                )
            )
            q = q.filter(
                CopsMaster.is_draft == 'N',
                CopsMaster.quashed != 'Y',
                CopsMaster.rejected != 'Y',
                or_(
                    CopsMaster.adjudication_date.isnot(None),
                    not_(pending_items_subq)
                )
            )
        elif sl == 'pending':
            # Pending = NO adjudication date AND has items awaiting adjudication
            pending_items_subq = exists().where(
                and_(
                    CopsItems.os_no == CopsMaster.os_no,
                    CopsItems.os_year == CopsMaster.os_year,
                    CopsItems.items_release_category.in_(['Under OS', 'Under Duty'])
                )
            )
            q = q.filter(
                CopsMaster.is_draft == 'N',
                CopsMaster.adjudication_date.is_(None),
                CopsMaster.quashed != 'Y',
                CopsMaster.rejected != 'Y',
                pending_items_subq,
            )
        elif sl == 'quashed':
            q = q.filter(or_(CopsMaster.quashed == 'Y', CopsMaster.rejected == 'Y'))
    total = q.count()
    records = q.order_by(
        CopsMaster.os_year.desc(),
        cast(CopsMaster.os_no, SAInteger).desc()
    ).offset((page - 1) * per_page).limit(per_page).all()
    # List view uses total_items from master — no item join needed
    for r in records:
        r.items = []
    return {"total": total, "page": page, "per_page": per_page, "items": records}


# ── Adjudication Module: Pending Count (lightweight — sidebar badge) ─────────
@router.get("/pending/count")
def get_pending_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """Returns only the pending case count — single SQL COUNT, no item joins."""
    pending_items_subq = exists().where(
        and_(
            CopsItems.os_no == CopsMaster.os_no,
            CopsItems.os_year == CopsMaster.os_year,
            CopsItems.items_release_category.in_(['Under OS', 'Under Duty'])
        )
    )
    count = db.query(func.count(CopsMaster.id)).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_draft == "N",
        CopsMaster.adjudication_date.is_(None),
        CopsMaster.quashed != "Y",
        CopsMaster.rejected != "Y",
        pending_items_subq,
    ).scalar()
    return {"count": count or 0}


# ── Adjudication Module: Pending Cases ───────────────────────────────────────
@router.get("/pending", response_model=List[schemas.CopsMasterOut])
def get_pending_adjudication(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)  # Adjudication module only
):
    """Adjudication Module: O/S cases awaiting adjudication."""
    pending_items_subq = exists().where(
        and_(
            CopsItems.os_no == CopsMaster.os_no,
            CopsItems.os_year == CopsMaster.os_year,
            CopsItems.items_release_category.in_(['Under OS', 'Under Duty'])
        )
    )
    records = db.query(CopsMaster).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_draft == "N",
        CopsMaster.adjudication_date.is_(None),
        CopsMaster.adj_offr_name.is_(None),
        CopsMaster.quashed != "Y",
        CopsMaster.rejected != "Y",
        pending_items_subq,
    ).order_by(CopsMaster.os_year.desc(), cast(CopsMaster.os_no, SAInteger).desc()).limit(200).all()
    # List view only needs master-level fields — skip item join for performance
    for r in records:
        r.items = []
    return records


# ── Adjudication Module: Adjudicated Cases ────────────────────────────────────
@router.get("/adjudicated", response_model=List[schemas.CopsMasterOut])
def get_adjudicated_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)  # Adjudication module only
):
    """Adjudication Module: Already-adjudicated O/S cases."""
    records = db.query(CopsMaster).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_draft == "N",
        CopsMaster.adjudication_date.isnot(None),
        CopsMaster.quashed != "Y",
        CopsMaster.rejected != "Y"
    ).order_by(CopsMaster.adjudication_date.desc()).limit(200).all()
    for r in records:
        r.items = []
    return records

# ── Adjudication Module: Quashed/Rejected Cases ──────────────────────────────
@router.get("/quashed", response_model=List[schemas.CopsMasterOut])
def get_quashed_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """Adjudication Module: Cases that were Quashed or Rejected."""
    records = db.query(CopsMaster).filter(
        CopsMaster.entry_deleted == "N",
        (CopsMaster.quashed == "Y") | (CopsMaster.rejected == "Y")
    ).order_by(CopsMaster.os_date.desc()).limit(200).all()
    for r in records:
        r.items = []
    return records



# ── Get Single O/S Case ───────────────────────────────────────────────────────
@router.get("/{os_no}/{os_year}", response_model=schemas.CopsMasterOut)
def get_os(
    os_no: str,
    os_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).order_by(CopsMaster.id.desc()).first()

    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found.")

    os_obj.items = db.query(CopsItems).filter(
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).all()
    return os_obj


# ── SDO: Modify O/S Case ──────────────────────────────────────────────────────
@router.put("/{os_no}/{os_year}", response_model=schemas.CopsMasterOut)
def update_os(
    os_no: str,
    os_year: int,
    data: schemas.CopsMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sdo_user)   # SDO module only
):
    """SDO Module: Modify an existing O/S case (only if not yet adjudicated)."""
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()

    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found.")

    if os_obj.os_printed == 'Y':
        raise HTTPException(
            status_code=400,
            detail="Print Out Has Already Been Taken for The Entered O.S.No. Cannot Modify its details !"
        )

    if os_obj.adjudication_date:
        raise HTTPException(
            status_code=400,
            detail="Modification Not Allowed: This O/S No. has already been adjudicated. Contact System Administrator !"
        )

    # Update master fields (do not allow changing O.S. No / Year via payload)
    update_data = data.model_dump(exclude={"items", "os_no", "os_year"})
    for key, value in update_data.items():
        setattr(os_obj, key, value)

    # Recalculate items and totals on the backend
    # Free allowance applies to "Under Duty" goods (reduces dutiable value) and "Under OS" goods (reduces seized value)
    total_val = 0.0
    total_duty = 0.0
    for item in data.items:
        item_value = float(item.items_value or 0.0)
        fa = _eff_fa(item_value, item)
        rate = float(item.cumulative_duty_rate or 0.0)
        duty = max(0.0, (item_value - fa)) * rate / 100.0
        total_val += item_value
        total_duty += duty

    os_obj.total_items_value = total_val
    os_obj.total_duty_amount = total_duty
    os_obj.total_payable = total_duty
    os_obj.total_items = len(data.items)

    # Replace items: flush pending session state first, then bulk-delete with
    # synchronize_session=False to avoid the ORM identity-map sync skipping the DELETE
    # (autoflush=False on the session means we must flush manually before bulk ops)
    db.flush()
    db.query(CopsItems).filter(
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).delete(synchronize_session=False)

    for c_item in data.items:
        item_value = float(c_item.items_value or 0.0)
        fa = _eff_fa(item_value, c_item)
        rate = float(c_item.cumulative_duty_rate or 0.0)
        duty = max(0.0, (item_value - fa)) * rate / 100.0

        db_item = CopsItems(
            os_no=os_no,
            os_date=os_obj.os_date,
            os_year=os_year,
            items_duty=duty,
            **c_item.model_dump(exclude={"items_duty"})
        )
        db.add(db_item)

    db.commit()
    db.refresh(os_obj)
    os_obj.items = db.query(CopsItems).filter(
        CopsItems.os_no == os_no, CopsItems.os_year == os_year
    ).all()
    return os_obj


# ── Mark OS as Printed (Print Lock) ───────────────────────────────────────────
@router.post("/{os_no}/{os_year}/mark-printed")
def mark_printed(
    os_no: str,
    os_year: int,
    db: Session = Depends(get_db),
):
    """Mark an O/S case as printed, locking it from further SDO modification."""
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()
    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found.")
    if os_obj.os_printed != 'Y':
        os_obj.os_printed = 'Y'
        db.commit()
    return {"message": "O.S. marked as printed.", "os_no": os_no, "os_year": os_year}


# ── Print O/S as PDF (WeasyPrint, legal size) ────────────────────────────────
@router.get("/{os_no}/{os_year}/print-pdf")
def print_os_pdf(
    os_no: str,
    os_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a legal-size, two-page PDF of the OS booking + adjudication order."""
    import os as _os
    from pathlib import Path
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML as WeasyHTML
    from fastapi.responses import Response

    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()
    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found.")

    items_db = db.query(CopsItems).filter(
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).order_by(CopsItems.items_sno).all()

    # ── helpers ──────────────────────────────────────────────────────────────
    def fmt_date(d) -> str:
        if not d:
            return "—"
        try:
            from datetime import date as _date
            if isinstance(d, _date):
                return d.strftime("%d/%m/%Y")
            return str(d)
        except Exception:
            return str(d)

    def fmt_indian(n) -> str:
        """Format number in Indian style: 3,26,914 instead of 326,914."""
        if n is None:
            return "0"
        n_int = int(round(float(n)))
        if n_int == 0:
            return "0"
        s = str(abs(n_int))
        if len(s) <= 3:
            return s
        result = s[-3:]
        s = s[:-3]
        parts = []
        while len(s) > 2:
            parts.append(s[-2:])
            s = s[:-2]
        if s:
            parts.append(s)
        return ",".join(reversed(parts)) + "," + result

    def fmt_num(n) -> str:
        """Format for record table cells — blank when zero."""
        if n is None or n == 0:
            return ""
        return fmt_indian(n)

    def num_to_words(num: int) -> str:
        if num == 0:
            return "Zero"
        a = ["", "one ", "two ", "three ", "four ", "five ", "six ", "seven ",
             "eight ", "nine ", "ten ", "eleven ", "twelve ", "thirteen ",
             "fourteen ", "fifteen ", "sixteen ", "seventeen ", "eighteen ", "nineteen "]
        b = ["", "", "twenty", "thirty", "forty", "fifty",
             "sixty", "seventy", "eighty", "ninety"]
        if num < 20:
            return a[num]
        if num < 100:
            return b[num // 10] + ((" " + a[num % 10]) if num % 10 else "")
        if num < 1000:
            return a[num // 100] + "hundred" + ((" and " + num_to_words(num % 100)) if num % 100 else "")
        if num < 100000:
            return num_to_words(num // 1000) + " thousand" + ((" " + num_to_words(num % 1000)) if num % 1000 else "")
        if num < 10000000:
            return num_to_words(num // 100000) + " lakh" + ((" " + num_to_words(num % 100000)) if num % 100000 else "")
        return num_to_words(num // 10000000) + " crore" + ((" " + num_to_words(num % 10000000)) if num % 10000000 else "")

    def title_words(n: float) -> str:
        return num_to_words(int(n)).strip().title()

    def day_or_night(shift: str | None) -> str:
        if not shift:
            return ""
        s = shift.upper()
        if any(x in s for x in ("A", "B", "DAY")):
            return "(D)"
        if any(x in s for x in ("C", "D", "NIGHT")):
            return "(N)"
        return ""

    # ── UQC abbreviation → readable label ────────────────────────────────────
    _UQC_LABEL = {
        "NOS": "Nos.", "STK": "Sticks", "KGS": "Kgs.",
        "GMS": "Gms.", "LTR": "Ltrs.", "MTR": "Mtrs.", "PRS": "Pairs",
    }
    def uqc_label(code: str) -> str:
        return _UQC_LABEL.get((code or "").upper(), code or "Nos.")

    # ── Item rows + summary totals (single pass) ─────────────────────────────
    item_rows = []
    LIABLE_CATS = ["CONFS", "ABS_CONFS", "RE_EXP", "RF", "REF", "UNDER OS"]
    FA_SUM_CATS = {"UNDER DUTY", "UNDER OS", "RF", "REF"}
    total_fa = 0.0
    total_fa_monetary = 0.0
    total_dutiable = 0.0
    total_liable_value = 0.0
    rf_val_items = 0.0
    ref_val_items = 0.0
    confs_val_items = 0.0
    qty_fa_list = []
    for idx, item in enumerate(items_db):
        cat = (item.items_release_category or "UNDER OS").upper()
        # "Liable" = Under OS + RF + REF + CONFS
        is_liable = cat in LIABLE_CATS
        is_duty = cat == "UNDER DUTY"
        is_confs = cat == "CONFS"

        val = float(item.items_value or 0)
        vpu = float(item.value_per_piece or 0)
        fa = _eff_fa(val, item)
        dutiable = max(0, val - fa)
        fa_type = (item.items_fa_type or 'value')
        qty = float(item.items_qty or 0)

        # Accumulate summary totals in this same pass
        if cat in FA_SUM_CATS:
            total_fa += fa
            if fa_type == 'value':
                total_fa_monetary += fa
            fa_qty_val = float(item.items_fa_qty or 0)
            if fa_type == 'qty' and fa_qty_val > 0:
                qty_fa_list.append(
                    f"{fa_qty_val:g} {_UQC_LABEL.get((item.items_fa_uqc or '').upper(), item.items_fa_uqc or 'Nos.')} of {item.items_desc}"
                )
        if is_duty:
            total_dutiable += dutiable
        if is_liable:
            total_liable_value += dutiable
        if cat == "RF":
            rf_val_items += dutiable
        elif cat == "REF":
            ref_val_items += dutiable
        elif cat == "CONFS":
            confs_val_items += dutiable

        # FA display: show for Under Duty and Under OS/RF/REF items (but not CONFS)
        show_fa = is_duty or (is_liable and not is_confs)
        if not show_fa:
            fa_disp = "—"
        elif fa_type == 'qty':
            fa_qty = item.items_fa_qty
            fa_uqc_label = uqc_label(item.items_fa_uqc or '')
            fa_disp = f"{fa_qty:g} {fa_uqc_label}".strip() if fa_qty else "—"
        else:
            fa_disp = fmt_indian(fa) if fa > 0 else "—"

        item_rows.append({
            "items_desc": item.items_desc,
            "items_qty": f"{qty:g}",
            "items_uqc": uqc_label(item.items_uqc or ''),
            "cumulative_duty_rate": int(item.cumulative_duty_rate or 0),
            "cat_upper": cat,
            "fa_display":    fa_disp,
            "duty_display":  (fmt_indian(dutiable) if is_duty and dutiable > 0 else "—"),
            "vpu_display":   (fmt_indian(vpu) if is_liable and vpu else "—"),
            "total_display": (fmt_indian(dutiable) if is_liable else "—"),
        })

    qty_fa_str = " & ".join(qty_fa_list)
    total_items_value = total_liable_value if total_liable_value > 0 else float(os_obj.total_items_value or 0)

    # ── Adjudication Case Values (Prioritize Master Record) ──────────────────
    # For new cases, adjudicators manually input redeemed_value and re_export_value at the case level.
    # We fallback to summing item categories for older data where these case-level values might be zero.
    master_redeemed = float(os_obj.redeemed_value or 0)
    master_re_export = float(os_obj.re_export_value or 0)
    master_confs = float(os_obj.confiscated_value or 0)

    # Serial numbers grouped by disposal category (for ORDER paragraph)
    rf_slnos = [str(idx + 1) for idx, i in enumerate(items_db) if (i.items_release_category or "Under OS") == "RF"]
    ref_slnos = [str(idx + 1) for idx, i in enumerate(items_db) if (i.items_release_category or "Under OS") == "REF"]
    confs_slnos = [str(idx + 1) for idx, i in enumerate(items_db) if (i.items_release_category or "Under OS") == "CONFS"]

    # Use master values if they exist, else fallback to item summation (for old un-migrated data)
    has_item_data = len(items_db) > 0
    conf_value = master_redeemed if master_redeemed > 0 else (rf_val_items if has_item_data else 0)
    re_exp_value = master_re_export if master_re_export > 0 else ref_val_items
    abs_conf_value = master_confs if master_confs > 0 else confs_val_items

    # Fines and Penalties
    rf_amount  = float(os_obj.rf_amount or 0)
    ref_amount = float(os_obj.ref_amount or 0)
    pp_amount  = float(os_obj.pp_amount or 0)

    # RF items with zero redemption fine → treat as absolute confiscation
    if rf_amount == 0 and conf_value > 0:
        abs_conf_value += conf_value
        conf_value = 0

    # When RF items move to abs conf, merge their sl.nos
    if rf_amount == 0 and rf_slnos:
        all_abs_conf_slnos = sorted(confs_slnos + rf_slnos, key=lambda x: int(x))
    else:
        all_abs_conf_slnos = confs_slnos

    # ── Logo path (absolute file:// URL for WeasyPrint) ──────────────────────
    frontend_public = Path(__file__).parent.parent.parent.parent / "frontend" / "public"
    logo_file = frontend_public / "customs-logo.jpg"
    logo_path = logo_file.as_uri() if logo_file.exists() else ""

    # ── Render template ───────────────────────────────────────────────────────
    templates_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    tmpl = env.get_template("os_print.html")

    # ── Point-in-time versioned config (based on OS date) ────────────────────
    from app.api.admin_api import _pit_config
    ref_date = os_obj.os_date if os_obj.os_date else date.today()
    pit = _pit_config(db, ref_date)
    ptc = pit["print_template"]
    def _ptc(key: str, fallback: str) -> str:
        row = ptc.get(key)
        return row["field_value"] if row else fallback

    class _SafeDict(dict):
        def __missing__(self, key: str):
            return "{" + key + "}"

    def _render_para(tpl: str, **kw: object) -> str:
        """Substitute {placeholder} values into an ORDER paragraph template."""
        return tpl.format_map(_SafeDict(kw))

    def _slnos_text(slnos: list) -> str:
        return f" at Sl.No(s). {', '.join(str(s) for s in slnos)}" if slnos else ""

    # ── Prev. offence + other PP offences (mirrors updated frontend logic) ────
    all_other_records = db.query(CopsMaster).filter(
        func.lower(CopsMaster.pax_name) == func.lower(os_obj.pax_name or ""),
        CopsMaster.entry_deleted == "N",
        ~((CopsMaster.os_no == os_no) & (CopsMaster.os_year == os_year))
    ).limit(50).all()

    current_os_date = os_obj.os_date  # date object

    # Same passport, before current OS date → "Prev. Offence in Above PP No(s)."
    same_pp_prior = [
        r for r in all_other_records
        if r.passport_no == os_obj.passport_no
        and r.os_date is not None
        and r.os_date < current_os_date
    ]
    same_pp_prior.sort(key=lambda r: r.os_date, reverse=True)  # newest first

    if same_pp_prior:
        os_list = ", ".join(f"{r.os_no}/{r.os_year}" for r in same_pp_prior)
        prev_offence_display = f"{len(same_pp_prior)} ({os_list})"
    else:
        # Fall back to legacy DB field
        prev_offence_display = (os_obj.previous_visits or "NIL").strip()

    # Different passport, same pax name → "Offences of Other PPs(if any)"
    other_pp_records = [r for r in all_other_records if r.passport_no != os_obj.passport_no]
    other_pp_offences = ", ".join(
        f"{r.passport_no} (OS {r.os_no}/{r.os_year})" for r in other_pp_records
    ) if other_pp_records else "NIL"

    pax_address = ", ".join(filter(None, [os_obj.pax_address1, os_obj.pax_address2, os_obj.pax_address3]))
    template_vars = dict(
        # Versioned headings
        col_fa_heading=_ptc("col_fa_heading",
            "Goods Allowed Free Under Rule 5 / Rule 13 of Baggage Rules, 1994"),
        col_liable_heading=_ptc("col_liable_heading",
            "Goods Liable to Action Under FEMA / Foreign Trade Act, 1992 & Customs Act, 1962"),
        summary_duty_text=_ptc("summary_duty_text",
            "Value of Goods Charged to Duty Under Foreign Trade (D&R) Act, 1992 & Customs Act, 1962"),
        summary_liable_text=_ptc("summary_liable_text",
            "Value of Goods Liable to Action under FEMA / Foreign Trade (D&R) Act, 1992 & Customs Act 1962"),
        os_no=os_obj.os_no,
        os_year=os_obj.os_year,
        booked_by=os_obj.booked_by or "AIU",
        os_date=fmt_date(os_obj.os_date),
        detention_date=fmt_date(os_obj.detention_date or os_obj.os_date),
        pax_name=os_obj.pax_name or "",
        father_name=os_obj.father_name or "",
        pax_address=pax_address,
        passport_no=os_obj.passport_no or "",
        passport_date=fmt_date(os_obj.passport_date),
        flight_no=os_obj.flight_no or "",
        flight_date=fmt_date(os_obj.flight_date),
        port_or_country=os_obj.port_of_dep_dest or os_obj.country_of_departure or "—",
        nationality=os_obj.nationality or os_obj.pax_nationality or "—",
        date_of_departure=os_obj.date_of_departure or "N.A.",
        stay_abroad_days=os_obj.stay_abroad_days or 0,
        residence_at=os_obj.residence_at or os_obj.country_of_departure or "ABROAD",
        previous_visits=os_obj.previous_visits or "NIL",
        items=item_rows,
        total_items_value_fmt=fmt_indian(total_items_value),
        total_fa_fmt=fmt_indian(total_fa_monetary),
        total_fa=total_fa_monetary,
        qty_fa_list=qty_fa_str,
        total_dutiable_fmt=fmt_indian(total_dutiable),
        prev_offence_display=prev_offence_display,
        other_pp_offences=other_pp_offences,
        supdts_remarks=os_obj.supdts_remarks or "",
        # Page 2
        day_or_night=day_or_night(os_obj.shift or os_obj.booked_by),
        adj_offr_name=os_obj.adj_offr_name or "__________________________",
        adj_offr_designation=os_obj.adj_offr_designation or "Deputy/Asst.Commr.",
        adjudication_date=fmt_date(os_obj.adjudication_date or os_obj.os_date),
        adjn_offr_remarks=os_obj.adjn_offr_remarks or "No remarks provided.",
        conf_value=int(conf_value),
        re_exp_value=int(re_exp_value),
        abs_conf_value=int(abs_conf_value),
        rf_slnos=", ".join(rf_slnos),
        ref_slnos=", ".join(ref_slnos),
        confs_slnos=", ".join(all_abs_conf_slnos),
        rf_amount=int(rf_amount),
        ref_amount=int(ref_amount),
        pp_amount=int(pp_amount),
        rf_words=title_words(rf_amount),
        ref_words=title_words(ref_amount),
        pp_words=title_words(pp_amount),
        total_duty_fmt=fmt_num(os_obj.total_duty_amount),
        fine_total_fmt=fmt_num(rf_amount + ref_amount),
        pp_amt_fmt=fmt_num(pp_amount),
        logo_path=logo_path,
        # All other versioned static text fields
        office_header_line1=_ptc("office_header_line1",
            "Office of the Deputy / Asst. Commissioner of Customs"),
        office_header_line2=_ptc("office_header_line2",
            "(Airport), Anna International Airport, Chennai-600027"),
        page1_title=_ptc("page1_title",
            "Detention / Seizure of Passenger's Baggage"),
        inventory_heading=_ptc("inventory_heading",
            "INVENTORY OF THE GOODS IMPORTED"),
        col_duty_heading=_ptc("col_duty_heading",
            "Goods Passed On Duty"),
        supdt_sig_title=_ptc("supdt_sig_title",
            "Supdt. of Customs"),
        p2_office_heading=_ptc("p2_office_heading",
            "Office of the Deputy / Asst. Commissioner of Customs (Airport), Anna International airport, Chennai-600027."),
        p2_waiver_heading=_ptc("p2_waiver_heading",
            "WAIVER OF SHOW CAUSE NOTICE"),
        waiver_text_1=_ptc("waiver_text_1",
            "The Charges have been orally communicated to me in respect of the goods mentioned overleaf and imported by me. Orders in the case may please be passed without issue of Show Cause Notice. However I may kindly be given a Personal Hearing."),
        waiver_text_2=_ptc("waiver_text_2",
            "I was present during the personal hearing conducted by the Deputy / Asst. Commissioner and I was heard."),
        nb1_text=_ptc("nb1_text",
            "N.B: 1. This copy is granted free of charge for the private use of the person to whom it is issued."),
        nb2_text=_ptc("nb2_text",
            "2. An Appeal against this Order shall lie before the Commissioner of Customs (Appeals), Custom House, Chennai-600 001 on payment of 7.5% of the duty demanded where duty or duty and penalty are in dispute, or penalty, where penalty alone is in dispute. The Appeal shall be filed within 60 days provided under Section 128 of the Customs Act, 1962 from the date of receipt of this Order."),
        note_scn_waived=_ptc("note_scn_waived",
            "Note: The issue of Show Cause Notice was waived at the instance of the Passenger."),
        legal_para_1=_ptc("legal_para_1",
            "In terms of Foreign Trade Policy notified by the Government in pursuance to Section 3(1) & 3(2) of the Foreign Trade (Development & Regulation) Act, 1992 read with the Rules framed thereunder, also read with Section 11(2)(u) of Customs Act, 1962, import of 'goods in commercial quantity / goods in the nature of non-bonafide baggage' is not permitted without a valid import licence, though exemption exists under clause 3(h) of the Foreign Trade (Exemption from application of Rules in certain cases) order 1993 for import of goods by a passenger from abroad only to the extent admissible under the Baggage Rules framed under Section 79 of the Customs Act, 1962."),
        legal_para_2=_ptc("legal_para_2",
            "Import of goods non-declared / misdeclared / concealed / in trade and in commercial quantity / non-bonafide in excess of the baggage allowance is therefore liable for confiscation under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (Development & Regulation) Act, 1992."),
        record_heading=_ptc("record_heading",
            "RECORD OF PERSONAL HEARING & FINDINGS"),
        order_heading=_ptc("order_heading",
            "ORDER"),
        # Pre-rendered ORDER paragraphs (template substitution done in Python)
        para_rf=_render_para(
            _ptc("order_para_rf",
                "I Order confiscation of the goods{rf_slnos_text} valued at Rs.{conf_value}/- under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of Foreign Trade (D&R) Act, 1992, but allow the passenger an option to redeem the goods valued at Rs.{conf_value}/- on a fine of Rs.{rf_amount}/- (Rupees {rf_words} Only) in lieu of confiscation under Section 125 of the Customs Act 1962 within 7 days from the date of receipt of this Order, Duty extra."),
            rf_slnos_text=_slnos_text(rf_slnos),
            conf_value=int(conf_value),
            rf_amount=int(rf_amount),
            rf_words=title_words(rf_amount),
        ) if conf_value > 0 and int(rf_amount) > 0 else "",
        para_ref=_render_para(
            _ptc("order_para_ref",
                "However, I give an option to reship the goods{ref_slnos_text} valued at Rs.{re_exp_value}/- on a fine of Rs.{ref_amount}/- (Rupees {ref_words} Only) under Section 125 of the Customs Act 1962 within 1 Month from the date of this Order."),
            ref_slnos_text=_slnos_text(ref_slnos),
            re_exp_value=int(re_exp_value),
            ref_amount=int(ref_amount),
            ref_words=title_words(ref_amount),
        ) if re_exp_value > 0 and int(ref_amount) > 0 else "",
        para_abs_conf=_render_para(
            _ptc("order_para_abs_conf",
                "I {also_text}order absolute confiscation of the goods{abs_conf_slnos_text} valued at Rs.{abs_conf_value}/- under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (D&R) Act, 1992."),
            also_text="also " if (conf_value > 0 or re_exp_value > 0) else "",
            abs_conf_slnos_text=_slnos_text(all_abs_conf_slnos),
            abs_conf_value=int(abs_conf_value),
        ) if abs_conf_value > 0 else "",
        para_pp=_render_para(
            _ptc("order_para_pp",
                "I further impose a Personal Penalty of Rs.{pp_amount}/- (Rupees {pp_words} Only) under Section 112(a) of the Customs Act, 1962."),
            pp_amount=int(pp_amount),
            pp_words=title_words(pp_amount),
        ) if int(pp_amount) > 0 else "",
        deputy_sig_title=_ptc("deputy_sig_title",
            "Deputy / Asst. Commissioner of Customs (Airport)"),
        bottom_nb1=_ptc("bottom_nb1",
            "N.B: 1. Perishables will be disposed off within seven days from the date of detention."),
        bottom_nb2=_ptc("bottom_nb2",
            "2. Where re-export is permitted, the passenger is advised to intimate the date of departure of flight atleast 48 hours in advance."),
        bottom_nb3=_ptc("bottom_nb3",
            "3. Warehouse rent and Handling Charges are chargeable for the goods detained."),
        received_order_text=_ptc("received_order_text",
            "Received the Order-in-Original"),
    )

    # ── Generate PDF ───────────────────────────────────────────────────────────
    # Two-phase binary search — O(log n) renders instead of O(n).
    # Phase 1: find largest p2 (p1 fixed at 9pt anchor).
    # Phase 2: find largest p1 (p2 fixed from phase 1).
    _P2 = [11.0, 10.5, 10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5]
    _P1 = [11.0, 10.5, 10.0, 9.5, 9.0, 8.5, 8.0]

    # Phase 1 — binary search over p2 with p1 fixed at 9pt
    lo, hi = 0, len(_P2) - 1
    best_p2 = f"{_P2[-1]}pt"
    while lo <= hi:
        mid = (lo + hi) // 2
        doc = WeasyHTML(string=tmpl.render(**template_vars,
                        p1_font_size="9pt", p2_font_size=f"{_P2[mid]}pt")).render()
        if len(doc.pages) <= 2:
            best_p2 = f"{_P2[mid]}pt"
            hi = mid - 1   # try a larger font
        else:
            lo = mid + 1   # need a smaller font

    # Phase 2 — binary search over p1 with best_p2 fixed
    lo, hi = 0, len(_P1) - 1
    rendered_doc = None
    while lo <= hi:
        mid = (lo + hi) // 2
        doc = WeasyHTML(string=tmpl.render(**template_vars,
                        p1_font_size=f"{_P1[mid]}pt", p2_font_size=best_p2)).render()
        if len(doc.pages) <= 2:
            rendered_doc = doc
            hi = mid - 1   # try a larger font
        else:
            lo = mid + 1   # need a smaller font

    if rendered_doc is None:
        rendered_doc = WeasyHTML(string=tmpl.render(**template_vars,
                       p1_font_size=f"{_P1[-1]}pt", p2_font_size=best_p2)).render()
    pdf_bytes = rendered_doc.write_pdf()

    # Mark as printed
    if os_obj.os_printed != "Y":
        os_obj.os_printed = "Y"
        db.commit()

    filename = f"OS_{os_no}_{os_year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Adjudication Module: Adjudicate O/S Case ─────────────────────────────────
@router.post("/{os_no}/{os_year}/adjudicate")
def online_adjudicate(
    os_no: str,
    os_year: int,
    payload: schemas.AdjudicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)   # Adjudication module only
):
    """Adjudication Module: Enter adjudication details for an O/S case."""
    rules = BusinessRulesEngine(db)

    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()
    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found.")

    if os_obj.adjudication_date:
        raise HTTPException(
            status_code=400,
            detail="This O/S case has already been adjudicated. Cancel adjudication first to re-adjudicate."
        )

    rules.validate_remarks_length(payload.adjn_offr_remarks)

    # Update adjudication details
    os_obj.adjudication_date = payload.adjudication_date or date.today()
    os_obj.adjudication_time = datetime.now()
    os_obj.adj_offr_name = payload.adj_offr_name
    os_obj.adj_offr_designation = current_user.user_desig or payload.adj_offr_designation
    os_obj.adjn_offr_remarks = payload.adjn_offr_remarks

    # Save per-item release categories
    if payload.item_categories:
        items = db.query(CopsItems).filter(
            CopsItems.os_no == os_no,
            CopsItems.os_year == os_year,
        ).all()
        for item in items:
            cat = payload.item_categories.get(str(item.id))
            if cat in ('CONFS', 'RF', 'REF'):
                item.items_release_category = cat

    # Disposal values (computed from item categories on frontend)
    os_obj.confiscated_value = payload.confiscated_value
    os_obj.redeemed_value = payload.redeemed_value
    os_obj.re_export_value = payload.re_export_value

    # Financial demands
    os_obj.rf_amount = payload.rf_amount
    os_obj.pp_amount = payload.pp_amount
    os_obj.ref_amount = payload.ref_amount
    # Duty is already populated by SDO module in os_obj.total_duty_amount
    os_obj.total_payable = os_obj.total_duty_amount + payload.rf_amount + payload.ref_amount + payload.pp_amount

    # Order-in-Original reference
    os_obj.online_adjn = "Y"
    os_obj.closure_ind = "Y" if payload.close_case else None

    db.commit()
    return {"message": "Adjudication Details Updated !", "os_no": os_no, "os_year": os_year}


# ── Adjudication Module: Cancel Adjudication ──────────────────────────────────
@router.post("/{os_no}/{os_year}/cancel-adjudication")
def cancel_adjudicate(
    os_no: str,
    os_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)  # Adjudication module only
):
    """Adjudication Module: Cancel an adjudication and re-open the case."""
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year
    ).first()
    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. not found")

    if os_obj.online_adjn != "Y":
        raise HTTPException(status_code=400, detail="O.S. is not currently adjudicated online.")

    # Archive the state
    try:
        del_obj = CopsMasterDeleted(
            **{c.name: getattr(os_obj, c.name) for c in CopsMaster.__table__.columns if c.name not in ['id', 'adjn_offr_remarks1']}
        )
        del_obj.adjn_offr_remarks1 = "ADJN. CANCELLED"
        db.add(del_obj)
    except Exception:
        pass  # audit table may differ in schema — don't block the cancel

    # Reset adjudication fields
    os_obj.online_adjn = "N"
    os_obj.adjudication_date = None
    os_obj.adjudication_time = None
    os_obj.adj_offr_name = None
    os_obj.adj_offr_designation = None
    os_obj.adjn_offr_remarks = None
    os_obj.confiscated_value = 0.0
    os_obj.redeemed_value = 0.0
    os_obj.re_export_value = 0.0
    os_obj.rf_amount = 0.0
    os_obj.pp_amount = 0.0
    os_obj.ref_amount = 0.0
    os_obj.total_payable = 0.0
    os_obj.closure_ind = None

    db.commit()
    return {"message": "Adjudication Particulars Not Updated in D/R Data ! Adjudication Cancelled Successfully."}


# ── Adjudication: Delete O/S Case (soft-delete, DC/AC only) ──────────────────
@router.delete("/{os_no}/{os_year}")
def delete_os(
    os_no: str,
    os_year: int,
    reason: str = Query(..., min_length=5, description="Mandatory reason for deletion (minimum 5 characters)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),   # Any active user (SDO, DC, AC)
):
    """
    Soft-delete an O/S case.

    Rules:
    - Any active user may delete (SDO deletes own drafts/pending; DC/AC can delete any).
    - A reason must be provided (min 5 characters).
    - Adjudicated cases cannot be deleted.
    - Before marking deleted, a full snapshot is archived to cops_master_deleted.
    - The OS No is freed for reuse: a new case with the same OS No can be
      created after deletion (uniqueness check filters entry_deleted='N').

    Audit trail stored on the cops_master record:
      deleted_by     — user_id of the officer who deleted
      deleted_reason — the reason provided
      deleted_on     — today's date
    """
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N",
    ).first()

    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found or already deleted.")

    if os_obj.adjudication_date:
        raise HTTPException(
            status_code=400,
            detail=(
                "This O/S case has already been adjudicated and cannot be deleted. "
                "Use the Quash workflow to remove an adjudicated case."
            ),
        )

    # Archive a full snapshot to cops_master_deleted BEFORE marking deleted.
    # This preserves the complete record state for audit/recovery.
    try:
        skip_cols = {"id", "adjn_offr_remarks1", "deleted_by", "deleted_reason", "deleted_on"}
        snapshot = CopsMasterDeleted(
            **{
                c.name: getattr(os_obj, c.name)
                for c in CopsMaster.__table__.columns
                if c.name not in skip_cols and hasattr(CopsMasterDeleted, c.name)
            }
        )
        db.add(snapshot)
    except Exception:
        # Never block deletion just because the audit archive fails.
        # The primary audit is the fields on the cops_master record itself.
        pass

    # Soft-delete with full audit trail
    os_obj.entry_deleted = "Y"
    os_obj.deleted_by = current_user.user_id
    os_obj.deleted_reason = reason.strip()
    os_obj.deleted_on = date.today()

    db.commit()
    return {
        "message": "O/S case deleted.",
        "os_no": os_no,
        "os_year": os_year,
        "deleted_by": current_user.user_id,
        "deleted_on": date.today().isoformat(),
        "note": f"OS No. {os_no}/{os_year} can now be reused for a new entry.",
    }

# ── Adjudication: Reject Pending O/S ─────────────────────────────────────────
@router.post("/{os_no}/{os_year}/reject")
def reject_os(
    os_no: str,
    os_year: int,
    payload: schemas.OSActionReason,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_draft == "N",
        CopsMaster.quashed != "Y"
    ).first()
    
    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. case not found.")
    if os_obj.adjudication_date is not None:
        raise HTTPException(status_code=400, detail="Cannot reject an already adjudicated case.")
        
    os_obj.rejected = "Y"
    os_obj.reject_reason = payload.reason
    db.commit()
    return {"message": "O/S case rejected."}

# ── Adjudication: Quash Adjudicated O/S ──────────────────────────────────────
@router.post("/{os_no}/{os_year}/quash")
def quash_os(
    os_no: str,
    os_year: int,
    payload: schemas.OSActionReason,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_draft == "N"
    ).first()
    
    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. case not found.")
    if os_obj.adjudication_date is None:
        raise HTTPException(status_code=400, detail="Cannot quash an un-adjudicated case.")
        
    if os_obj.adjudication_time and datetime.now() - os_obj.adjudication_time > timedelta(hours=1):
        raise HTTPException(
            status_code=400, 
            detail="Quash period expired. Cases can only be quashed within 1 hour of adjudication."
        )
        
    os_obj.quashed = "Y"
    os_obj.quash_reason = payload.reason
    os_obj.quashed_by = current_user.user_name
    os_obj.quash_date = date.today()
    db.commit()
    return {"message": "O/S case quashed."}
