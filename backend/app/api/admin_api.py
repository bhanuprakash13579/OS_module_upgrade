"""
System-admin API — device registration, user management, backup/restore.
All endpoints require a valid system_admin JWT (obtained via /api/admin/login).
The login endpoint itself is always open (verified against the hardcoded hash).
"""
import csv
import io
import zipfile
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.auth import User
from app.models.offence import CopsMaster, CopsItems
from app.models.config import FeatureFlags
from app.models.security import AllowedDevice
import app.state as state
from app.api.backup import (
    _MASTER_COLS, _ITEMS_COLS, _val, _parse_date, _flt,
    _existing_os_keys, _existing_item_keys,
    _LEGACY_DEFAULT_FIELDS,
    post_import_optimise, set_bulk_pragma,
)
from app.security.admin_auth import (
    verify_admin_credentials,
    create_admin_token,
    require_admin,
)
from app.security.device import (
    is_device_registered,
    register_device,
    get_device_info,
)
from app.security.passwords import pwd_context

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class FeatureFlagUpdate(BaseModel):
    apis_enabled: bool


class AllowedDeviceCreate(BaseModel):
    label: str
    ip_address: str | None = None
    mac_address: str | None = None
    hostname: str | None = None
    notes: str | None = None


class AllowedDeviceUpdate(BaseModel):
    label: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    hostname: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    user_id: str        # login email / username
    user_name: str      # display name
    user_desig: str = ""
    user_pwd: str       # plain-text password (will be hashed server-side)
    user_role: str      # SDO | DC | AC


class UpdateUserRequest(BaseModel):
    user_name: str | None = None
    user_desig: str | None = None
    user_pwd: str | None = None   # plain-text; if provided, re-hashed
    user_status: str | None = None
    user_role: str | None = None


# ── Admin login ───────────────────────────────────────────────────────────────

@router.post("/login")
def admin_login(body: AdminLoginRequest):
    """
    Verify the hardcoded system-admin credentials and return a JWT.
    The credentials are validated against the bcrypt hash compiled into
    the binary — never against the database.
    """
    if not verify_admin_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
        )
    return {"access_token": create_admin_token(), "token_type": "bearer"}


# ── Device registration ───────────────────────────────────────────────────────

@router.get("/device-info", dependencies=[Depends(require_admin)])
def device_info():
    return get_device_info()


@router.post("/register-device", dependencies=[Depends(require_admin)])
def register_this_device():
    """Register the current machine. Requires a valid admin JWT."""
    fingerprint = register_device()
    return {
        "message": "Device registered successfully.",
        "fingerprint": fingerprint,
        **get_device_info(),
    }


# ── Feature Flags ─────────────────────────────────────────────────────────────

@router.get("/features", dependencies=[Depends(require_admin)])
def get_feature_flags(db: Session = Depends(get_db)):
    """Return current feature flag values."""
    flags = db.query(FeatureFlags).first()
    if not flags:
        return {"apis_enabled": False}
    return {"apis_enabled": bool(flags.apis_enabled)}


@router.post("/features", dependencies=[Depends(require_admin)])
def set_feature_flags(body: FeatureFlagUpdate, db: Session = Depends(get_db)):
    """Enable or disable optional modules."""
    flags = db.query(FeatureFlags).first()
    if not flags:
        flags = FeatureFlags(apis_enabled=body.apis_enabled)
        db.add(flags)
    else:
        flags.apis_enabled = body.apis_enabled
    db.commit()
    return {"apis_enabled": bool(flags.apis_enabled)}


def _refresh_whitelist(db: Session):
    """Rebuild state.allowed_ips from the DB after any CRUD operation."""
    devices = db.query(AllowedDevice).filter(AllowedDevice.is_active == True).all()
    state.allowed_ips = {d.ip_address for d in devices if d.ip_address}


# ── App Mode (read-only — mode is set by COPS_ENV, not the admin panel) ───────

@router.get("/mode", dependencies=[Depends(require_admin)])
def get_app_mode():
    """Return current mode (read-only)."""
    return {"prod_mode": state.prod_mode}


# ── Network Access Control (IP/MAC Whitelist) ─────────────────────────────────

