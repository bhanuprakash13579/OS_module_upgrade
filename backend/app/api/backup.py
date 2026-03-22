from collections import defaultdict
from datetime import date, datetime
import csv
import io
import os
import sqlite3
import tempfile
import zipfile
from typing import List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text, or_, and_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.offence import CopsMaster, CopsItems
from app.models.auth import User
from app.services.auth import get_adjn_user, get_current_active_user


router = APIRouter()


# ── Shared bulk-import optimiser ─────────────────────────────────────────────

_COPS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_cops_master_os_no_year       ON cops_master (os_no, os_year)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_draft_deleted     ON cops_master (entry_deleted, is_draft)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_adjudication_date ON cops_master (adjudication_date)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_quashed_rejected  ON cops_master (quashed, rejected)",
    "CREATE INDEX IF NOT EXISTS ix_cops_items_os_no_year         ON cops_items  (os_no, os_year)",
]


def post_import_optimise(db: Session) -> None:
    """
    Call once after any bulk data import (MDB, ZIP restore, CSV legacy upload).

    1. CREATE INDEX IF NOT EXISTS — creates any missing performance indexes in a
       single B-tree build pass over the already-inserted data.  This is faster
       than having SQLite update indexes row-by-row during the import itself.
       It is a no-op when the indexes already exist.

    2. ANALYZE — rewrites sqlite_stat1 so the query planner knows the new row
       counts and uses the correct index on the next paginated list query.
    """
    for stmt in _COPS_INDEXES:
        db.execute(text(stmt))
    db.execute(text("ANALYZE cops_master"))
    db.execute(text("ANALYZE cops_items"))
    db.commit()


def set_bulk_pragma(db: Session) -> None:
    """
    Set SQLite PRAGMAs that speed up bulk inserts.
    Safe to call with WAL mode active — WAL already guarantees crash safety.
    """
    db.execute(text("PRAGMA cache_size = -65536"))   # 64 MB page cache
    db.execute(text("PRAGMA temp_store = MEMORY"))

_LEGACY_DEFAULT_FIELDS = [
    "unique_no", "os_no", "os_year", "os_date", "pax_name",
    "pax_name_modified_by_vig", "pax_address1", "pax_address2",
    "pax_address3", "father_name", "pax_date_of_birth", "passport_no",
    "passport_date", "pax_nationality", "flight_no", "previous_visits",
    "adj_offr_name", "adj_offr_designation", "location_code", "flight_date",
    "total_items", "total_duty_amount", "total_items_value", "total_fa_value",
    "rf_amount", "pp_amount", "ref_amount", "wh_amount", "other_amount",
    "br_amount", "booked_by", "adjn_offr_remarks", "adjn_offr_remarks1",
    "redeemed_value", "confiscated_value", "dutiable_value", "re_export_value",
    "pax_image_filename", "adjudication_date", "total_payable", "os_category",
    "bkup_taken", "date_of_departure", "residence_at", "online_os",
    "online_adjn", "dr_no", "dr_year", "entry_deleted", "os_printed",
    "old_passport_no", "previous_os_details", "total_drs", "pax_status",
    "country_of_departure", "seizure_date",
]

