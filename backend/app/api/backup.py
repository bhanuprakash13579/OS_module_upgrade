from collections import defaultdict
from datetime import date, datetime
import csv
import io
import os
import sqlite3
import tempfile
import zipfile
from typing import List, Optional, Set, Tuple

try:
    import pyzipper as _pyzipper   # AES-256 encrypted ZIPs
    _PYZIPPER_AVAILABLE = True
except ImportError:
    _pyzipper = None               # type: ignore[assignment]
    _PYZIPPER_AVAILABLE = False

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from sqlalchemy import text, or_, and_, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, get_cipher_module, get_db_key, get_db_path
from app.models.offence import CopsMaster, CopsItems
from app.models.auth import User
from app.security.admin_auth import require_admin
from app.services.auth import get_adjn_user, get_current_active_user


router = APIRouter()


# ── Streaming helpers ────────────────────────────────────────────────────────

def _cleanup_temp(path: str):
    """Delete a temp file; silently ignore errors (already gone, etc.)."""
    try:
        os.unlink(path)
    except OSError:
        pass


def _iter_bytesio(buf: io.BytesIO, chunk_size: int = 1024 * 1024):
    """Yield *chunk_size* byte slices from a BytesIO (default 1 MB)."""
    while True:
        chunk = buf.read(chunk_size)
        if not chunk:
            break
        yield chunk


# ── Shared bulk-import optimiser ─────────────────────────────────────────────

_COPS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_cops_master_os_no_year          ON cops_master (os_no, os_year)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_draft_deleted        ON cops_master (entry_deleted, is_draft)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_adjudication_date    ON cops_master (adjudication_date)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_quashed_rejected     ON cops_master (quashed, rejected)",
    # New performance indexes added in v3 optimisation pass
    "CREATE INDEX IF NOT EXISTS ix_cops_master_os_year             ON cops_master (os_year)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_adj_offr_name       ON cops_master (adj_offr_name)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_online_adjn         ON cops_master (online_adjn)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_adjudication_time   ON cops_master (adjudication_time)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_closure_ind         ON cops_master (closure_ind)",
    "CREATE INDEX IF NOT EXISTS ix_cops_master_pending_composite   ON cops_master (entry_deleted, is_draft, adjudication_date, adj_offr_name)",
    "CREATE INDEX IF NOT EXISTS ix_cops_items_os_no_year           ON cops_items  (os_no, os_year)",
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
        except (ValueError, TypeError):
            import logging as _log
            _log.getLogger(__name__).warning("Invalid os_date %r in CSV row — defaulting to today", os_date_str)
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
    "is_draft", "is_legacy", "is_offline_adjudication", "file_spot", "os_printed", "os_category", "online_os",
    "adjudication_date", "adjudication_time",
    "adj_offr_name", "adj_offr_designation",
    "adjn_offr_remarks", "adjn_offr_remarks1", "adjn_section_ref", "online_adjn",
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
    # Post-adjudication receipts
    "post_adj_br_entries", "post_adj_dr_no", "post_adj_dr_date",
    # Soft-delete audit trail
    "deleted_by", "deleted_reason", "deleted_on",
]

# All cops_items columns to export (excludes 'id')
_ITEMS_COLS = [
    "os_no", "os_year", "os_date", "location_code",
    "items_sno", "items_desc", "items_qty", "items_uqc",
    "value_per_piece", "items_value", "items_fa",
    "cumulative_duty_rate", "items_duty", "items_duty_type",
    "items_category", "items_sub_category", "items_release_category",
    "items_dr_no", "items_dr_year",
    "items_fa_type", "items_fa_qty", "items_fa_uqc",
    "unique_no", "entry_deleted", "bkup_taken",
]

# ── BR / DR export column lists ───────────────────────────────────────────────

