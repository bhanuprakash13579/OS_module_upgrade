import logging
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, cast, Integer as SAInteger, exists, not_, text
from collections import defaultdict

logger = logging.getLogger(__name__)

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


# ── Centralized "pending adjudication" filter ─────────────────────────────────
# IMPORTANT: This is the single source of truth for what makes a case "pending".
# It is used by:
#   1. get_all_os()             — the generic list endpoint (?status=pending)
#   2. get_pending_count()      — sidebar badge count
#   3. get_pending_adjudication() — dedicated pending list endpoint
# If the definition of "pending" ever changes, update this ONE function.
def _pending_filters():
    """Return SQLAlchemy filter criteria for a truly pending case.

    A case is pending adjudication when ALL of these are true:
      - entry_deleted != 'Y'   (not soft-deleted — applied by the caller)
      - is_draft == 'N'        (SDO has submitted it)
      - adjudication_date IS NULL  (no order date set)
      - adj_offr_name IS NULL     (no adjudicating officer assigned)
      - adjn_offr_remarks IS NULL or ''  (no AC order text — historical MDB data
            has AC remarks set even when adj_offr_name/date are NULL because the
            old module stored them separately; non-empty remarks = already adjudicated)
      - quashed != 'Y'           (not quashed)
      - rejected != 'Y'          (not rejected)
    """
    return [
        CopsMaster.is_draft == 'N',
        CopsMaster.adjudication_date.is_(None),
        CopsMaster.adj_offr_name.is_(None),
        or_(CopsMaster.adjn_offr_remarks.is_(None), CopsMaster.adjn_offr_remarks == ''),
        CopsMaster.quashed != 'Y',
        CopsMaster.rejected != 'Y',
        or_(CopsMaster.is_legacy.is_(None), CopsMaster.is_legacy != 'Y'),
        or_(CopsMaster.is_offline_adjudication.is_(None), CopsMaster.is_offline_adjudication != 'Y'),
    ]


# ── 24-Hour Modification Window ───────────────────────────────────────────────
def _within_edit_window(os_obj) -> bool:
    """
    Returns True if the 24-hour post-adjudication modification window is open.
    The window starts from adjudication_time and lasts exactly 24 hours.
    If adjudication_time is not set the case is not yet adjudicated (always editable by SDO).
    """
    if not os_obj.adjudication_time:
        return True
    return datetime.now() - os_obj.adjudication_time <= timedelta(hours=24)


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
from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor
_item_desc_cache: list[str] = []
_item_desc_cache_ts: float = 0.0
_item_desc_lock = _threading.Lock()

# ── PDF template cache (loaded once, reused across requests) ──────────────────
_pdf_jinja_env = None
_pdf_jinja_lock = _threading.Lock()

def _get_pdf_template():
    """Return the cached Jinja2 environment+template for OS print (thread-safe)."""
    global _pdf_jinja_env
    if _pdf_jinja_env is not None:
        return _pdf_jinja_env
    with _pdf_jinja_lock:
        if _pdf_jinja_env is None:
            from pathlib import Path
            from jinja2 import Environment, FileSystemLoader
            templates_dir = Path(__file__).parent.parent / "templates"
            env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
            _pdf_jinja_env = env.get_template("os_print.html")
    return _pdf_jinja_env

# ── Font-size result cache (in-memory, keyed on template-data hash) ───────────
# Any change to OS data, items, remarks, or admin print-template config produces
# a different hash → automatic cache miss.  No manual invalidation needed.
_font_cache: dict[str, tuple[str, str]] = {}
_FONT_CACHE_MAX = 200          # evict oldest entry beyond this limit