_ACCESS_DATE_FORMATS = [
    "%m/%d/%y %H:%M:%S",   # 07/09/12 00:00:00
    "%m/%d/%Y %H:%M:%S",   # 07/09/2012 00:00:00
    "%m/%d/%y",             # 07/09/12
    "%m/%d/%Y",             # 07/09/2012
    "%d/%m/%Y",             # 09/07/2012
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def _parse_date(value: Optional[str]) -> date:
    if not value or not value.strip():
        return date.today()
    v = value.strip().strip('"')
    for fmt in _ACCESS_DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return date.today()


def _flt(row: dict, key: str) -> float:
    v = row.get(key) or row.get(key.upper())
    try:
        return float(v) if v and str(v).strip() else 0.0
    except (ValueError, TypeError):
        return 0.0


def _existing_os_keys(db: Session) -> Set[Tuple[str, int, str]]:
    """
    Returns a set of (trimmed_os_no, os_year, trimmed_location_code).
    TRIM is applied because the old VB6/Access DB stored os_no as 50-char
    padded text. Without trimming, the same case can appear as a duplicate.
    """
    rows = db.query(
        CopsMaster.os_no,
        CopsMaster.os_year,
        CopsMaster.location_code,
    ).all()
    return {((r[0] or "").strip(), r[1], (r[2] or "").strip()) for r in rows}


def _existing_item_keys(db: Session) -> Set[Tuple[str, int, str, int]]:
    """Returns (trimmed_os_no, os_year, trimmed_location_code, items_sno) for all items."""
    rows = db.query(
        CopsItems.os_no,
        CopsItems.os_year,
        CopsItems.location_code,
        CopsItems.items_sno,
    ).all()
    return {((r[0] or "").strip(), r[1], (r[2] or "").strip(), r[3] or 0) for r in rows}


@router.post("/upload/legacy")
def upload_legacy(
    file: UploadFile = File(...),
    no_header: bool = Form(False),
    fieldnames: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user),
):
    """
    Import legacy CSV (from old cops_master exports).
    Safe behaviour: only INSERT new OS cases; skip duplicates.

    If the CSV has no header row, set no_header=true and optionally provide
    a comma-separated list of field names in fieldnames matching the CSV column order.
    """
    try:
        raw = file.file.read().decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read uploaded file.")

    if no_header:
        # Use user-supplied fieldnames or fall back to default legacy order
        if fieldnames.strip():
            cols = [f.strip() for f in fieldnames.split(",") if f.strip()]
        else:
            cols = _LEGACY_DEFAULT_FIELDS
        reader = csv.DictReader(io.StringIO(raw), fieldnames=cols)
    else:
        # Auto-detect: peek at first row to see if it looks like a header
        first_line = raw.split("\n")[0].lower() if raw else ""
        known_cols = {"os_no", "os_year", "location_code", "os_date", "booked_by",
                      "pax_name", "passport_no", "unique_no", "total_items_value",
                      "total_duty_amount", "total_payable"}
        has_header = any(col in first_line for col in known_cols)
        if has_header:
            reader = csv.DictReader(io.StringIO(raw))
        else:
            # No recognisable header — fall back to default legacy column order
            reader = csv.DictReader(io.StringIO(raw), fieldnames=_LEGACY_DEFAULT_FIELDS)

    existing = _existing_os_keys(db)

    inserted = 0
    skipped = 0
    invalid = 0
    rows_read = 0

    for row in reader:
        rows_read += 1
        os_no = (row.get("os_no") or row.get("OS_NO") or "").strip()
        if not os_no:
            invalid += 1
            continue
        try:
            os_year = int(row.get("os_year") or row.get("OS_YEAR") or 0)
        except ValueError:
            invalid += 1
            continue
        location_code = (row.get("location_code") or row.get("LOCATION_CODE") or "").strip()

        key = (os_no, os_year, location_code)
        if key in existing:
            skipped += 1
            continue

        os_date_val = _parse_date(row.get("os_date") or row.get("OS_DATE"))

        master = CopsMaster(
            os_no=os_no,
            os_year=os_year,
            os_date=os_date_val,
            location_code=location_code,
            booked_by=(row.get("booked_by") or row.get("BOOKED_BY") or "").strip() or None,
            pax_name=(row.get("pax_name") or row.get("PAX_NAME") or "").strip() or None,
            passport_no=(row.get("passport_no") or row.get("PASSPORT_NO") or "").strip() or None,
            total_items_value=_flt(row, "total_items_value"),
            total_duty_amount=_flt(row, "total_duty_amount"),
            total_payable=_flt(row, "total_payable"),
            is_draft="N",
        )
        db.add(master)
        existing.add(key)
        inserted += 1

    db.commit()
    post_import_optimise(db)
    return {"inserted": inserted, "skipped": skipped, "invalid": invalid, "rows_read": rows_read}