@router.get("/devices", dependencies=[Depends(require_admin)])
def list_devices(db: Session = Depends(get_db)):
    """List all allowed devices (active and inactive)."""
    devices = db.query(AllowedDevice).order_by(AllowedDevice.label).all()
    return [
        {
            "id": d.id,
            "label": d.label,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "hostname": d.hostname,
            "is_active": d.is_active,
            "added_by": d.added_by,
            "added_on": d.added_on.isoformat() if d.added_on else None,
            "notes": d.notes,
        }
        for d in devices
    ]


@router.post("/devices", dependencies=[Depends(require_admin)])
def add_device(body: AllowedDeviceCreate, db: Session = Depends(get_db)):
    """Add a device to the whitelist."""
    if not body.label.strip():
        raise HTTPException(status_code=400, detail="Label is required.")
    if body.ip_address:
        existing = db.query(AllowedDevice).filter(
            AllowedDevice.ip_address == body.ip_address,
            AllowedDevice.is_active == True
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"IP {body.ip_address} is already whitelisted as '{existing.label}'.")
    device = AllowedDevice(
        label=body.label.strip(),
        ip_address=body.ip_address,
        mac_address=body.mac_address,
        hostname=body.hostname,
        notes=body.notes,
        added_on=date.today(),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    _refresh_whitelist(db)
    return {"id": device.id, "label": device.label, "ip_address": device.ip_address}


@router.patch("/devices/{device_id}", dependencies=[Depends(require_admin)])
def update_device(device_id: int, body: AllowedDeviceUpdate, db: Session = Depends(get_db)):
    """Update a whitelisted device's details or active status."""
    device = db.query(AllowedDevice).filter(AllowedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    if body.label is not None:
        device.label = body.label.strip()
    if body.ip_address is not None:
        device.ip_address = body.ip_address
    if body.mac_address is not None:
        device.mac_address = body.mac_address
    if body.hostname is not None:
        device.hostname = body.hostname
    if body.is_active is not None:
        device.is_active = body.is_active
    if body.notes is not None:
        device.notes = body.notes
    db.commit()
    _refresh_whitelist(db)
    return {"message": f"Device '{device.label}' updated.", "id": device.id}


@router.delete("/devices/{device_id}", dependencies=[Depends(require_admin)])
def remove_device(device_id: int, db: Session = Depends(get_db)):
    """Remove a device from the whitelist (hard delete)."""
    device = db.query(AllowedDevice).filter(AllowedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    label = device.label
    db.delete(device)
    db.commit()
    _refresh_whitelist(db)
    return {"message": f"Device '{label}' removed from whitelist."}


# ── User management ───────────────────────────────────────────────────────────

@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.user_role, User.user_name).all()
    return [
        {
            "user_id": u.user_id,
            "user_name": u.user_name,
            "user_desig": u.user_desig,
            "user_role": u.user_role,
            "user_status": u.user_status,
            "created_on": u.created_on.isoformat() if u.created_on else None,
        }
        for u in users
    ]


_VALID_ROLES = {"SDO", "DC", "AC"}

@router.post("/users", dependencies=[Depends(require_admin)])
def create_user(body: CreateUserRequest, db: Session = Depends(get_db)):
    if body.user_role not in _VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{body.user_role}'. Valid roles: SDO, DC, AC",
        )
    existing = db.query(User).filter(User.user_id == body.user_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"User '{body.user_id}' already exists.",
        )
    user = User(
        user_id=body.user_id,
        user_name=body.user_name,
        user_desig=body.user_desig,
        user_pwd=pwd_context.hash(body.user_pwd),
        user_role=body.user_role,
        user_status="ACTIVE",
        created_by="sysadmin",
        created_on=date.today(),
    )
    db.add(user)
    db.commit()
    return {"message": f"User '{body.user_id}' created.", "user_role": body.user_role}


@router.patch("/users/{user_id}", dependencies=[Depends(require_admin)])
def update_user(user_id: str, body: UpdateUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if body.user_name is not None:
        user.user_name = body.user_name
    if body.user_desig is not None:
        user.user_desig = body.user_desig
    if body.user_pwd is not None:
        user.user_pwd = pwd_context.hash(body.user_pwd)
    if body.user_status is not None:
        user.user_status = body.user_status
    if body.user_role is not None:
        user.user_role = body.user_role
    db.commit()
    return {"message": f"User '{user_id}' updated."}


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def close_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.user_status = "CLOSED"
    db.commit()
    return {"message": f"User '{user_id}' closed."}


# ── Backup & Restore ──────────────────────────────────────────────────────────

@router.get("/backup/export")
def admin_export_full(db: Session = Depends(get_db), _=Depends(require_admin)):
    """
    Full database export — ALL OS cases and items, no date filter.
    Returns a ZIP containing cops_master.csv and cops_items.csv.
    """
    masters = (
        db.query(CopsMaster)
        .order_by(CopsMaster.os_date, CopsMaster.os_no)
        .all()
    )
    items = (
        db.query(CopsItems)
        .order_by(CopsItems.os_date, CopsItems.os_no, CopsItems.items_sno)
        .all()
    )

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

    filename = f"cops_full_backup_{date.today().isoformat()}.zip"
    return StreamingResponse(
        iter([zip_buf.read()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/backup/restore")
def admin_restore_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Restore from a backup ZIP (produced by /admin/backup/export).
    Inserts missing records only — never overwrites existing data.
    os_no is always trimmed to handle legacy 50-char padded values.
    """
    import sqlalchemy

    try:
        raw_bytes = file.file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot read uploaded file.")

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw_bytes))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="File is not a valid ZIP archive.")

    if "cops_master.csv" not in zf.namelist():
        raise HTTPException(status_code=400, detail="ZIP must contain cops_master.csv")

    # Build type map so we can safely convert CSV strings to Python types
    def _col_type(model, col_name: str) -> str:
        try:
            col = model.__table__.columns[col_name]
            t = col.type
            if isinstance(t, (sqlalchemy.Float, sqlalchemy.Numeric, sqlalchemy.REAL)):
                return "float"
            if isinstance(t, sqlalchemy.Integer):
                return "int"
            if isinstance(t, (sqlalchemy.Date, sqlalchemy.DateTime)):
                return "date"
        except Exception:
            pass
        return "str"

    def _coerce(val: str, kind: str):
        v = val.strip()
        if not v:
            return None
        if kind == "float":
            try:
                return float(v)
            except ValueError:
                return None
        if kind == "int":
            try:
                return int(float(v))
            except ValueError:
                return None
        if kind == "date":
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            return None
        return v  # str

    set_bulk_pragma(db)
    existing_masters = _existing_os_keys(db)
    existing_items = _existing_item_keys(db)
    master_inserted = master_skipped = items_inserted = items_skipped = 0

    # ── Restore cops_master ──────────────────────────────────────────────────
    master_text = zf.read("cops_master.csv").decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(master_text)):
        os_no = (row.get("os_no") or "").strip()
        if not os_no:
            continue
        try:
            os_year = int(row.get("os_year") or 0)
        except ValueError:
            continue
        location_code = (row.get("location_code") or "").strip()
        key = (os_no, os_year, location_code)
        if key in existing_masters:
            master_skipped += 1
            continue

        kwargs = {"os_no": os_no, "os_year": os_year, "location_code": location_code}
        for col in _MASTER_COLS:
            if col in kwargs:
                continue
            raw = row.get(col, "")
            if raw == "" or raw is None:
                continue
            kind = _col_type(CopsMaster, col)
            coerced = _coerce(raw, kind)
            if coerced is not None:
                kwargs[col] = coerced

        db.add(CopsMaster(**kwargs))
        existing_masters.add(key)
        master_inserted += 1

    db.flush()

    # ── Restore cops_items ───────────────────────────────────────────────────
    if "cops_items.csv" in zf.namelist():
        items_text = zf.read("cops_items.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(items_text)):
            os_no = (row.get("os_no") or "").strip()
            if not os_no:
                continue
            try:
                os_year = int(row.get("os_year") or 0)
                items_sno = int(row.get("items_sno") or 0)
            except ValueError:
                continue
            location_code = (row.get("location_code") or "").strip()
            item_key = (os_no, os_year, location_code, items_sno)
            if item_key in existing_items:
                items_skipped += 1
                continue

            kwargs = {
                "os_no": os_no, "os_year": os_year,
                "location_code": location_code, "items_sno": items_sno,
            }
            for col in _ITEMS_COLS:
                if col in kwargs:
                    continue
                raw = row.get(col, "")
                if raw == "" or raw is None:
                    continue
                kind = _col_type(CopsItems, col)
                coerced = _coerce(raw, kind)
                if coerced is not None:
                    kwargs[col] = coerced

            db.add(CopsItems(**kwargs))
            existing_items.add(item_key)
            items_inserted += 1

    db.commit()
    post_import_optimise(db)
    return {
        "master_inserted": master_inserted,
        "master_skipped": master_skipped,
        "items_inserted": items_inserted,
        "items_skipped": items_skipped,
    }


@router.post("/backup/upload-legacy")
def admin_upload_legacy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Import cops_master CSV exported from the old VB6 / MS-Access database.
    Auto-detects header row; falls back to legacy column order if no header found.
    Inserts new records only — skips duplicates.
    """
    try:
        raw = file.file.read().decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot read uploaded file.")

    first_line = raw.split("\n")[0].lower() if raw else ""
    known_cols = {"os_no", "os_year", "location_code", "os_date", "pax_name", "passport_no"}
    has_header = any(col in first_line for col in known_cols)

    if has_header:
        reader = csv.DictReader(io.StringIO(raw))
    else:
        reader = csv.DictReader(io.StringIO(raw), fieldnames=_LEGACY_DEFAULT_FIELDS)

    set_bulk_pragma(db)
    existing = _existing_os_keys(db)
    inserted = skipped = invalid = 0

    for row in reader:
        os_no = (row.get("os_no") or "").strip()
        if not os_no:
            invalid += 1
            continue
        try:
            os_year = int(row.get("os_year") or 0)
        except ValueError:
            invalid += 1
            continue
        location_code = (row.get("location_code") or "").strip()
        key = (os_no, os_year, location_code)
        if key in existing:
            skipped += 1
            continue

        master = CopsMaster(
            os_no=os_no,
            os_year=os_year,
            os_date=_parse_date(row.get("os_date")),
            location_code=location_code,
            booked_by=(row.get("booked_by") or "").strip() or None,
            pax_name=(row.get("pax_name") or "").strip() or None,
            passport_no=(row.get("passport_no") or "").strip() or None,
            total_items_value=_flt(row, "total_items_value"),
            total_duty_amount=_flt(row, "total_duty_amount"),
            total_payable=_flt(row, "total_payable"),
            total_fa_value=_flt(row, "total_fa_value"),
            rf_amount=_flt(row, "rf_amount"),
            pp_amount=_flt(row, "pp_amount"),
            ref_amount=_flt(row, "ref_amount"),
            adj_offr_name=(row.get("adj_offr_name") or "").strip() or None,
            adj_offr_designation=(row.get("adj_offr_designation") or "").strip() or None,
            adjn_offr_remarks=(row.get("adjn_offr_remarks") or "").strip() or None,
            # Import adjudication_date; if missing but officer name is set (legacy adjudicated),
            # fall back to os_date so the case doesn't appear in the pending list
            adjudication_date=(
                _parse_date(row.get("adjudication_date")) if row.get("adjudication_date")
                else (_parse_date(row.get("os_date")) if (row.get("adj_offr_name") or "").strip() else None)
            ),
            is_draft="N",
        )
        db.add(master)
        existing.add(key)
        inserted += 1

    db.commit()
    post_import_optimise(db)
    return {"inserted": inserted, "skipped": skipped, "invalid": invalid}


# Legacy column order for cops_items as exported from old Access DB
_LEGACY_ITEMS_FIELDS = [
    "os_no", "os_date", "os_year", "location_code",
    "items_sno", "items_desc", "items_qty", "items_uqc",
    "items_value", "items_fa", "items_duty", "items_duty_type",
    "items_category", "items_release_category", "items_sub_category",
    "items_dr_no", "items_dr_year", "unique_no",
    "entry_deleted", "bkup_taken", "value_per_piece", "cumulative_duty_rate",
]


@router.post("/backup/upload-legacy-items")
def admin_upload_legacy_items(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Import cops_items CSV exported from the old VB6 / MS-Access database.
    Auto-detects header row; falls back to legacy column order if no header found.
    Inserts new records only — skips duplicates on (os_no, os_year, location_code, items_sno).
    """
    try:
        raw = file.file.read().decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot read uploaded file.")

    first_line = raw.split("\n")[0].lower() if raw else ""
    known_cols = {"os_no", "items_sno", "items_desc", "items_duty", "items_value"}
    has_header = any(col in first_line for col in known_cols)

    if has_header:
        reader = csv.DictReader(io.StringIO(raw))
    else:
        reader = csv.DictReader(io.StringIO(raw), fieldnames=_LEGACY_ITEMS_FIELDS)

    set_bulk_pragma(db)
    existing = _existing_item_keys(db)
    inserted = skipped = invalid = 0

    for row in reader:
        os_no = (row.get("os_no") or "").strip()
        if not os_no:
            invalid += 1
            continue
        try:
            os_year   = int(float(row.get("os_year")   or 0))
            items_sno = int(float(row.get("items_sno") or 0))
        except (ValueError, TypeError):
            invalid += 1
            continue

        location_code = (row.get("location_code") or "").strip()
        key = (os_no, os_year, location_code, items_sno)
        if key in existing:
            skipped += 1
            continue

        item = CopsItems(
            os_no=os_no,
            os_year=os_year,
            location_code=location_code,
            items_sno=items_sno,
            os_date=_parse_date(row.get("os_date")),
            items_desc=(row.get("items_desc") or "").strip() or None,
            items_qty=_flt(row, "items_qty"),
            items_uqc=(row.get("items_uqc") or "").strip() or None,
            items_value=_flt(row, "items_value"),
            items_fa=_flt(row, "items_fa"),
            items_duty=_flt(row, "items_duty"),
            items_duty_type=(row.get("items_duty_type") or "").strip() or None,
            items_category=(row.get("items_category") or "").strip() or None,
            items_sub_category=(row.get("items_sub_category") or "").strip() or None,
            items_release_category=(row.get("items_release_category") or "").strip() or None,
            items_dr_no=int(float(row.get("items_dr_no") or 0)) if (row.get("items_dr_no") or "").strip() else None,
            items_dr_year=int(float(row.get("items_dr_year") or 0)) if (row.get("items_dr_year") or "").strip() else None,
            value_per_piece=_flt(row, "value_per_piece"),
            cumulative_duty_rate=_flt(row, "cumulative_duty_rate"),
            entry_deleted=(row.get("entry_deleted") or "").strip() or None,
        )
        db.add(item)
        existing.add(key)
        inserted += 1

    db.commit()

    # For items imported with no release_category: if the master case has ZERO adjudication
    # evidence, no other adjudicated items, AND is from a recent year (last 2 years) —
    # this is a genuinely pending case. Mark as 'Under OS' so the pending filter works.
    # Old cases (3+ years ago) with null categories are assumed adjudicated in the old system.
    current_year = date.today().year
    db.execute(text("""
        UPDATE cops_items
        SET items_release_category = 'Under OS'
        WHERE items_release_category IS NULL
        AND (os_no, os_year) IN (
            SELECT DISTINCT ci.os_no, ci.os_year
            FROM cops_items ci
            JOIN cops_master cm ON cm.os_no = ci.os_no AND cm.os_year = ci.os_year
            WHERE ci.items_release_category IS NULL
            AND cm.os_year >= :cutoff_year
            AND cm.adj_offr_name IS NULL
            AND cm.adjudication_date IS NULL
            AND (cm.rf_amount IS NULL OR cm.rf_amount <= 0)
            AND (cm.pp_amount IS NULL OR cm.pp_amount <= 0)
            AND (cm.ref_amount IS NULL OR cm.ref_amount <= 0)
            AND (cm.adjn_offr_remarks1 IS NULL OR cm.adjn_offr_remarks1 = '')
            AND NOT EXISTS (
                SELECT 1 FROM cops_items ci2
                WHERE ci2.os_no = ci.os_no AND ci2.os_year = ci.os_year
                AND ci2.items_release_category IN ('CONFS', 'RF', 'REF', 'DUTY')
            )
        )
    """), {"cutoff_year": current_year - 1})
    db.commit()

    post_import_optimise(db)
    return {"inserted": inserted, "skipped": skipped, "invalid": invalid}


# ── MDB Direct Import ─────────────────────────────────────────────────────────

@router.post("/backup/import-mdb")
def admin_import_mdb(
    mdb_path: str = Form(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Import directly from an MS-Access .mdb file on the server.
    Reads cops_master and cops_items via mdbtools (mdb-export).
    Only inserts missing records — never overwrites existing data.
    mdb_path must be an absolute path accessible by the backend process.
    """
    import os
    from app.services.mdb_import import import_from_mdb

    if not os.path.isfile(mdb_path):
        raise HTTPException(status_code=400, detail=f"File not found: {mdb_path}")
    if not mdb_path.lower().endswith(".mdb"):
        raise HTTPException(status_code=400, detail="File must be an .mdb file.")

    try:
        result = import_from_mdb(mdb_path, db)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG — Print Template, Baggage Rules, Special Item Allowances
# ═══════════════════════════════════════════════════════════════════════════════

from app.models.config import PrintTemplateConfig, BaggageRulesConfig, SpecialItemAllowance
from typing import Optional, List


# ── Schemas ───────────────────────────────────────────────────────────────────

class PrintConfigIn(BaseModel):
    field_key: str
    field_label: Optional[str] = None
    field_value: str
    effective_from: date


class BaggageRuleIn(BaseModel):
    rule_key: str
    rule_label: Optional[str] = None
    rule_value: float
    rule_uqc: str
    effective_from: date


class SpecialAllowanceIn(BaseModel):
    item_name: str
    keywords: Optional[str] = None
    allowance_qty: float
    allowance_uqc: str
    effective_from: date
    active: Optional[str] = 'Y'


# ── Helper: point-in-time resolver ───────────────────────────────────────────

def _pit_config(db: Session, ref_date: date) -> dict:
    """
    Return all active config entries as of ref_date.
    For each field_key/rule_key, pick the row with the highest effective_from <= ref_date.
    """
    from sqlalchemy import func

    # Print template
    ptc_rows = db.query(PrintTemplateConfig).filter(
        PrintTemplateConfig.effective_from <= ref_date
    ).all()
    ptc: dict = {}
    for row in ptc_rows:
        existing = ptc.get(row.field_key)
        if existing is None or row.effective_from > existing.effective_from:
            ptc[row.field_key] = row

    # Baggage rules
    brc_rows = db.query(BaggageRulesConfig).filter(
        BaggageRulesConfig.effective_from <= ref_date
    ).all()
    brc: dict = {}
    for row in brc_rows:
        existing = brc.get(row.rule_key)
        if existing is None or row.effective_from > existing.effective_from:
            brc[row.rule_key] = row

    # Special allowances (all active; no point-in-time for new items — use latest effective)
    sia_rows = db.query(SpecialItemAllowance).filter(
        SpecialItemAllowance.active == 'Y',
        SpecialItemAllowance.effective_from <= ref_date
    ).all()
    # Latest version per item_name
    sia: dict = {}
    for row in sia_rows:
        existing = sia.get(row.item_name)
        if existing is None or row.effective_from > existing.effective_from:
            sia[row.item_name] = row

    return {
        "print_template": {k: {"field_key": v.field_key, "field_label": v.field_label,
                               "field_value": v.field_value, "effective_from": str(v.effective_from)}
                           for k, v in ptc.items()},
        "baggage_rules": {k: {"rule_key": v.rule_key, "rule_label": v.rule_label,
                              "rule_value": v.rule_value, "rule_uqc": v.rule_uqc,
                              "effective_from": str(v.effective_from)}
                          for k, v in brc.items()},
        "special_allowances": [
            {"id": v.id, "item_name": v.item_name, "keywords": v.keywords,
             "allowance_qty": v.allowance_qty, "allowance_uqc": v.allowance_uqc,
             "effective_from": str(v.effective_from)}
            for v in sia.values()
        ],
    }


# ── Public: point-in-time config lookup (used by print + preview) ─────────────

@router.get("/config/pit")
def get_pit_config(ref_date: date, db: Session = Depends(get_db)):
    """Return the active config as of ref_date. No auth required (read-only)."""
    return _pit_config(db, ref_date)


# ── Admin: Print Template Config ──────────────────────────────────────────────

@router.get("/config/print-template")
def list_print_template(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(PrintTemplateConfig).order_by(
        PrintTemplateConfig.field_key, PrintTemplateConfig.effective_from
    ).all()
    return [{"id": r.id, "field_key": r.field_key, "field_label": r.field_label,
             "field_value": r.field_value, "effective_from": str(r.effective_from),
             "created_by": r.created_by, "created_at": str(r.created_at or '')}
            for r in rows]


@router.post("/config/print-template", status_code=201)
def add_print_template(body: PrintConfigIn, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = PrintTemplateConfig(
        field_key=body.field_key.strip(),
        field_label=body.field_label,
        field_value=body.field_value.strip(),
        effective_from=body.effective_from,
        created_by=admin.get("sub", "admin"),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "message": "Added"}


@router.put("/config/print-template/{row_id}")
def update_print_template(row_id: int, body: PrintConfigIn,
                           admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(PrintTemplateConfig).filter(PrintTemplateConfig.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    row.field_value    = body.field_value.strip()
    row.effective_from = body.effective_from
    db.commit()
    return {"message": "Updated"}


@router.delete("/config/print-template/{row_id}")
def delete_print_template(row_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(PrintTemplateConfig).filter(PrintTemplateConfig.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}


# ── Admin: Baggage Rules Config ───────────────────────────────────────────────

@router.get("/config/baggage-rules")
def list_baggage_rules(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(BaggageRulesConfig).order_by(
        BaggageRulesConfig.rule_key, BaggageRulesConfig.effective_from
    ).all()
    return [{"id": r.id, "rule_key": r.rule_key, "rule_label": r.rule_label,
             "rule_value": r.rule_value, "rule_uqc": r.rule_uqc,
             "effective_from": str(r.effective_from), "created_by": r.created_by}
            for r in rows]


@router.post("/config/baggage-rules", status_code=201)
def add_baggage_rule(body: BaggageRuleIn, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = BaggageRulesConfig(
        rule_key=body.rule_key.strip(),
        rule_label=body.rule_label,
        rule_value=body.rule_value,
        rule_uqc=body.rule_uqc.strip(),
        effective_from=body.effective_from,
        created_by=admin.get("sub", "admin"),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "message": "Added"}


@router.put("/config/baggage-rules/{row_id}")
def update_baggage_rule(row_id: int, body: BaggageRuleIn,
                         admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(BaggageRulesConfig).filter(BaggageRulesConfig.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    row.rule_value     = body.rule_value
    row.rule_uqc       = body.rule_uqc.strip()
    row.effective_from = body.effective_from
    db.commit()
    return {"message": "Updated"}


@router.delete("/config/baggage-rules/{row_id}")
def delete_baggage_rule(row_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(BaggageRulesConfig).filter(BaggageRulesConfig.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}


# ── Admin: Special Item Allowances ────────────────────────────────────────────

@router.get("/config/special-allowances")
def list_special_allowances(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(SpecialItemAllowance).order_by(
        SpecialItemAllowance.item_name, SpecialItemAllowance.effective_from
    ).all()
    return [{"id": r.id, "item_name": r.item_name, "keywords": r.keywords,
             "allowance_qty": r.allowance_qty, "allowance_uqc": r.allowance_uqc,
             "effective_from": str(r.effective_from), "active": r.active,
             "created_by": r.created_by}
            for r in rows]


@router.post("/config/special-allowances", status_code=201)
def add_special_allowance(body: SpecialAllowanceIn, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = SpecialItemAllowance(
        item_name=body.item_name.strip(),
        keywords=(body.keywords or '').lower().strip(),
        allowance_qty=body.allowance_qty,
        allowance_uqc=body.allowance_uqc.strip(),
        effective_from=body.effective_from,
        active=body.active or 'Y',
        created_by=admin.get("sub", "admin"),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "message": "Added"}


@router.put("/config/special-allowances/{row_id}")
def update_special_allowance(row_id: int, body: SpecialAllowanceIn,
                              admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(SpecialItemAllowance).filter(SpecialItemAllowance.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    row.item_name     = body.item_name.strip()
    row.keywords      = (body.keywords or '').lower().strip()
    row.allowance_qty = body.allowance_qty
    row.allowance_uqc = body.allowance_uqc.strip()
    row.effective_from = body.effective_from
    row.active        = body.active or 'Y'
    db.commit()
    return {"message": "Updated"}


@router.delete("/config/special-allowances/{row_id}")
def delete_special_allowance(row_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.query(SpecialItemAllowance).filter(SpecialItemAllowance.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}