def _font_cache_key(template_vars: dict) -> str:
    """Deterministic hash of all template data that affects page layout."""
    import hashlib, json
    # logo_path doesn't affect text layout; exclude to match sizing behaviour
    filtered = {k: v for k, v in template_vars.items() if k != "logo_path"}
    raw = json.dumps(filtered, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

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
    # Fast path (no lock): return cached value if fresh
    if _item_desc_cache and (now - _item_desc_cache_ts) < 300:
        return _item_desc_cache
    # Slow path: acquire lock, re-check under lock to prevent thundering herd
    with _item_desc_lock:
        if _item_desc_cache and (_time.time() - _item_desc_cache_ts) < 300:
            return _item_desc_cache
        rows = (
            db.query(
                CopsItems.items_desc,
                func.count(CopsItems.items_desc).label("cnt")
            )
            .filter(
                CopsItems.items_desc.isnot(None),
                CopsItems.items_desc != '',
                CopsItems.entry_deleted == "N",
            )
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
        _item_desc_cache = result
        _item_desc_cache_ts = _time.time()
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
        duty = round(max(0.0, (item_value - fa)) * rate / 100.0, 2)
        total_val += item_value
        total_duty = round(total_duty + duty, 2)
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
        duty = round(max(0.0, (item_value - fa)) * rate / 100.0, 2)

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
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).all()
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
    br_dr_pending: bool = Query(False),
):
    """All active users: OS case list with server-side pagination, search, and filters."""
    q = db.query(CopsMaster).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.os_year <= 2100,   # guard against stray data-entry errors (e.g. os_year=20007)
    )
    if search.strip():
        s = f"%{search.strip()}%"
        q = q.filter(or_(
            CopsMaster.os_no.ilike(s),
            CopsMaster.pax_name.ilike(s),
            CopsMaster.passport_no.ilike(s),
            CopsMaster.old_passport_no.ilike(s),
            CopsMaster.flight_no.ilike(s),
        ))
    if year:
        q = q.filter(CopsMaster.os_year == year)
    if status:
        sl = status.lower()
        if sl == 'draft':
            q = q.filter(CopsMaster.is_draft == 'Y')
        elif sl == 'adjudicated':
            # Adjudicated = EITHER adjudication_date OR adj_offr_name is set.
            # This mirrors the inverse of _pending_filters() — a case exits the
            # pending queue as soon as either field is populated.  Old imported
            # records may have adj_offr_name without a date, so checking only
            # adjudication_date would make those invisible in both lists.
            q = q.filter(
                CopsMaster.is_draft == 'N',
                CopsMaster.quashed != 'Y',
                CopsMaster.rejected != 'Y',
                or_(
                    CopsMaster.adjudication_date.isnot(None),
                    CopsMaster.adj_offr_name.isnot(None),
                )
            )
        elif sl == 'pending':
            # Uses the centralized _pending_filters() — see top of file
            q = q.filter(*_pending_filters())
    # BR/DR pending: adjudicated cases where no post-adj receipt data has been entered yet
    if br_dr_pending:
        q = q.filter(
            CopsMaster.adjudication_date.isnot(None),
            CopsMaster.post_adj_br_entries.is_(None),
            CopsMaster.post_adj_dr_no.is_(None),
        )
    total = q.count()
    records = q.order_by(
        CopsMaster.os_year.desc(),
        cast(CopsMaster.os_no, SAInteger).desc()
    ).offset((page - 1) * per_page).limit(per_page).all()
    # List view uses total_items from master — no item join needed
    for r in records:
        r.items = []
    return {"total": total, "page": page, "per_page": per_page, "items": records}


# ── SDO: Update post-adjudication BR/DR receipt metadata ─────────────────────
@router.patch("/{os_no}/{os_year}/post-adj")
def update_post_adj(
    os_no: str,
    os_year: int,
    data: schemas.PostAdjUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sdo_user),
):
    """
    SDO: Record BR/DR receipt details after the adjudication order is issued.
    Strictly limited to post_adj_br_entries, post_adj_dr_no, post_adj_dr_date.
    No adjudication field (officer, amounts, dates) is ever touched.
    """
    import json as _json

    case = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N",
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="O.S. case not found.")
    if not case.adjudication_date:
        raise HTTPException(
            status_code=400,
            detail="BR/DR details can only be added after the adjudication order is issued.",
        )

    # Serialize BR entries to JSON (empty list → NULL to keep DB clean)
    entries = [{"no": e.no, "date": e.date.isoformat() if e.date else None}
               for e in data.br_entries if e.no.strip()]
    case.post_adj_br_entries = _json.dumps(entries) if entries else None
    case.post_adj_dr_no      = data.dr_no.strip() if data.dr_no and data.dr_no.strip() else None
    case.post_adj_dr_date    = data.dr_date or None

    db.commit()
    return {"status": "ok"}


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
    # Uses _pending_filters() — single source of truth (see top of file)
    count = db.query(func.count(CopsMaster.id)).filter(
        CopsMaster.entry_deleted == "N",
        *_pending_filters(),
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
    # Uses _pending_filters() — single source of truth (see top of file)
    records = db.query(CopsMaster).filter(
        CopsMaster.entry_deleted == "N",
        *_pending_filters(),
        pending_items_subq,
    ).order_by(CopsMaster.os_year.desc(), cast(CopsMaster.os_no, SAInteger).desc()).limit(200).all()
    # List view only needs master-level fields — skip item join for performance
    for r in records:
        r.items = []
    return records


# ── Lookup passport details for smart auto-fill (Offline Adjudication) ───────
@router.get("/passports/lookup-by-pp")
def lookup_passport_details(
    passport_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sdo_user)
):
    """
    Smart auto-fill: given a passport number, return passenger details
    from the most recent case in the DB with that passport number.
    Also returns linked old passports via name+DOB matching.
    """
    from app.services.apis_match import _name_score, _NAME_THRESHOLD

    pp = passport_no.strip().upper()
    if not pp:
        return {"found": False}

    # Find most recent case with this passport number
    rec = db.query(CopsMaster).filter(
        CopsMaster.passport_no == pp,
        CopsMaster.entry_deleted == "N"
    ).order_by(CopsMaster.os_year.desc(), CopsMaster.id.desc()).first()

    if not rec:
        return {"found": False}

    # Build linked passport list (same DOB + similar name)
    linked_passports: set = {pp}
    if rec.pax_date_of_birth and rec.pax_name:
        candidates = db.query(CopsMaster).filter(
            CopsMaster.pax_date_of_birth == rec.pax_date_of_birth,
            CopsMaster.entry_deleted == "N"
        ).limit(200).all()
        for c in candidates:
            if _name_score(rec.pax_name, c.pax_name or '') >= _NAME_THRESHOLD:
                if c.passport_no:
                    linked_passports.add(c.passport_no.strip().upper())
                if c.old_passport_no:
                    for op in c.old_passport_no.split(";"):
                        if op.strip():
                            linked_passports.add(op.strip().upper())
    linked_passports.discard(pp)  # remove current passport from old list

    return {
        "found": True,
        "pax_name": rec.pax_name,
        "pax_nationality": rec.pax_nationality,
        "pax_date_of_birth": rec.pax_date_of_birth.isoformat() if rec.pax_date_of_birth else None,
        "pax_address1": rec.pax_address1,
        "pax_address2": rec.pax_address2,
        "pax_address3": rec.pax_address3,
        "pp_issue_place": rec.pp_issue_place,
        "passport_date": rec.passport_date.isoformat() if rec.passport_date else None,
        "residence_at": rec.residence_at,
        "father_name": rec.father_name,
        "old_passport_no": ";".join(sorted(linked_passports)) if linked_passports else None,
    }