@router.post("/upload/new")
def upload_new(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_adjn_user),
):
    """
    Import CSV exported from the new system.
    Behaviour: only INSERT new OS cases; skip existing os_no/os_year/location_code.
    """
    try:
        raw = file.file.read().decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read uploaded file.")

    reader = csv.DictReader(io.StringIO(raw))
    existing = _existing_os_keys(db)

    inserted = 0
    skipped = 0

    for row in reader:
        os_no = (row.get("os_no") or "").strip()
        if not os_no:
            continue
        try:
            os_year = int(row.get("os_year") or 0)
        except ValueError:
            continue
        location_code = (row.get("location_code") or "").strip()

        key = (os_no, os_year, location_code)
        if key in existing:
            skipped += 1
            continue

        os_date_str = row.get("os_date")
        try:
            os_date_val = date.fromisoformat(os_date_str) if os_date_str else date.today()
        except Exception:
            os_date_val = date.today()

        master = CopsMaster(
            os_no=os_no,
            os_year=os_year,
            os_date=os_date_val,
            location_code=location_code,
            booked_by=row.get("booked_by"),
            pax_name=row.get("pax_name"),
            passport_no=row.get("passport_no"),
            total_items_value=float(row.get("total_items_value") or 0) if row.get("total_items_value") else 0.0,
            total_duty_amount=float(row.get("total_duty_amount") or 0) if row.get("total_duty_amount") else 0.0,
            total_payable=float(row.get("total_payable") or 0) if row.get("total_payable") else 0.0,
            is_draft=row.get("is_draft") or "N",
        )
        db.add(master)
        existing.add(key)
        inserted += 1

    db.commit()
    post_import_optimise(db)
    return {"inserted": inserted, "skipped": skipped}


def _val(v) -> str:
    """Safely convert any SQLAlchemy column value to a CSV-safe string.
    Strings are stripped so legacy padded values (50-char os_no) are cleaned
    on export and the backup CSV is free of trailing-space artefacts.
    """
    if v is None:
        return ""
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, str):
        return v.strip()
    return str(v)


# All cops_master columns to export (excludes auto-increment PK 'id')
_MASTER_COLS = [
    "os_no", "os_year", "os_date", "location_code", "shift",
    "detention_date", "case_type", "booked_by",
    # Pax
    "pax_name", "pax_name_modified_by_vig", "pax_nationality",
    "passport_no", "passport_date", "pp_issue_place",
    "pax_address1", "pax_address2", "pax_address3",
    "pax_date_of_birth", "pax_status", "residence_at",
    "country_of_departure", "port_of_dep_dest", "date_of_departure",
    "stay_abroad_days", "pax_image_filename", "father_name",
    "old_passport_no", "previous_visits",
    # Flight
    "flight_no", "flight_date",
    # Items summary
    "total_items", "total_items_value", "total_fa_value",
    "dutiable_value", "redeemed_value", "re_export_value", "confiscated_value",
    # Financials
    "total_duty_amount", "rf_amount", "pp_amount", "ref_amount",
    "br_amount", "wh_amount", "other_amount", "total_payable",
    # BR linkage
    "br_no_str", "br_no_num", "br_date_str", "br_amount_str",
    # Status / adjudication
    "is_draft", "os_printed", "os_category", "online_os",
    "adjudication_date", "adjudication_time",
    "adj_offr_name", "adj_offr_designation",
    "adjn_offr_remarks", "adjn_offr_remarks1", "online_adjn",
    # Supdt remarks
    "supdts_remarks", "supdt_remarks2",
    # Admin
    "unique_no", "entry_deleted", "bkup_taken",
    # Detention
    "detained_by", "seal_no", "nationality", "seizure_date",
    # DR linkage
    "dr_no", "dr_year", "total_drs",
    # Misc
    "previous_os_details", "total_pkgs", "closure_ind",
    # Workflow exits
    "quashed", "quashed_by", "quash_reason", "quash_date",
    "rejected", "reject_reason",
]