_BR_MASTER_COLS = [
    "br_no", "br_date", "br_type", "br_year", "br_shift",
    "flight_no", "flight_date",
    "pax_name", "pax_nationality", "passport_no", "passport_date",
    "passport_issue_place", "pax_address1", "pax_address2", "pax_address3",
    "pax_date_of_birth", "pax_status", "residence_at",
    "country_of_departure", "departure_date",
    "os_no", "os_date", "dr_no", "dr_date",
    "total_items_value", "total_fa_value", "total_duty_amount",
    "rf_amount", "pp_amount", "ref_amount", "wh_amount", "other_amount", "br_amount",
    "challan_no", "bank_date", "bank_shift", "batch_date", "batch_shift",
    "dc_code", "unique_no", "location_code", "login_id",
    "entry_deleted", "bkup_taken", "br_printed", "ff_ind",
    "image_filename", "table_name", "arrived_from", "br_amount_str", "br_no_str",
    "abroad_stay", "total_fa_availed", "actual_br_type", "total_payable",
    "_availed_remarks",  # ORM attribute name; DB column is availed_remarks
]

_BR_ITEMS_COLS = [
    "br_no", "br_date", "br_shift", "br_type",
    "items_sno", "items_desc", "items_qty", "items_uqc", "items_value",
    "items_fa", "items_bcd", "items_cvd", "items_cess", "items_hec", "items_duty",
    "items_duty_type", "items_category",
    "items_dr_no", "items_dr_year", "items_release_category",
    "flight_no", "bank_date", "bank_shift", "batch_date", "batch_shift",
    "unique_no", "location_code", "login_id", "entry_deleted", "bkup_taken",
]

_DR_MASTER_COLS = [
    "dr_no", "dr_date", "dr_year", "dr_type",
    "pax_name", "passport_no", "passport_date",
    "pax_address1", "pax_address2", "pax_address3",
    "port_of_departure", "flight_no", "flight_date",
    "total_items_value",
    "closure_ind", "closure_remarks", "closure_date",
    "closed_batch_date", "closed_batch_shift",
    "warehouse_no",
    "entry_deleted", "unique_no", "location_code", "login_id",
    "detained_by", "detained_pkg_no", "detained_pkg_type",
    "seal_no", "dr_printed", "detention_reasons",
    "seizure_date", "os_no", "receipt_by_who",
]