# ── SDO: Create Offline Adjudication Case ────────────────────────────────────
@router.post("/offline", response_model=schemas.CopsMasterOut)
def create_offline_adjudication(
    data: schemas.CopsMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_sdo_user)
):
    """
    SDO Module: Register an offline adjudication case.
    Same as create_os but with relaxed date validation and is_offline_adjudication='Y'.
    """
    from app.services.rules_engine import BusinessRulesEngine
    rules = BusinessRulesEngine(db)
    data.passport_no = rules.normalize_passport(data.passport_no)

    os_date = data.os_date
    if not os_date:
        from datetime import date as _date
        os_date = _date.today()

    os_no = str(data.os_no or '').strip()
    if not os_no:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="O.S. No. is required.")
    if not os_no.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="O.S. No. must contain digits only.")

    os_year = os_date.year

    existing = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"O.S. No. {os_no}/{os_year} already exists.")

    total_val = 0.0
    total_duty = 0.0
    for item in data.items:
        item_value = float(item.items_value or 0.0)
        fa = _eff_fa(item_value, item)
        rate = float(item.cumulative_duty_rate or 0.0)
        duty = round(max(0.0, (item_value - fa)) * rate / 100.0, 2)
        total_val += item_value
        total_duty = round(total_duty + duty, 2)

    os_obj = CopsMaster(
        os_no=os_no,
        os_date=os_date,
        os_year=os_year,
        total_items=len(data.items),
        total_items_value=total_val,
        total_duty_amount=total_duty,
        total_payable=total_duty,
        is_offline_adjudication='Y',
        **data.model_dump(exclude={"items", "os_no", "os_year", "os_date", "is_offline_adjudication"})
    )
    db.add(os_obj)
    db.commit()
    db.refresh(os_obj)

    for c_item in data.items:
        item_value = float(c_item.items_value or 0.0)
        fa = _eff_fa(item_value, c_item)
        rate = float(c_item.cumulative_duty_rate or 0.0)
        duty = round(max(0.0, (item_value - fa)) * rate / 100.0, 2)
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
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).all()
    return os_obj


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

# ── Adjudication: Pending Offline Adjudication Count ─────────────────────────
@router.get("/offline-pending/count")
def get_offline_pending_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """Returns count of offline adjudication cases pending officer details entry."""
    count = db.query(func.count(CopsMaster.id)).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_offline_adjudication == 'Y',
        CopsMaster.adj_offr_name.is_(None),
    ).scalar()
    return {"count": count or 0}


# ── Adjudication: Combined sidebar counts (one round-trip instead of two) ────
@router.get("/sidebar-counts")
def get_sidebar_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """
    Returns both pending and offline-pending counts in a single DB transaction.
    Replaces the two separate /pending/count and /offline-pending/count calls
    made by AdjudicationLayout on every mount.
    """
    pending_items_subq = exists().where(
        and_(
            CopsItems.os_no == CopsMaster.os_no,
            CopsItems.os_year == CopsMaster.os_year,
            CopsItems.items_release_category.in_(['Under OS', 'Under Duty'])
        )
    )
    pending_count = db.query(func.count(CopsMaster.id)).filter(
        CopsMaster.entry_deleted == "N",
        *_pending_filters(),
        pending_items_subq,
    ).scalar() or 0

    offline_count = db.query(func.count(CopsMaster.id)).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_offline_adjudication == 'Y',
        CopsMaster.adj_offr_name.is_(None),
    ).scalar() or 0

    return {"pending": pending_count, "offline_pending": offline_count}