# All cops_items columns to export (excludes 'id')
_ITEMS_COLS = [
    "os_no", "os_year", "os_date", "location_code",
    "items_sno", "items_desc", "items_qty", "items_uqc",
    "value_per_piece", "items_value", "items_fa",
    "cumulative_duty_rate", "items_duty", "items_duty_type",
    "items_category", "items_sub_category", "items_release_category",
    "items_dr_no", "items_dr_year",
    "unique_no", "entry_deleted", "bkup_taken",
]


@router.get("/export/csv")
def export_csv(
    from_date: Optional[date] = Query(None, alias="from_date"),
    to_date: Optional[date] = Query(None, alias="to_date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export cops_master + cops_items as a restorable ZIP.
    - If from_date and to_date are provided: exports only that date range.
    - If neither is provided: exports the full database (all records).
    The ZIP can be restored via the admin panel Restore section.
    """
    q_master = db.query(CopsMaster)
    if from_date and to_date:
        q_master = q_master.filter(
            CopsMaster.os_date >= from_date, CopsMaster.os_date <= to_date
        )
    masters: List[CopsMaster] = q_master.order_by(CopsMaster.os_date, CopsMaster.os_no).all()

    os_keys = {(m.os_no, m.os_year, m.location_code or "") for m in masters}

    q_items = db.query(CopsItems)
    if from_date and to_date:
        q_items = q_items.filter(
            CopsItems.os_date >= from_date, CopsItems.os_date <= to_date
        )
    items: List[CopsItems] = q_items.order_by(
        CopsItems.os_date, CopsItems.os_no, CopsItems.items_sno
    ).all()
    items = [it for it in items if (it.os_no, it.os_year, it.location_code or "") in os_keys]

    master_buf = io.StringIO()
    mw = csv.writer(master_buf)
    mw.writerow(_MASTER_COLS)
    for m in masters:
        mw.writerow([_val(getattr(m, col, None)) for col in _MASTER_COLS])

    items_buf = io.StringIO()
    iw = csv.writer(items_buf)
    iw.writerow(_ITEMS_COLS)
    for it in items:
        iw.writerow([_val(getattr(it, col, None)) for col in _ITEMS_COLS])

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("cops_master.csv", master_buf.getvalue())
        zf.writestr("cops_items.csv", items_buf.getvalue())
    zip_buf.seek(0)

    today = date.today().isoformat()
    if from_date and to_date:
        filename = f"os_backup_{from_date}_{to_date}.zip"
    else:
        filename = f"cops_full_backup_{today}.zip"

    return StreamingResponse(
        iter([zip_buf.read()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/db")
def export_db(
    current_user: User = Depends(get_current_active_user),
):
    """
    Stream a consistent binary copy of the entire SQLite database.
    Uses sqlite3.backup() into a temp file so the snapshot is crash-safe
    and WAL-flushed. Restoring this file on a new machine gives the complete
    state: OS cases, users, settings, print template history, statutes, masters.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        raise HTTPException(status_code=400, detail="SQLite export is only available for SQLite deployments.")

    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    try:
        os.close(tmp_fd)
        src = sqlite3.connect(db_path)
        dst = sqlite3.connect(tmp_path)
        src.backup(dst)
        src.close()
        dst.close()
        with open(tmp_path, "rb") as f:
            data = f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    today = date.today().isoformat()
    return StreamingResponse(
        iter([data]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="cops_fulldb_{today}.db"'},
    )


# ── Custom Report ─────────────────────────────────────────────────────────────

# Safe allowlist — prevents column-name injection
_REPORT_MASTER_COLS: Set[str] = {
    "os_no", "os_year", "os_date", "location_code", "case_type", "booked_by", "os_category",
    "pax_name", "pax_nationality", "passport_no", "passport_date", "pp_issue_place",
    "pax_address1", "pax_address2", "pax_address3", "pax_date_of_birth",
    "father_name", "residence_at", "country_of_departure", "date_of_departure",
    "port_of_dep_dest", "stay_abroad_days", "old_passport_no", "pax_status",
    "flight_no", "flight_date",
    "total_items", "total_items_value", "total_fa_value", "dutiable_value",
    "redeemed_value", "re_export_value", "confiscated_value",
    "total_duty_amount", "rf_amount", "pp_amount", "ref_amount",
    "br_amount", "wh_amount", "other_amount", "total_payable",
    "br_no_num", "br_date_str", "br_amount_str", "br_no_str",
    "adjudication_date", "adj_offr_name", "adj_offr_designation", "adjn_offr_remarks",
    "online_adjn", "dr_no", "dr_year", "seizure_date", "supdts_remarks",
}

_REPORT_ITEM_COLS: Set[str] = {
    "items_desc", "items_qty", "items_uqc", "items_value", "items_fa",
    "items_duty", "items_duty_type", "items_category", "items_sub_category",
    "items_release_category", "value_per_piece", "cumulative_duty_rate",
}


class CustomReportRequest(BaseModel):
    master_cols: List[str]
    item_cols: List[str] = []
    from_date: Optional[date] = None
    to_date: Optional[date] = None


@router.post("/custom-report")
def custom_report(
    body: CustomReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Build a custom report by selecting any combination of cops_master and
    cops_items columns.

    If item columns are included, the result is expanded (one row per item).
    Master columns are repeated on every item row for the same OS case.
    If a case has no items, it still appears once with empty item fields.
    """
    invalid = (set(body.master_cols) - _REPORT_MASTER_COLS) | (set(body.item_cols) - _REPORT_ITEM_COLS)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown columns: {sorted(invalid)}")
    if not body.master_cols and not body.item_cols:
        raise HTTPException(status_code=400, detail="Select at least one column.")

    q = db.query(CopsMaster).filter(CopsMaster.entry_deleted == "N")
    if body.from_date and body.to_date:
        q = q.filter(CopsMaster.os_date >= body.from_date, CopsMaster.os_date <= body.to_date)
    masters: List[CopsMaster] = q.order_by(CopsMaster.os_year, CopsMaster.os_no).all()

    include_items = bool(body.item_cols)
    all_cols = body.master_cols + body.item_cols
    rows = []

    # Bulk-load all items for the filtered masters in a single query (avoids N+1)
    items_map = defaultdict(list)
    if include_items and masters:
        _CHUNK = 900
        os_keys_list = [(m.os_no, m.os_year, m.location_code or "") for m in masters]
        for i in range(0, len(os_keys_list), _CHUNK):
            chunk = os_keys_list[i:i + _CHUNK]
            pair_filter = or_(*[
                and_(
                    CopsItems.os_no == no,
                    CopsItems.os_year == yr,
                    CopsItems.location_code == lc,
                )
                for no, yr, lc in chunk
            ])
            for it in (
                db.query(CopsItems)
                .filter(pair_filter)
                .order_by(CopsItems.os_no, CopsItems.os_year, CopsItems.items_sno)
                .all()
            ):
                items_map[(it.os_no, it.os_year, it.location_code or "")].append(it)

    for m in masters:
        master_data = {col: _val(getattr(m, col, None)) for col in body.master_cols}
        if include_items:
            m_items = items_map.get((m.os_no, m.os_year, m.location_code or ""), [])
            if m_items:
                for item in m_items:
                    row = dict(master_data)
                    for col in body.item_cols:
                        row[col] = _val(getattr(item, col, None))
                    rows.append(row)
            else:
                row = dict(master_data)
                for col in body.item_cols:
                    row[col] = ""
                rows.append(row)
        else:
            rows.append(master_data)

    return {"columns": all_cols, "rows": rows, "total": len(rows)}