_DR_ITEMS_COLS = [
    "dr_no", "dr_date", "dr_type",
    "items_sno", "items_desc", "items_qty", "items_uqc", "items_value",
    "items_fa", "items_release_category",
    "receipt_by_who", "item_closure_remarks",
    "detained_pkg_no", "detained_pkg_type",
    "unique_no", "location_code",
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
    def _sc(cols):
        """Map ORM attribute names to SQL column names (strips leading underscore)."""
        return ", ".join(c.lstrip("_") for c in cols)

    # ── Raw SQL queries — bypass ORM hydration overhead ───────────────────────
    if from_date and to_date:
        p = {"fd": from_date, "td": to_date}
        master_rows    = db.execute(text(
            f"SELECT {_sc(_MASTER_COLS)} FROM cops_master "
            "WHERE os_date >= :fd AND os_date <= :td ORDER BY os_date, os_no"
        ), p).fetchall()
        # JOIN pushes item filtering into the DB — no Python-level set filtering
        items_rows     = db.execute(text(
            f"SELECT {', '.join('ci.' + c for c in _ITEMS_COLS)} "
            "FROM cops_items ci "
            "INNER JOIN cops_master cm ON ci.os_no = cm.os_no AND ci.os_year = cm.os_year "
            "WHERE cm.os_date >= :fd AND cm.os_date <= :td "
            "ORDER BY ci.os_date, ci.os_no, ci.items_sno"
        ), p).fetchall()
        br_master_rows = db.execute(text(
            f"SELECT {_sc(_BR_MASTER_COLS)} FROM br_master "
            "WHERE br_date >= :fd AND br_date <= :td ORDER BY br_date, br_no"
        ), p).fetchall()
        br_items_rows  = db.execute(text(
            f"SELECT {_sc(_BR_ITEMS_COLS)} FROM br_items "
            "WHERE br_date >= :fd AND br_date <= :td ORDER BY br_date, br_no, items_sno"
        ), p).fetchall()
        dr_master_rows = db.execute(text(
            f"SELECT {_sc(_DR_MASTER_COLS)} FROM dr_master "
            "WHERE dr_date >= :fd AND dr_date <= :td ORDER BY dr_date, dr_no"
        ), p).fetchall()
        dr_items_rows  = db.execute(text(
            f"SELECT {_sc(_DR_ITEMS_COLS)} FROM dr_items "
            "WHERE dr_date >= :fd AND dr_date <= :td ORDER BY dr_date, dr_no, items_sno"
        ), p).fetchall()
    else:
        master_rows    = db.execute(text(f"SELECT {_sc(_MASTER_COLS)} FROM cops_master ORDER BY os_date, os_no")).fetchall()
        items_rows     = db.execute(text(f"SELECT {_sc(_ITEMS_COLS)} FROM cops_items ORDER BY os_date, os_no, items_sno")).fetchall()
        br_master_rows = db.execute(text(f"SELECT {_sc(_BR_MASTER_COLS)} FROM br_master ORDER BY br_date, br_no")).fetchall()
        br_items_rows  = db.execute(text(f"SELECT {_sc(_BR_ITEMS_COLS)} FROM br_items ORDER BY br_date, br_no, items_sno")).fetchall()
        dr_master_rows = db.execute(text(f"SELECT {_sc(_DR_MASTER_COLS)} FROM dr_master ORDER BY dr_date, dr_no")).fetchall()
        dr_items_rows  = db.execute(text(f"SELECT {_sc(_DR_ITEMS_COLS)} FROM dr_items ORDER BY dr_date, dr_no, items_sno")).fetchall()

    def _to_csv(headers, rows) -> bytes:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(headers)
        w.writerows(([_val(v) for v in row] for row in rows))
        return buf.getvalue().encode("utf-8")

    # ── Write ZIP to temp file (same pattern as export_db — no BytesIO bloat) ─
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    try:
        os.close(tmp_fd)
        if _PYZIPPER_AVAILABLE:
            from app.security.device import get_zip_password
            zf_ctx = _pyzipper.AESZipFile(
                tmp_path, mode="w",
                compression=zipfile.ZIP_STORED,
                encryption=_pyzipper.WZ_AES,
            )
            zf_ctx.setpassword(get_zip_password())
        else:
            zf_ctx = zipfile.ZipFile(tmp_path, mode="w",
                                     compression=zipfile.ZIP_STORED)
        with zf_ctx as zf:
            zf.writestr("cops_master.csv",  _to_csv(_MASTER_COLS,                             master_rows))
            zf.writestr("cops_items.csv",   _to_csv(_ITEMS_COLS,                              items_rows))
            zf.writestr("br_master.csv",    _to_csv([c.lstrip("_") for c in _BR_MASTER_COLS], br_master_rows))
            zf.writestr("br_items.csv",     _to_csv(_BR_ITEMS_COLS,                           br_items_rows))
            zf.writestr("dr_master.csv",    _to_csv(_DR_MASTER_COLS,                          dr_master_rows))
            zf.writestr("dr_items.csv",     _to_csv(_DR_ITEMS_COLS,                           dr_items_rows))
    except Exception:
        _cleanup_temp(tmp_path)
        raise

    today = date.today().isoformat()
    filename = (f"os_backup_{from_date}_{to_date}.zip" if from_date and to_date
                else f"cops_full_backup_{today}.zip")
    return FileResponse(
        tmp_path,
        media_type="application/zip",
        filename=filename,
        headers={"Content-Encoding": "identity"},
        background=BackgroundTask(_cleanup_temp, tmp_path),
    )


@router.get("/export/db")
def export_db(
    current_user: User = Depends(get_current_active_user),
):
    """
    Stream a consistent binary copy of the entire SQLite database.

    Uses sqlite3.backup() (or sqlcipher3.backup() when encryption is active)
    into a temp file so the snapshot is WAL-flushed and crash-safe.

    If SQLCipher encryption is enabled (the default), the exported file is also
    encrypted with the same AES-256 key.  To open it manually use DB Browser
    for SQLite with the SQLCipher plugin and the hex key from GET /db-cipher-key
    (admin auth required).
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        raise HTTPException(status_code=400, detail="SQLite export is only available for SQLite deployments.")

    db_path = get_db_path()
    if not db_path:
        raise HTTPException(status_code=500, detail="Could not resolve database path.")

    cipher = get_cipher_module()
    db_key = get_db_key()

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    src = dst = None
    try:
        os.close(tmp_fd)

        if cipher and db_key:
            # ── Encrypted path — use sqlcipher3 for both src and dst ──────────
            hex_pragma = f"PRAGMA key = \"x'{db_key}'\""
            src = cipher.connect(db_path)
            src.execute(hex_pragma)
            dst = cipher.connect(tmp_path)
            dst.execute(hex_pragma)
            src.backup(dst)
        else:
            # ── Plaintext fallback ────────────────────────────────────────────
            src = sqlite3.connect(db_path)
            dst = sqlite3.connect(tmp_path)
            src.backup(dst)
    except Exception:
        for conn in (src, dst):
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
        _cleanup_temp(tmp_path)
        raise
    finally:
        for conn in (src, dst):
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    # Stream directly from disk — no memory copy.  BackgroundTask deletes
    # the temp file after the last byte has been sent to the client.
    today = date.today().isoformat()
    suffix = "_enc" if (cipher and db_key) else ""
    return FileResponse(
        tmp_path,
        media_type="application/octet-stream",
        filename=f"cops_fulldb_{today}{suffix}.db",
        headers={"Content-Encoding": "identity"},
        background=BackgroundTask(_cleanup_temp, tmp_path),
    )


@router.get("/db-cipher-key")
def get_db_cipher_key(
    _admin=Depends(require_admin),
):
    """
    Return the AES-256 SQLCipher hex key used to encrypt the database.

    This endpoint is admin-only.  Use this key to manually open a copied
    .db file in DB Browser for SQLite (with SQLCipher plugin):
      1. Open Database → select the .db file
      2. Choose "SQLCipher 4 defaults" cipher settings
      3. Key format → "Raw key / Hex key"
      4. Paste the 64-char hex string returned here → OK

    If encryption is not active (sqlcipher3 not installed), returns null.
    """
    from app.security.device import get_zip_password
    db_key = get_db_key()
    zip_pw = get_zip_password().decode()
    return {
        "encrypted": db_key is not None,
        "key": db_key,          # 64-char hex AES-256 key, or null
        "algorithm": "AES-256-CBC (SQLCipher 4)" if db_key else None,
        "key_format": "raw hex" if db_key else None,
        "zip_password": zip_pw,
        "zip_password_note": (
            "Type this string in 7-Zip / WinRAR when opening an exported backup ZIP."
        ),
        "note": (
            "Keep these secrets. Anyone with the DB key AND the database file "
            "can read all data. The ZIP password protects exported CSV backups."
        ) if db_key else "Database is not encrypted.",
    }


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
    "adjn_section_ref",
    "online_adjn", "dr_no", "dr_year", "seizure_date", "supdts_remarks",
    "post_adj_br_entries", "post_adj_dr_no", "post_adj_dr_date",
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
    case_type: Optional[str] = None  # "Export Case" | "Arrival Case" | None (all)


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
    if body.case_type:
        if (body.case_type or "").strip().upper() == "EXPORT CASE":
            q = q.filter(func.upper(CopsMaster.case_type) == "EXPORT CASE")
        else:
            q = q.filter(
                or_(CopsMaster.case_type.is_(None), func.upper(CopsMaster.case_type) != "EXPORT CASE")
            )
    masters: List[CopsMaster] = q.order_by(CopsMaster.os_year, CopsMaster.os_no).all()

    include_items = bool(body.item_cols)
    all_cols = body.master_cols + body.item_cols
    rows = []

    # Bulk-load all items for the filtered masters in a single query (avoids N+1).
    # Use JOIN on master IDs (chunked at 900) — safer than a raw OR chain.
    items_map = defaultdict(list)
    if include_items and masters:
        _CHUNK = 900
        master_ids = [m.id for m in masters]
        for i in range(0, len(master_ids), _CHUNK):
            chunk = master_ids[i:i + _CHUNK]
            for it in (
                db.query(CopsItems)
                .join(CopsMaster, and_(CopsItems.os_no == CopsMaster.os_no,
                                       CopsItems.os_year == CopsMaster.os_year))
                .filter(CopsMaster.id.in_(chunk))
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


# ── Adjudication Officers Summary PDF ────────────────────────────────────────

class AdjudicationSummaryRequest(BaseModel):
    from_date: date
    to_date: date


@router.post("/adjudication-summary-pdf")
def adjudication_summary_pdf(
    body: AdjudicationSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Aggregate all adjudicated cases (by adjudication_date) in the given period,
    group by officer name, and return a landscape A4 PDF report.
    """
    from weasyprint import HTML as WeasyHTML
    from fastapi.responses import Response

    data = (
        db.query(
            CopsMaster.adj_offr_name,
            func.max(CopsMaster.adj_offr_designation).label("designation"),
            func.count(CopsMaster.id).label("cases"),
            func.coalesce(func.sum(CopsMaster.total_items_value), 0.0).label("total_value"),
            func.coalesce(func.sum(CopsMaster.dutiable_value), 0.0).label("dutiable_value"),
            func.coalesce(func.sum(CopsMaster.redeemed_value), 0.0).label("redeemed_value"),
            func.coalesce(func.sum(CopsMaster.re_export_value), 0.0).label("re_export_value"),
            func.coalesce(func.sum(CopsMaster.confiscated_value), 0.0).label("confiscated_value"),
            func.coalesce(func.sum(CopsMaster.total_duty_amount), 0.0).label("duty_levied"),
            func.coalesce(func.sum(CopsMaster.rf_amount), 0.0).label("rf_levied"),
            func.coalesce(func.sum(CopsMaster.ref_amount), 0.0).label("ref_levied"),
            func.coalesce(func.sum(CopsMaster.pp_amount), 0.0).label("pp_levied"),
        )
        .filter(
            CopsMaster.entry_deleted == "N",
            CopsMaster.adj_offr_name.isnot(None),
            CopsMaster.adj_offr_name != "",
            CopsMaster.adjudication_date >= body.from_date,
            CopsMaster.adjudication_date <= body.to_date,
        )
        .group_by(CopsMaster.adj_offr_name)
        .order_by(CopsMaster.adj_offr_name)
        .all()
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail="No adjudicated cases found for the selected date range.",
        )

    def fmt(n) -> str:
        """Indian-style comma formatting. Returns — for zero/null."""
        val = float(n or 0)
        if val == 0:
            return "\u2014"
        n_int = int(round(abs(val)))
        s = str(n_int)
        if len(s) <= 3:
            result = s
        else:
            result = s[-3:]
            s = s[:-3]
            parts = []
            while len(s) > 2:
                parts.append(s[-2:])
                s = s[:-2]
            if s:
                parts.append(s)
            result = ",".join(reversed(parts)) + "," + result
        return result

    totals = {
        "cases": sum(r.cases for r in data),
        "total_value":      sum(float(r.total_value or 0)      for r in data),
        "dutiable_value":   sum(float(r.dutiable_value or 0)   for r in data),
        "redeemed_value":   sum(float(r.redeemed_value or 0)   for r in data),
        "re_export_value":  sum(float(r.re_export_value or 0)  for r in data),
        "confiscated_value":sum(float(r.confiscated_value or 0)for r in data),
        "duty_levied":      sum(float(r.duty_levied or 0)      for r in data),
        "rf_levied":        sum(float(r.rf_levied or 0)        for r in data),
        "ref_levied":       sum(float(r.ref_levied or 0)       for r in data),
        "pp_levied":        sum(float(r.pp_levied or 0)        for r in data),
    }

    from_str = body.from_date.strftime("%d/%m/%Y")
    to_str   = body.to_date.strftime("%d/%m/%Y")
    gen_dt   = datetime.now().strftime("%d/%m/%Y %H:%M")

    rows_html = ""
    for i, r in enumerate(data, 1):
        desig = r.designation or ""
        rows_html += f"""
        <tr>
          <td class="ctr">{i}</td>
          <td class="name">{r.adj_offr_name or ""}{"<br><span class='desig'>" + desig + "</span>" if desig else ""}</td>
          <td class="num">{r.cases}</td>
          <td class="num">{fmt(r.total_value)}</td>
          <td class="num">{fmt(r.dutiable_value)}</td>
          <td class="num">{fmt(r.redeemed_value)}</td>
          <td class="num">{fmt(r.re_export_value)}</td>
          <td class="num">{fmt(r.confiscated_value)}</td>
          <td class="num">{fmt(r.duty_levied)}</td>
          <td class="num">{fmt(r.rf_levied)}</td>
          <td class="num">{fmt(r.ref_levied)}</td>
          <td class="num">{fmt(r.pp_levied)}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4 landscape;
    margin: 10mm 8mm 14mm 8mm;
  }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8pt;
    color: #111;
    margin: 0;
  }}
  .report-header {{
    text-align: center;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 2px solid #1e4a72;
  }}
  .report-header .title {{
    font-size: 11pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .report-header .subtitle {{
    font-size: 9pt;
    font-weight: bold;
    margin-top: 3px;
    color: #1e4a72;
  }}
  .report-header .meta {{
    font-size: 7.5pt;
    color: #555;
    margin-top: 2px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 4px;
  }}
  th {{
    background-color: #1e4a72;
    color: #fff;
    font-weight: bold;
    font-size: 7pt;
    text-align: center;
    padding: 5px 3px;
    border: 1px solid #163d60;
    line-height: 1.3;
  }}
  td {{
    border: 1px solid #c8d4e0;
    padding: 3.5px 4px;
    font-size: 7.5pt;
    vertical-align: middle;
  }}
  td.ctr  {{ text-align: center; color: #555; }}
  td.name {{ text-align: left; font-weight: 600; line-height: 1.35; }}
  td.num  {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .desig  {{ font-size: 6.5pt; color: #666; font-weight: normal; }}
  tr:nth-child(even) {{ background-color: #f2f7fc; }}
  tr:hover {{ background-color: #e8f1fa; }}
  .total-row td {{
    background-color: #1e4a72 !important;
    color: #fff !important;
    font-weight: bold;
    font-size: 7.5pt;
    border-color: #163d60;
  }}
  .footer {{
    margin-top: 8px;
    font-size: 6.5pt;
    color: #666;
    display: flex;
    justify-content: space-between;
    border-top: 1px solid #ccc;
    padding-top: 4px;
  }}
</style>
</head>
<body>
  <div class="report-header">
    <div class="title">Adjudicating Officers — Performance Summary Report</div>
    <div class="subtitle">Period : {from_str} &nbsp;to&nbsp; {to_str}</div>
    <div class="meta">Filtered by adjudication date &nbsp;|&nbsp; All amounts in Indian Rupees (₹), rounded to nearest rupee &nbsp;|&nbsp; &mdash; denotes zero</div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:3%">S.<br>No.</th>
        <th style="width:13%">Officer Name /<br>Designation</th>
        <th style="width:5%">No. of<br>Cases</th>
        <th style="width:8%">Total Value<br>Under OS (₹)</th>
        <th style="width:8%">Dutiable<br>Value (₹)</th>
        <th style="width:8%">Redeemed<br>Value (₹)</th>
        <th style="width:8%">Re-export<br>Value (₹)</th>
        <th style="width:8%">Abs. Confiscated<br>Value (₹)</th>
        <th style="width:8%">Duty<br>Levied (₹)</th>
        <th style="width:8%">R.F.<br>Levied (₹)</th>
        <th style="width:8%">R.E.F.<br>Levied (₹)</th>
        <th style="width:8%">Personal<br>Penalty (₹)</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
      <tr class="total-row">
        <td class="ctr" colspan="2">GRAND TOTAL</td>
        <td class="num">{totals["cases"]}</td>
        <td class="num">{fmt(totals["total_value"])}</td>
        <td class="num">{fmt(totals["dutiable_value"])}</td>
        <td class="num">{fmt(totals["redeemed_value"])}</td>
        <td class="num">{fmt(totals["re_export_value"])}</td>
        <td class="num">{fmt(totals["confiscated_value"])}</td>
        <td class="num">{fmt(totals["duty_levied"])}</td>
        <td class="num">{fmt(totals["rf_levied"])}</td>
        <td class="num">{fmt(totals["ref_levied"])}</td>
        <td class="num">{fmt(totals["pp_levied"])}</td>
      </tr>
    </tbody>
  </table>

  <div class="footer">
    <span>COPS &mdash; Internal Use Only</span>
    <span>Generated on {gen_dt}</span>
  </div>
</body>
</html>"""

    pdf_bytes = WeasyHTML(string=html).write_pdf()
    from_label = body.from_date.strftime("%Y%m%d")
    to_label   = body.to_date.strftime("%Y%m%d")
    filename   = f"adjn_summary_{from_label}_to_{to_label}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