# ── Adjudication: Pending Offline Adjudication List ──────────────────────────
@router.get("/offline-pending", response_model=List[schemas.CopsMasterOut])
def get_offline_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """Cases registered as offline adjudication but officer details not yet captured."""
    records = db.query(CopsMaster).filter(
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_offline_adjudication == 'Y',
        CopsMaster.adj_offr_name.is_(None),
    ).order_by(CopsMaster.os_year.desc(), cast(CopsMaster.os_no, SAInteger).desc()).limit(200).all()
    for r in records:
        r.items = []
    return records


# ── Adjudication: Complete Offline Adjudication ───────────────────────────────
@router.patch("/{os_no}/{os_year}/complete-offline-adj")
def complete_offline_adjudication(
    os_no: str,
    os_year: int,
    data: schemas.OfflineAdjudicationComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """
    Adjudication Module: Capture officer details for an offline adjudication case.
    Mandatory: adj_offr_name, adj_offr_designation.
    """
    case = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_offline_adjudication == 'Y',
    ).first()
    if not case:
        raise HTTPException(status_code=404,
                            detail="Offline adjudication case not found.")
    if case.adj_offr_name:
        raise HTTPException(status_code=400,
                            detail="This offline case has already been completed.")

    from datetime import date as _date
    case.adj_offr_name = data.adj_offr_name.strip()
    case.adj_offr_designation = data.adj_offr_designation.strip()
    case.adjudication_date = data.adjudication_date or _date.today()
    # Stamp adjudication_time so the 24-hour modification window works correctly.
    # Without this, _within_edit_window() sees None and returns True forever.
    case.adjudication_time = datetime.now()
    case.rf_amount = data.rf_amount
    case.pp_amount = data.pp_amount
    case.ref_amount = data.ref_amount
    case.confiscated_value = data.confiscated_value
    case.redeemed_value = data.redeemed_value
    case.re_export_value = data.re_export_value
    if data.adjn_offr_remarks:
        case.adjn_offr_remarks = data.adjn_offr_remarks
    if data.close_case:
        case.closure_ind = 'Y'

    db.commit()
    return {"status": "ok", "os_no": os_no, "os_year": os_year}


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


# ── SDO / Adjudication: Modify O/S Case ──────────────────────────────────────
@router.put("/{os_no}/{os_year}", response_model=schemas.CopsMasterOut)
def update_os(
    os_no: str,
    os_year: int,
    data: schemas.CopsMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Modify an existing O/S case.

    - SDO users: always allowed (unless print lock is active).
      After adjudication, within 24 hours: allowed — resets adjudication fields.
      After adjudication, beyond 24 hours: blocked.
    - DC/AC users: only allowed on adjudicated cases within the 24-hour window.
      Resets adjudication fields so the case returns to pending for re-adjudication.
    """
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N"
    ).first()

    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. record not found.")

    # Role-based access:
    # - DC/AC users: can edit any pending case freely; after adjudication, only within 24h window.
    # - SDO users: existing behaviour (print lock + 24h adjudication window).
    if current_user.user_role in ("DC", "AC"):
        if os_obj.adjudication_date and not _within_edit_window(os_obj):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modification window has expired. O/S cases can only be modified within 24 hours of adjudication."
            )
    elif current_user.user_role != "SDO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this case."
        )

    if os_obj.adjudication_date:
        # Case is adjudicated — only allowed within the 24-hour window
        if not _within_edit_window(os_obj):
            raise HTTPException(
                status_code=400,
                detail="Modification window has expired. O/S cases can only be modified within 24 hours of adjudication."
            )
        # Reset all adjudication fields — case returns to pending for re-adjudication
        os_obj.online_adjn = "N"
        os_obj.adjudication_date = None
        os_obj.adjudication_time = None
        os_obj.adj_offr_name = None
        os_obj.adj_offr_designation = None
        os_obj.adjn_offr_remarks = None
        os_obj.os_printed = 'N'
        os_obj.confiscated_value = 0.0
        os_obj.redeemed_value = 0.0
        os_obj.re_export_value = 0.0
        os_obj.rf_amount = 0.0
        os_obj.pp_amount = 0.0
        os_obj.ref_amount = 0.0
        os_obj.total_payable = 0.0
        os_obj.closure_ind = None
    elif os_obj.os_printed == 'Y':
        # Not adjudicated but already printed — block modification
        raise HTTPException(
            status_code=400,
            detail="Print Out Has Already Been Taken for The Entered O.S.No. Cannot Modify its details !"
        )

    # Update master fields (do not allow changing O.S. No / Year via payload)
    update_data = data.model_dump(exclude={"items", "os_no", "os_year"})
    for key, value in update_data.items():
        setattr(os_obj, key, value)

    # Recalculate items and totals on the backend
    # Free allowance applies to "Under Duty" goods (reduces dutiable value) and "Under OS" goods (reduces seized value)
    total_val = 0.0
    total_duty = 0.0
    total_fa = 0.0
    for item in data.items:
        item_value = float(item.items_value or 0.0)
        fa = _eff_fa(item_value, item)
        rate = float(item.cumulative_duty_rate or 0.0)
        duty = round(max(0.0, (item_value - fa)) * rate / 100.0, 2)
        total_val += item_value
        total_fa += fa
        total_duty = round(total_duty + duty, 2)

    os_obj.total_items_value = total_val
    os_obj.total_fa_value = round(total_fa, 2)
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
        duty = round(max(0.0, (item_value - fa)) * rate / 100.0, 2)

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
    current_user: User = Depends(get_current_active_user),
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


# ── BR / DR display helpers for PDF template ─────────────────────────────────
def _fmt_dot_date(d) -> str:
    """Format a date (date object or ISO string) as dd.mm.yyyy with dots."""
    if not d:
        return ""
    try:
        from datetime import date as _date
        if isinstance(d, _date):
            return d.strftime("%d.%m.%Y")
        # Try parsing ISO string — strip any time component before the T or space
        from datetime import datetime as _dt
        date_part = str(d).split("T")[0].split(" ")[0]
        return _dt.strptime(date_part, "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception:
        return str(d)


def _fmt_br_entries(raw_json) -> str:
    """Return e.g. 'BR.No.9291 dt.05.03.2026, BR.No.9292 dt.06.03.2026' or ''."""
    if not raw_json:
        return ""
    try:
        import json as _json
        entries = _json.loads(raw_json) if isinstance(raw_json, str) else raw_json
        parts = []
        for e in entries:
            no = (e.get("no") or "").strip()
            if not no:
                continue
            dt = _fmt_dot_date(e.get("date"))
            parts.append(f"BR.No.{no} dt.{dt}" if dt else f"BR.No.{no}")
        return ", ".join(parts)
    except Exception:
        return ""


def _fmt_dr(dr_no, dr_date) -> str:
    """Return e.g. 'DR.No.3539 dt.05.03.2026' or ''."""
    if not dr_no or not str(dr_no).strip():
        return ""
    dt = _fmt_dot_date(dr_date)
    return f"DR.No.{str(dr_no).strip()} dt.{dt}" if dt else f"DR.No.{str(dr_no).strip()}"


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
    rf_slnos: list[str] = []
    ref_slnos: list[str] = []
    confs_slnos: list[str] = []
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
            rf_slnos.append(str(idx + 1))
        elif cat == "REF":
            ref_val_items += dutiable
            ref_slnos.append(str(idx + 1))
        elif cat == "CONFS":
            confs_val_items += dutiable
            confs_slnos.append(str(idx + 1))

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

    # Serial numbers grouped by disposal category — accumulated in the main loop above

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
    # In a frozen PyInstaller EXE sys._MEIPASS is the temp extraction dir;
    # the spec bundles ../frontend/dist → frontend_dist inside _MEIPASS.
    # In dev, fall back to the source tree (frontend/public or frontend/dist).
    import sys as _sys
    if getattr(_sys, 'frozen', False):
        _base = Path(getattr(_sys, '_MEIPASS', '')) / "frontend_dist"
    else:
        _base = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    logo_file = _base / "customs-logo.jpg"
    logo_path = logo_file.as_uri() if logo_file.exists() else ""

    # ── Render template (cached across requests) ──────────────────────────────
    tmpl = _get_pdf_template()

    # ── Export / Arrival distinction ──────────────────────────────────────────
    is_export = (os_obj.case_type or "").strip().upper() == "EXPORT CASE"

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
        from_to_text=(
            f"CHENNAI TO {os_obj.port_of_dep_dest or os_obj.country_of_departure or '—'}"
            if is_export else
            f"{os_obj.port_of_dep_dest or os_obj.country_of_departure or '—'} TO CHENNAI"
        ),
        stay_abroad_text="N/A" if is_export else f"{os_obj.stay_abroad_days or 0} Days",
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
        inventory_heading=_ptc(
            "export_inventory_heading" if is_export else "inventory_heading",
            "INVENTORY OF THE GOODS DETAINED FOR EXPORT" if is_export else "INVENTORY OF THE GOODS IMPORTED"),
        col_duty_heading=_ptc("col_duty_heading",
            "Goods Passed On Duty"),
        supdt_sig_title=_ptc("supdt_sig_title",
            "Supdt. of Customs"),
        p2_office_heading=_ptc("p2_office_heading",
            "Office of the Deputy / Asst. Commissioner of Customs (Airport), Anna International airport, Chennai-600027."),
        p2_waiver_heading=_ptc("p2_waiver_heading",
            "WAIVER OF SHOW CAUSE NOTICE"),
        waiver_text_1=_ptc(
            "export_waiver_text_1" if is_export else "waiver_text_1",
            "The Charges have been orally communicated to me in respect of the goods mentioned overleaf and detained at the time of my departure. Orders in the case may please be passed without issue of Show Cause Notice. However I may kindly be given a Personal Hearing."
            if is_export else
            "The Charges have been orally communicated to me in respect of the goods mentioned overleaf and imported by me. Orders in the case may please be passed without issue of Show Cause Notice. However I may kindly be given a Personal Hearing."),
        waiver_text_2=_ptc("waiver_text_2",
            "I was present during the personal hearing conducted by the Deputy / Asst. Commissioner and I was heard."),
        nb1_text=_ptc("nb1_text",
            "N.B: 1. This copy is granted free of charge for the private use of the person to whom it is issued."),
        nb2_text=_ptc("nb2_text",
            "2. An Appeal against this Order shall lie before the Commissioner of Customs (Appeals), Custom House, Chennai-600 001 on payment of 7.5% of the duty demanded where duty or duty and penalty are in dispute, or penalty, where penalty alone is in dispute. The Appeal shall be filed within 60 days provided under Section 128 of the Customs Act, 1962 from the date of receipt of this Order."),
        note_scn_waived=_ptc("note_scn_waived",
            "Note: The issue of Show Cause Notice was waived at the instance of the Passenger."),
        legal_para_1=_ptc(
            "export_legal_para_1" if is_export else "legal_para_1",
            "In terms of Foreign Trade Policy notified by the Government in pursuance to Section 3(1) & 3(2) of the Foreign Trade (Development & Regulation) Act, 1992, export of goods without proper Customs declaration or in violation of applicable export regulations / restrictions is prohibited. Passengers are required to declare all goods carried at the time of departure as mandated under Section 40 of the Customs Act, 1962."
            if is_export else
            "In terms of Foreign Trade Policy notified by the Government in pursuance to Section 3(1) & 3(2) of the Foreign Trade (Development & Regulation) Act, 1992 read with the Rules framed thereunder, also read with Section 11(2)(u) of Customs Act, 1962, import of 'goods in commercial quantity / goods in the nature of non-bonafide baggage' is not permitted without a valid import licence, though exemption exists under clause 3(h) of the Foreign Trade (Exemption from application of Rules in certain cases) order 1993 for import of goods by a passenger from abroad only to the extent admissible under the Baggage Rules framed under Section 79 of the Customs Act, 1962."),
        legal_para_2=_ptc(
            "export_legal_para_2" if is_export else "legal_para_2",
            "Export of goods non-declared / misdeclared / concealed / in commercial quantity / contrary to any prohibition or export restriction is therefore liable for confiscation under Section 113 of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (Development & Regulation) Act, 1992."
            if is_export else
            "Import of goods non-declared / misdeclared / concealed / in trade and in commercial quantity / non-bonafide in excess of the baggage allowance is therefore liable for confiscation under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (Development & Regulation) Act, 1992."),
        record_heading=_ptc("record_heading",
            "RECORD OF PERSONAL HEARING & FINDINGS"),
        order_heading=_ptc("order_heading",
            "ORDER"),
        # Pre-rendered ORDER paragraphs (template substitution done in Python)
        para_rf=_render_para(
            _ptc(
                "export_order_para_rf" if is_export else "order_para_rf",
                # Export: Section 113, no "Duty extra" (export violations don't attract inbound duty)
                "I Order confiscation of the goods{rf_slnos_text} valued at Rs.{conf_value}/- under Section 113 of the Customs Act, 1962, but allow the passenger an option to redeem the goods valued at Rs.{conf_value}/- on a fine of Rs.{rf_amount}/- (Rupees {rf_words} Only) in lieu of confiscation under Section 125 of the Customs Act 1962 within 7 days from the date of receipt of this Order."
                if is_export else
                "I Order confiscation of the goods{rf_slnos_text} valued at Rs.{conf_value}/- under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of Foreign Trade (D&R) Act, 1992, but allow the passenger an option to redeem the goods valued at Rs.{conf_value}/- on a fine of Rs.{rf_amount}/- (Rupees {rf_words} Only) in lieu of confiscation under Section 125 of the Customs Act 1962 within 7 days from the date of receipt of this Order, Duty extra."),
            rf_slnos_text=_slnos_text(rf_slnos),
            conf_value=int(conf_value),
            rf_amount=int(rf_amount),
            rf_words=title_words(rf_amount),
        ) if conf_value > 0 and int(rf_amount) > 0 else "",
        # Re-export option does not apply to export/departure cases —
        # goods seized on exit cannot be "reshipped abroad"
        para_ref=_render_para(
            _ptc("order_para_ref",
                "However, I give an option to reship the goods{ref_slnos_text} valued at Rs.{re_exp_value}/- on a fine of Rs.{ref_amount}/- (Rupees {ref_words} Only) under Section 125 of the Customs Act 1962 within 1 Month from the date of this Order."),
            ref_slnos_text=_slnos_text(ref_slnos),
            re_exp_value=int(re_exp_value),
            ref_amount=int(ref_amount),
            ref_words=title_words(ref_amount),
        ) if (re_exp_value > 0 and int(ref_amount) > 0 and not is_export) else "",
        para_abs_conf=_render_para(
            _ptc(
                "export_order_para_abs_conf" if is_export else "order_para_abs_conf",
                # Export: Section 113
                "I {also_text}order absolute confiscation of the goods{abs_conf_slnos_text} valued at Rs.{abs_conf_value}/- under Section 113 of the Customs Act, 1962."
                if is_export else
                "I {also_text}order absolute confiscation of the goods{abs_conf_slnos_text} valued at Rs.{abs_conf_value}/- under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (D&R) Act, 1992."),
            also_text="also " if (conf_value > 0 or re_exp_value > 0) else "",
            abs_conf_slnos_text=_slnos_text(all_abs_conf_slnos),
            abs_conf_value=int(abs_conf_value),
        ) if abs_conf_value > 0 else "",
        para_pp=_render_para(
            _ptc(
                "export_order_para_pp" if is_export else "order_para_pp",
                # Export: Section 114 (import equivalent is Section 112)
                "I further impose a Personal Penalty of Rs.{pp_amount}/- (Rupees {pp_words} Only) under Section 114 of the Customs Act, 1962."
                if is_export else
                "I further impose a Personal Penalty of Rs.{pp_amount}/- (Rupees {pp_words} Only) under Section 112(a) of the Customs Act, 1962."),
            pp_amount=int(pp_amount),
            pp_words=title_words(pp_amount),
        ) if int(pp_amount) > 0 else "",
        deputy_sig_title=_ptc("deputy_sig_title",
            "Deputy / Asst. Commissioner of Customs (Airport)"),
        bottom_nb1=_ptc("bottom_nb1",
            "N.B: 1. Perishables will be disposed off within seven days from the date of detention."),
        # Re-export note is irrelevant for export/departure cases
        bottom_nb2="" if is_export else _ptc("bottom_nb2",
            "2. Where re-export is permitted, the passenger is advised to intimate the date of departure of flight atleast 48 hours in advance."),
        bottom_nb3=_ptc("bottom_nb3",
            "3. Warehouse rent and Handling Charges are chargeable for the goods detained."),
        received_order_text=_ptc("received_order_text",
            "Received the Order-in-Original"),
        br_display=_fmt_br_entries(os_obj.post_adj_br_entries),
        dr_display=_fmt_dr(os_obj.post_adj_dr_no, os_obj.post_adj_dr_date),
    )

    # ── Generate PDF ───────────────────────────────────────────────────────────
    # Two independent top-down searches (Page 1 font, Page 2 font) run in
    # parallel using a 2-worker thread pool.  Top-down starts from the largest
    # font and stops at the first size that fits on one page — for routine
    # 1-to-4 item bookings this resolves in a single render instead of the 3
    # that a binary search needs.  Results are cached in-memory keyed on a
    # SHA-256 hash of all template data, so repeat downloads of the same
    # unchanged O/S are instant.
    _P2 = [11.0, 10.5, 10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5]
    _P1 = [11.0, 10.5, 10.0, 9.5, 9.0, 8.5, 8.0]

    cache_key = _font_cache_key(template_vars)
    cached = _font_cache.get(cache_key)

    if cached:
        best_p1, best_p2 = cached
    else:
        test_vars = template_vars.copy()
        test_vars["logo_path"] = ""          # skip image I/O during sizing

        def _fit_page(sizes, page_no):
            """Top-down search: return largest font size that fits on one page."""
            for size in sizes:
                html = tmpl.render(**test_vars, **{
                    f"p{page_no}_font_size": f"{size}pt",
                    "only_page": page_no,
                })
                if len(WeasyHTML(string=html).render().pages) <= 1:
                    return f"{size}pt"
            return f"{sizes[-1]}pt"          # fallback to smallest

        with _ThreadPoolExecutor(max_workers=2) as _pool:
            _f1 = _pool.submit(_fit_page, _P1, 1)
            _f2 = _pool.submit(_fit_page, _P2, 2)
            best_p1 = _f1.result()
            best_p2 = _f2.result()

        # Store in cache (evict oldest entry if over limit)
        if len(_font_cache) >= _FONT_CACHE_MAX:
            _font_cache.pop(next(iter(_font_cache)))
        _font_cache[cache_key] = (best_p1, best_p2)

    def _step_down(size_str: str, sizes: list) -> str:
        """Return the next smaller size in the list, or the minimum if already there."""
        try:
            idx = sizes.index(float(size_str.replace("pt", "")))
            return f"{sizes[min(idx + 1, len(sizes) - 1)]}pt"
        except ValueError:
            return f"{sizes[-1]}pt"

    # Final combined render with the real logo and optimal font sizes.
    # Post-render safety check: if content is extreme (very long remarks,
    # many items) the combined render can still exceed 2 pages even when each
    # page passed its isolated test. Step both font sizes down and retry up to
    # 3 times to guarantee the output is always exactly 2 pages.
    rendered_doc = WeasyHTML(string=tmpl.render(**template_vars,
                            p1_font_size=best_p1, p2_font_size=best_p2)).render()
    for _ in range(3):
        if len(rendered_doc.pages) <= 2:
            break
        best_p1 = _step_down(best_p1, _P1)
        best_p2 = _step_down(best_p2, _P2)
        rendered_doc = WeasyHTML(string=tmpl.render(**template_vars,
                                p1_font_size=best_p1, p2_font_size=best_p2)).render()

    # If safety-check stepped down from a cached value, update the cache
    if cached and (best_p1, best_p2) != cached:
        _font_cache[cache_key] = (best_p1, best_p2)

    pdf_bytes = rendered_doc.write_pdf()

    if os_obj.os_printed != "Y":
        os_obj.os_printed = "Y"
        db.commit()

    filename = f"OS_{os_no}_{os_year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Encoding": "identity",
        },
    )


# ── Adjudication Module: Adjudicate O/S Case ─────────────────────────────────
@router.post("/{os_no}/{os_year}/adjudicate", response_model=schemas.CopsMasterOut)
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
        # Already adjudicated — only allow re-adjudication within the 24-hour window
        if not _within_edit_window(os_obj):
            raise HTTPException(
                status_code=400,
                detail="Re-adjudication not allowed. The 24-hour modification window has expired."
            )
        # Within window: allow re-adjudication (fall through to update fields below)

    rules.validate_remarks_length(payload.adjn_offr_remarks)

    # Update adjudication details
    os_obj.adjudication_date = payload.adjudication_date or date.today()
    # Stamp adjudication_time only on the FIRST adjudication.
    # Re-adjudications (Edit Adjudication within 24h) must not reset the clock —
    # the 24-hour window always runs from the original first adjudication time.
    # Exception: if adjudication_time is None (e.g. after an SDO edit reset it to
    # pending), it is a fresh adjudication event and gets a new timestamp.
    if not os_obj.adjudication_time:
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
    base_duty = float(os_obj.total_duty_amount or 0.0)
    os_obj.total_payable = base_duty + payload.rf_amount + payload.ref_amount + payload.pp_amount

    # Order-in-Original reference
    os_obj.online_adjn = "Y"
    os_obj.closure_ind = "Y" if payload.close_case else None

    db.commit()
    db.refresh(os_obj)
    # Attach items so the frontend can update its local state without a follow-up GET
    os_obj.items = db.query(CopsItems).filter(
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).all()
    return os_obj


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
                "This O/S case has already been adjudicated and cannot be deleted via this route. "
                "To remove an adjudicated case, use the Delete option in the Adjudication module "
                "within 24 hours of adjudication."
            ),
        )

    # Archive a full snapshot to cops_master_deleted BEFORE marking deleted.
    # This preserves the complete record state for audit/recovery.
    # If the snapshot fails, the entire operation is aborted — deletion without
    # an audit trail violates compliance requirements.
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
        db.flush()  # Surface any constraint/schema errors before we touch the master row
    except Exception as exc:
        db.rollback()
        logger.error("Audit archive failed — deletion aborted for OS %s/%s: %s", os_no, os_year, exc)
        raise HTTPException(
            status_code=500,
            detail="Deletion could not be completed: audit trail write failed. Please try again or contact support.",
        )

    # Soft-delete the master row and mark all child items deleted too.
    # Items must be marked so that autocomplete and direct item queries
    # don't surface descriptions from deleted cases.
    os_obj.entry_deleted = "Y"
    os_obj.deleted_by = current_user.user_id
    os_obj.deleted_reason = reason.strip()
    os_obj.deleted_on = date.today()

    db.query(CopsItems).filter(
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year,
    ).update({"entry_deleted": "Y"}, synchronize_session=False)

    db.commit()
    return {
        "message": "O/S case deleted.",
        "os_no": os_no,
        "os_year": os_year,
        "deleted_by": current_user.user_id,
        "deleted_on": date.today().isoformat(),
        "note": f"OS No. {os_no}/{os_year} can now be reused for a new entry.",
    }

# ── Adjudication: Delete Adjudicated O/S within 24-Hour Window ───────────────
@router.post("/{os_no}/{os_year}/quash")
def quash_os(
    os_no: str,
    os_year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user)
):
    """
    Permanently delete an adjudicated O/S case within the 24-hour modification window.

    Unlike a soft-delete or quash, this is a hard delete: all records are
    removed from cops_master and cops_items as if the case never existed.
    No reason or user attribution is captured — the 24-hour window is the
    sole safeguard.

    Window: 24 hours from adjudication_time.
    """
    os_obj = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == os_year,
        CopsMaster.entry_deleted == "N",
        CopsMaster.is_draft == "N"
    ).first()

    if not os_obj:
        raise HTTPException(status_code=404, detail="O.S. case not found.")
    if os_obj.adjudication_date is None:
        raise HTTPException(status_code=400, detail="Cannot delete an un-adjudicated case using this endpoint.")

    if not _within_edit_window(os_obj):
        raise HTTPException(
            status_code=400,
            detail="Deletion window has expired. O/S cases can only be deleted within 24 hours of adjudication."
        )

    # Hard delete: remove items first (FK constraint), then the master record
    db.query(CopsItems).filter(
        CopsItems.os_no == os_no,
        CopsItems.os_year == os_year
    ).delete(synchronize_session=False)
    db.delete(os_obj)
    db.commit()
    return {"message": "O/S case permanently deleted.", "os_no": os_no, "os_year": os_year}
