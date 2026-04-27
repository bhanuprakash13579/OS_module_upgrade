"""
System-admin API — device registration, user management, backup/restore.
All endpoints require a valid system_admin JWT (obtained via /api/admin/login).
The login endpoint itself is always open (verified against the hardcoded hash).
"""
import csv
import io
import logging
import os
import shutil
import sqlite3 as _stdlib_sqlite3
import tempfile
import threading
import time
import zipfile

_log = logging.getLogger(__name__)
from datetime import date, datetime, timezone

try:
    import pyzipper as _pyzipper   # AES-256 encrypted ZIPs
    _PYZIPPER_AVAILABLE = True
except ImportError:
    _pyzipper = None               # type: ignore[assignment]
    _PYZIPPER_AVAILABLE = False

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from fastapi.responses import FileResponse, StreamingResponse, Response
from starlette.background import BackgroundTask
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.models.auth import User
from app.models.offence import CopsMaster, CopsItems
from app.models.config import (
    FeatureFlags, PrintTemplateConfig, BaggageRulesConfig,
    SpecialItemAllowance, ShiftTimingMaster, MarginMaster,
)
from app.models.statutes import LegalStatute
from app.models.security import AllowedDevice
from app.models.masters import (
    DcMaster, AirlinesMast, ArrivalFlightMaster, AirportMaster,
    NationalityMaster, PortMaster, ItemCatMaster, DutyRateMaster, BrNoLimits,
)
from app.models.baggage import BrMaster, BrItems
from app.api.masters import bust_all_master_caches
from app.models.detention import DrMaster, DrItems
from app.models.fuel import FuelMaster
from app.models.offence import OsMaster, ItemTrans
from app.models.warehouse import WhMaster, WhItems, WhRelease, WhLocationChange, ValuablesMaster, ValuablesItems
from app.models.mhb import MahazarMaster, MahazarItems, MhbMaster, MhbItems
from app.models.appeal import AppealMaster, AppealItems
from app.models.revenue import Revenue, RevChallans, ChallanMaster
import app.state as state
from app.api.backup import (
    _MASTER_COLS, _ITEMS_COLS, _val, _parse_date, _flt,
    _existing_os_keys, _existing_item_keys,
    _LEGACY_DEFAULT_FIELDS,
    post_import_optimise, set_bulk_pragma,
    _BR_MASTER_COLS, _BR_ITEMS_COLS, _DR_MASTER_COLS, _DR_ITEMS_COLS,
)
from app.security.admin_auth import (
    verify_admin_credentials,
    create_admin_token,
    require_admin,
    _ADMIN_USERNAME,
)
from app.security.device import (
    is_device_registered,
    register_device,
    get_device_info,
    get_zip_password,
)
from app.database import get_cipher_module, get_db_key, get_db_path, migrate_plaintext_to_encrypted
from app.security.passwords import pwd_context
from app.services.auth import get_current_active_user
from collections import defaultdict as _defaultdict

# ── Admin login rate limiting ─────────────────────────────────────────────────
_admin_login_attempts: dict = _defaultdict(list)
_ADMIN_RATE_WINDOW = 300   # 5 minutes
_ADMIN_RATE_MAX    = 10    # max failed attempts per window

def _admin_check_rate_limit(ip: str) -> bool:
    if not state.prod_mode:
        return True
    now = time.time()
    window_start = now - _ADMIN_RATE_WINDOW
    attempts = [t for t in _admin_login_attempts[ip] if t > window_start]
    _admin_login_attempts[ip] = attempts
    if len(attempts) >= _ADMIN_RATE_MAX:
        return False
    _admin_login_attempts[ip].append(now)
    return True

# ── Generic table registry ────────────────────────────────────────────────────
# Each entry: (csv_name, model, unique_cols_tuple, order_cols_tuple)
_TABLE_REGISTRY = [
    # Master tables
    ("dc_master.csv",              DcMaster,            ("dc_code",),                              ("dc_code",)),
    ("airlines_mast.csv",          AirlinesMast,        ("airline_code",),                         ("airline_code",)),
    ("arrival_flight_master.csv",  ArrivalFlightMaster, ("flight_no", "airline_code"),             ("flight_no", "airline_code")),
    ("airport_master.csv",         AirportMaster,       ("airport_name",),                         ("airport_name",)),
    ("nationality_master.csv",     NationalityMaster,   ("nationality",),                          ("nationality",)),
    ("port_master.csv",            PortMaster,          ("port_of_departure",),                    ("port_of_departure",)),
    ("item_cat_master.csv",        ItemCatMaster,       ("category_code",),                        ("category_code",)),
    ("duty_rate_master.csv",       DutyRateMaster,      ("duty_category", "from_date"),            ("duty_category", "from_date")),
    ("br_no_limits.csv",           BrNoLimits,          ("br_type",),                              ("br_type",)),
    # Baggage
    ("br_master.csv",              BrMaster,            ("br_no", "br_date", "br_type"),           ("br_date", "br_no")),
    ("br_items.csv",               BrItems,             ("br_no", "br_date", "items_sno"),         ("br_date", "br_no", "items_sno")),
    # Detention
    ("dr_master.csv",              DrMaster,            ("dr_no", "dr_date"),                      ("dr_date", "dr_no")),
    ("dr_items.csv",               DrItems,             ("dr_no", "items_sno"),                    ("dr_no", "items_sno")),
    # Fuel
    ("fuel_master.csv",            FuelMaster,          ("br_no", "br_date"),                      ("br_date", "br_no")),
    # OS (offence)
    ("os_master.csv",              OsMaster,            ("osnumber", "osdate", "location_code"),   ("osdate", "osnumber")),
    ("item_trans.csv",             ItemTrans,           ("item_os_no", "item_osdate", "item_no"),  ("item_osdate", "item_os_no")),
    # Warehouse
    ("wh_master.csv",              WhMaster,            ("wh_no", "wh_date"),                      ("wh_date", "wh_no")),
    ("wh_items.csv",               WhItems,             ("wh_no", "items_sno"),                    ("wh_no", "items_sno")),
    ("wh_release.csv",             WhRelease,           ("wh_no", "wh_release_no"),                ("wh_no", "wh_release_no")),
    ("wh_location_change.csv",     WhLocationChange,    ("wh_no", "change_date", "old_location"),  ("wh_no", "change_date")),
    ("valuables_master.csv",       ValuablesMaster,     ("wh_no", "wh_date"),                      ("wh_date", "wh_no")),
    ("valuables_items.csv",        ValuablesItems,      ("wh_no", "items_sno"),                    ("wh_no", "items_sno")),
    # MHB
    ("mahazar_master.csv",         MahazarMaster,       ("os_no", "system_reference_no"),          ("os_no",)),
    ("mahazar_items.csv",          MahazarItems,        ("os_no", "system_reference_no", "items_sno"), ("os_no", "system_reference_no")),
    ("mhb_master.csv",             MhbMaster,           ("mhb_no", "mhb_year"),                    ("mhb_no", "mhb_year")),
    ("mhb_items.csv",              MhbItems,            ("mhb_no", "items_sno"),                   ("mhb_no", "items_sno")),
    # Appeal
    ("appeal_master.csv",          AppealMaster,        ("os_no", "os_date"),                      ("os_date", "os_no")),
    ("appeal_items.csv",           AppealItems,         ("os_no", "items_sno"),                    ("os_no", "items_sno")),
    # Revenue
    ("revenue.csv",                Revenue,             ("rev_date",),                             ("rev_date",)),
    ("rev_challans.csv",           RevChallans,         ("rev_date", "challan_no"),                ("rev_date",)),
    ("challan_master.csv",         ChallanMaster,       ("batch_date", "batch_shift", "sdo_code", "challan_no"), ("batch_date", "sdo_code")),
]


def _model_cols(model) -> list:
    """All column names for a model, excluding 'id'."""
    return [c.name for c in model.__table__.columns if c.name != "id"]


def _col_type_generic(model, col_name: str) -> str:
    import sqlalchemy
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


def _coerce_val(val: str, kind: str):
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
        from datetime import datetime as _dt
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return _dt.strptime(v, fmt).date()
            except ValueError:
                continue
        return None
    return v


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
def admin_login(body: AdminLoginRequest, request: Request):
    """
    Verify the hardcoded system-admin credentials and return a JWT.
    The credentials are validated against the bcrypt hash compiled into
    the binary — never against the database.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not _admin_check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please wait {_ADMIN_RATE_WINDOW // 60} minutes before trying again.",
        )
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


# ── Trial Counter Management ──────────────────────────────────────────────────

@router.post("/trial/reset", dependencies=[Depends(require_admin)])
def reset_trial(db: Session = Depends(get_db)):
    """Reset trial start date to today, re-opening a fresh 30-day window."""
    flags = db.query(FeatureFlags).filter(FeatureFlags.id == 1).first()
    if not flags:
        flags = FeatureFlags(id=1, apis_enabled=False)
        db.add(flags)
    flags.trial_start_date = str(date.today())
    flags.trial_disabled = False
    db.commit()
    return {"trial_start_date": flags.trial_start_date, "trial_disabled": False,
            "message": "Trial reset — 30-day window starts today"}


@router.post("/trial/disable", dependencies=[Depends(require_admin)])
def disable_trial(db: Session = Depends(get_db)):
    """Disable trial mode (convert to permanent installation — banner disappears)."""
    flags = db.query(FeatureFlags).filter(FeatureFlags.id == 1).first()
    if not flags:
        flags = FeatureFlags(id=1, apis_enabled=False)
        db.add(flags)
    flags.trial_disabled = True
    db.commit()
    return {"trial_disabled": True,
            "message": "Trial disabled — installation is now permanent"}


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
        if body.user_role not in _VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(_VALID_ROLES))}")
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


@router.delete("/users/{user_id}/hard", dependencies=[Depends(require_admin)])
def hard_delete_user(user_id: str, db: Session = Depends(get_db)):
    """Completely remove a CLOSED user from the database."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.user_status != "CLOSED":
        raise HTTPException(status_code=400, detail="Only CLOSED users can be permanently deleted.")
    db.delete(user)
    db.commit()
    return {"message": f"User '{user_id}' permanently deleted."}


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

    _STATUTE_COLS = ["keyword", "display_name", "is_prohibited",
                     "supdt_goods_clause", "adjn_goods_clause", "legal_reference"]
    statutes = db.query(LegalStatute).order_by(LegalStatute.id).all()
    statutes_buf = io.StringIO()
    sw = csv.writer(statutes_buf)
    sw.writerow(_STATUTE_COLS)
    for s in statutes:
        sw.writerow([_val(getattr(s, col, None)) for col in _STATUTE_COLS])

    # ── print_template_config (versioned OS headings/paragraphs) ─────────────
    _PTC_COLS = ["field_key", "field_label", "field_value", "effective_from", "created_by", "created_at"]
    ptc_rows = db.query(PrintTemplateConfig).order_by(
        PrintTemplateConfig.field_key, PrintTemplateConfig.effective_from
    ).all()
    ptc_buf = io.StringIO()
    ptcw = csv.writer(ptc_buf)
    ptcw.writerow(_PTC_COLS)
    for r in ptc_rows:
        ptcw.writerow([_val(getattr(r, col, None)) for col in _PTC_COLS])

    # ── baggage_rules_config (versioned numeric rules) ────────────────────────
    _BRC_COLS = ["rule_key", "rule_label", "rule_value", "rule_uqc", "effective_from", "created_by", "created_at"]
    brc_rows = db.query(BaggageRulesConfig).order_by(
        BaggageRulesConfig.rule_key, BaggageRulesConfig.effective_from
    ).all()
    brc_buf = io.StringIO()
    brcw = csv.writer(brc_buf)
    brcw.writerow(_BRC_COLS)
    for r in brc_rows:
        brcw.writerow([_val(getattr(r, col, None)) for col in _BRC_COLS])

    # ── special_item_allowances ───────────────────────────────────────────────
    _SIA_COLS = ["item_name", "keywords", "allowance_qty", "allowance_uqc",
                 "effective_from", "active", "created_by", "created_at"]
    sia_rows = db.query(SpecialItemAllowance).order_by(
        SpecialItemAllowance.item_name, SpecialItemAllowance.effective_from
    ).all()
    sia_buf = io.StringIO()
    siaw = csv.writer(sia_buf)
    siaw.writerow(_SIA_COLS)
    for r in sia_rows:
        siaw.writerow([_val(getattr(r, col, None)) for col in _SIA_COLS])

    # ── feature_flags (single-row settings) ───────────────────────────────────
    _FF_COLS = ["apis_enabled", "session_timeout_minutes"]
    ff_row = db.query(FeatureFlags).filter(FeatureFlags.id == 1).first()
    ff_buf = io.StringIO()
    ffw = csv.writer(ff_buf)
    ffw.writerow(_FF_COLS)
    if ff_row:
        ffw.writerow([_val(getattr(ff_row, col, None)) for col in _FF_COLS])

    # ── shift_timing_master ───────────────────────────────────────────────────
    _STM_COLS = ["day_shift_from_hrs", "day_shift_to_hrs",
                 "night_shift_from_hrs", "night_shift_to_hrs"]
    stm_row = db.query(ShiftTimingMaster).filter(ShiftTimingMaster.id == 1).first()
    stm_buf = io.StringIO()
    stmw = csv.writer(stm_buf)
    stmw.writerow(_STM_COLS)
    if stm_row:
        stmw.writerow([_val(getattr(stm_row, col, None)) for col in _STM_COLS])

    # ── margin_master ─────────────────────────────────────────────────────────
    _MM_COLS = ["br_top_margin", "dr_top_margin"]
    mm_row = db.query(MarginMaster).filter(MarginMaster.id == 1).first()
    mm_buf = io.StringIO()
    mmw = csv.writer(mm_buf)
    mmw.writerow(_MM_COLS)
    if mm_row:
        mmw.writerow([_val(getattr(mm_row, col, None)) for col in _MM_COLS])

    # ── users (hashed passwords only — system-admin password NOT stored in DB) ─
    _USER_COLS = ["user_name", "user_desig", "user_id", "user_pwd",
                  "created_by", "created_on", "user_status", "user_role", "closed_on"]
    users = db.query(User).order_by(User.id).all()
    users_buf = io.StringIO()
    uw = csv.writer(users_buf)
    uw.writerow(_USER_COLS)
    for u in users:
        uw.writerow([_val(getattr(u, col, None)) for col in _USER_COLS])

    zip_buf = io.BytesIO()
    if _PYZIPPER_AVAILABLE:
        _pwd = get_zip_password()
        _log.info("ZIP backup: AES-256 encrypted, password length=%d chars", len(_pwd))
        zf_ctx = _pyzipper.AESZipFile(
            zip_buf, mode="w",
            compression=_pyzipper.ZIP_DEFLATED,
            compresslevel=1,               # fastest deflate — ~3-4× faster
            encryption=_pyzipper.WZ_AES,
        )
        zf_ctx.setpassword(_pwd)
    else:
        _log.warning("ZIP backup: pyzipper NOT available — backup is UNENCRYPTED plain ZIP")
        zf_ctx = zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED,
                                compresslevel=1)

    with zf_ctx as zf:
        zf.writestr("cops_master.csv", master_buf.getvalue())
        zf.writestr("cops_items.csv", items_buf.getvalue())
        zf.writestr("legal_statutes.csv", statutes_buf.getvalue())
        zf.writestr("print_template_config.csv", ptc_buf.getvalue())
        zf.writestr("baggage_rules_config.csv", brc_buf.getvalue())
        zf.writestr("special_item_allowances.csv", sia_buf.getvalue())
        zf.writestr("feature_flags.csv", ff_buf.getvalue())
        zf.writestr("shift_timing_master.csv", stm_buf.getvalue())
        zf.writestr("margin_master.csv", mm_buf.getvalue())
        zf.writestr("users.csv", users_buf.getvalue())
        # Export all registered tables
        for csv_name, model, _unique_cols, order_cols in _TABLE_REGISTRY:
            cols = _model_cols(model)
            order_attrs = [getattr(model, c) for c in order_cols]
            rows = db.query(model).order_by(*order_attrs).all()
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(cols)
            for r in rows:
                w.writerow([_val(getattr(r, col, None)) for col in cols])
            zf.writestr(csv_name, buf.getvalue())
    content_length = zip_buf.tell()
    zip_buf.seek(0)

    def _iter_bytes(b: io.BytesIO, chunk: int = 1024 * 1024):
        while True:
            data = b.read(chunk)
            if not data:
                break
            yield data

    filename = f"cops_full_backup_{date.today().isoformat()}.zip"
    return StreamingResponse(
        _iter_bytes(zip_buf),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(content_length),
            "Content-Encoding": "identity",
        },
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

    _zip_tmp = None
    try:
        tmp_fd, _zip_tmp = tempfile.mkstemp(suffix=".zip")
        os.close(tmp_fd)
        _MAX_ZIP = 500 * 1024 * 1024  # 500 MB
        _written = 0
        with open(_zip_tmp, "wb") as _f:
            for _chunk in iter(lambda: file.file.read(1024 * 1024), b""):
                _written += len(_chunk)
                if _written > _MAX_ZIP:
                    raise HTTPException(status_code=413, detail="Upload too large (max 500 MB).")
                _f.write(_chunk)
    except HTTPException:
        if _zip_tmp:
            try:
                os.unlink(_zip_tmp)
            except OSError:
                pass
        raise  # re-raise 413 / other HTTP errors as-is
    except Exception:
        if _zip_tmp:
            try:
                os.unlink(_zip_tmp)
            except OSError:
                pass
        raise HTTPException(status_code=400, detail="Cannot read uploaded file.")

    zf = None
    if _PYZIPPER_AVAILABLE:
        try:
            _zf = _pyzipper.AESZipFile(_zip_tmp)
            _zf.setpassword(get_zip_password())
            # Test-read the first file to verify the password works
            _zf.read(_zf.namelist()[0])
            zf = _zf
        except (RuntimeError, zipfile.BadZipFile):
            # Wrong password or not AES-encrypted — try as plain ZIP
            try:
                zf = zipfile.ZipFile(_zip_tmp)
            except zipfile.BadZipFile:
                pass
        except zipfile.BadZipFile:
            pass
        # Any other exception (IOError, MemoryError, etc.) propagates — it's a real error
    else:
        try:
            zf = zipfile.ZipFile(_zip_tmp)
        except zipfile.BadZipFile:
            pass

    if zf is None:
        try:
            os.unlink(_zip_tmp)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail="File is not a valid ZIP archive.")

    if "cops_master.csv" not in zf.namelist():
        try:
            os.unlink(_zip_tmp)
        except OSError:
            pass
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
            if isinstance(t, sqlalchemy.DateTime):
                return "datetime"
            if isinstance(t, sqlalchemy.Date):
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
        if kind == "datetime":
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
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

    # ── Restore legal_statutes ───────────────────────────────────────────────
    statutes_inserted = statutes_skipped = 0
    if "legal_statutes.csv" in zf.namelist():
        existing_keywords = {
            row[0]
            for row in db.query(LegalStatute.keyword).all()
        }
        statutes_text = zf.read("legal_statutes.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(statutes_text)):
            keyword = (row.get("keyword") or "").strip()
            if not keyword or keyword in existing_keywords:
                statutes_skipped += 1
                continue
            is_prohibited_raw = (row.get("is_prohibited") or "").strip().lower()
            is_prohibited = is_prohibited_raw in ("true", "1", "yes")
            db.add(LegalStatute(
                keyword=keyword,
                display_name=(row.get("display_name") or "").strip(),
                is_prohibited=is_prohibited,
                supdt_goods_clause=(row.get("supdt_goods_clause") or "").strip(),
                adjn_goods_clause=(row.get("adjn_goods_clause") or "").strip(),
                legal_reference=(row.get("legal_reference") or "").strip(),
            ))
            existing_keywords.add(keyword)
            statutes_inserted += 1

    # ── Restore print_template_config ────────────────────────────────────────
    ptc_inserted = ptc_skipped = 0
    if "print_template_config.csv" in zf.namelist():
        existing_ptc = {
            (r[0], r[1])
            for r in db.query(
                PrintTemplateConfig.field_key, PrintTemplateConfig.effective_from
            ).all()
        }
        ptc_text = zf.read("print_template_config.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(ptc_text)):
            key = (row.get("field_key") or "").strip()
            eff_raw = (row.get("effective_from") or "").strip()
            if not key or not eff_raw:
                continue
            eff = _coerce(eff_raw, "date")
            if eff is None:
                continue
            if (key, eff) in existing_ptc:
                ptc_skipped += 1
                continue
            db.add(PrintTemplateConfig(
                field_key=key,
                field_label=(row.get("field_label") or "").strip() or None,
                field_value=(row.get("field_value") or ""),
                effective_from=eff,
                created_by=(row.get("created_by") or "").strip() or None,
                created_at=_coerce((row.get("created_at") or "").strip(), "date"),
            ))
            existing_ptc.add((key, eff))
            ptc_inserted += 1

    # ── Restore baggage_rules_config ──────────────────────────────────────────
    brc_inserted = brc_skipped = 0
    if "baggage_rules_config.csv" in zf.namelist():
        existing_brc = {
            (r[0], r[1])
            for r in db.query(
                BaggageRulesConfig.rule_key, BaggageRulesConfig.effective_from
            ).all()
        }
        brc_text = zf.read("baggage_rules_config.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(brc_text)):
            key = (row.get("rule_key") or "").strip()
            eff_raw = (row.get("effective_from") or "").strip()
            if not key or not eff_raw:
                continue
            eff = _coerce(eff_raw, "date")
            if eff is None:
                continue
            if (key, eff) in existing_brc:
                brc_skipped += 1
                continue
            val_raw = (row.get("rule_value") or "").strip()
            rule_val = _coerce(val_raw, "float")
            if rule_val is None:
                continue
            db.add(BaggageRulesConfig(
                rule_key=key,
                rule_label=(row.get("rule_label") or "").strip() or None,
                rule_value=rule_val,
                rule_uqc=(row.get("rule_uqc") or "").strip() or None,
                effective_from=eff,
                created_by=(row.get("created_by") or "").strip() or None,
                created_at=_coerce((row.get("created_at") or "").strip(), "date"),
            ))
            existing_brc.add((key, eff))
            brc_inserted += 1

    # ── Restore special_item_allowances ───────────────────────────────────────
    sia_inserted = sia_skipped = 0
    if "special_item_allowances.csv" in zf.namelist():
        existing_sia = {
            (r[0], r[1])
            for r in db.query(
                SpecialItemAllowance.item_name, SpecialItemAllowance.effective_from
            ).all()
        }
        sia_text = zf.read("special_item_allowances.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(sia_text)):
            item_name = (row.get("item_name") or "").strip()
            eff_raw = (row.get("effective_from") or "").strip()
            if not item_name or not eff_raw:
                continue
            eff = _coerce(eff_raw, "date")
            if eff is None:
                continue
            if (item_name, eff) in existing_sia:
                sia_skipped += 1
                continue
            qty_raw = (row.get("allowance_qty") or "").strip()
            qty = _coerce(qty_raw, "float")
            if qty is None:
                continue
            db.add(SpecialItemAllowance(
                item_name=item_name,
                keywords=(row.get("keywords") or "").strip() or None,
                allowance_qty=qty,
                allowance_uqc=(row.get("allowance_uqc") or "").strip() or None,
                effective_from=eff,
                active=(row.get("active") or "Y").strip() or "Y",
                created_by=(row.get("created_by") or "").strip() or None,
                created_at=_coerce((row.get("created_at") or "").strip(), "date"),
            ))
            existing_sia.add((item_name, eff))
            sia_inserted += 1

    # ── Restore feature_flags (single row — overwrite id=1 if present) ────────
    if "feature_flags.csv" in zf.namelist():
        ff_text = zf.read("feature_flags.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(ff_text)):
            apis_raw = (row.get("apis_enabled") or "").strip().lower()
            apis_val = apis_raw in ("true", "1", "yes")
            timeout_raw = (row.get("session_timeout_minutes") or "480").strip()
            timeout_val = _coerce(timeout_raw, "int") or 480
            ff = db.query(FeatureFlags).filter(FeatureFlags.id == 1).first()
            if ff is None:
                db.add(FeatureFlags(id=1, apis_enabled=apis_val, session_timeout_minutes=timeout_val))
            # If exists, leave as-is (don't overwrite active settings)
            break  # single-row table

    # ── Restore shift_timing_master ───────────────────────────────────────────
    if "shift_timing_master.csv" in zf.namelist():
        stm_text = zf.read("shift_timing_master.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(stm_text)):
            stm = db.query(ShiftTimingMaster).filter(ShiftTimingMaster.id == 1).first()
            if stm is None:
                db.add(ShiftTimingMaster(
                    id=1,
                    day_shift_from_hrs=_coerce(row.get("day_shift_from_hrs", "7"), "int") or 7,
                    day_shift_to_hrs=_coerce(row.get("day_shift_to_hrs", "19"), "int") or 19,
                    night_shift_from_hrs=_coerce(row.get("night_shift_from_hrs", "19"), "int") or 19,
                    night_shift_to_hrs=_coerce(row.get("night_shift_to_hrs", "7"), "int") or 7,
                ))
            break  # single-row table

    # ── Restore margin_master ─────────────────────────────────────────────────
    if "margin_master.csv" in zf.namelist():
        mm_text = zf.read("margin_master.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(mm_text)):
            mm = db.query(MarginMaster).filter(MarginMaster.id == 1).first()
            if mm is None:
                db.add(MarginMaster(
                    id=1,
                    br_top_margin=_coerce(row.get("br_top_margin", "0.31"), "float") or 0.31,
                    dr_top_margin=_coerce(row.get("dr_top_margin", "0.31"), "float") or 0.31,
                ))
            break  # single-row table

    # ── Restore users (hashed passwords — system-admin password NOT in DB) ────
    users_inserted = users_skipped = 0
    if "users.csv" in zf.namelist():
        existing_user_ids = {
            r[0] for r in db.query(User.user_id).all()
        }
        users_text = zf.read("users.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(users_text)):
            uid = (row.get("user_id") or "").strip()
            if not uid or uid in existing_user_ids:
                users_skipped += 1
                continue
            db.add(User(
                user_name=(row.get("user_name") or "").strip(),
                user_desig=(row.get("user_desig") or "").strip() or None,
                user_id=uid,
                user_pwd=(row.get("user_pwd") or "").strip(),
                created_by=(row.get("created_by") or "").strip() or None,
                created_on=_coerce((row.get("created_on") or "").strip(), "date"),
                user_status=(row.get("user_status") or "ACTIVE").strip(),
                user_role=(row.get("user_role") or "SDO").strip(),
                closed_on=_coerce((row.get("closed_on") or "").strip(), "date"),
            ))
            existing_user_ids.add(uid)
            users_inserted += 1

    # ── Restore all registered tables (additive only — never overwrites existing) ─
    registry_counts: dict = {}
    for csv_name, model, unique_cols, _order_cols in _TABLE_REGISTRY:
        if csv_name not in zf.namelist():
            continue
        cols = _model_cols(model)
        # Build existing key set from unique columns
        existing = {
            tuple(str(v) if v is not None else "" for v in row)
            for row in db.query(*[getattr(model, c) for c in unique_cols]).all()
        }
        text = zf.read(csv_name).decode("utf-8-sig")
        ins = skp = 0
        for row in csv.DictReader(io.StringIO(text)):
            key = tuple((row.get(c) or "").strip() for c in unique_cols)
            if any(not k for k in key) or key in existing:
                skp += 1
                continue
            kwargs: dict = {}
            for col in cols:
                raw = (row.get(col) or "").strip()
                if not raw:
                    continue
                kind = _col_type_generic(model, col)
                coerced = _coerce_val(raw, kind)
                if coerced is not None:
                    kwargs[col] = coerced
            db.add(model(**kwargs))
            existing.add(key)
            ins += 1
        registry_counts[csv_name] = {"inserted": ins, "skipped": skp}

    # ── Restore br_master ─────────────────────────────────────────────────────
    br_inserted = br_skipped = 0
    if "br_master.csv" in zf.namelist():
        existing_brs = {
            (r[0], r[1] or 0)
            for r in db.query(BrMaster.br_no, BrMaster.br_year).all()
        }
        br_text = zf.read("br_master.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(br_text)):
            try:
                br_no_val = int(row.get("br_no") or 0)
            except ValueError:
                continue
            if not br_no_val:
                continue
            br_date_val = _coerce((row.get("br_date") or "").strip(), "date")
            if br_date_val is None:
                continue
            br_type_val = (row.get("br_type") or "").strip()
            if not br_type_val:
                continue
            br_year_val = _coerce((row.get("br_year") or "").strip(), "int") or 0
            key = (br_no_val, br_year_val)
            if key in existing_brs:
                br_skipped += 1
                continue
            kwargs: dict = {"br_no": br_no_val, "br_date": br_date_val, "br_type": br_type_val}
            for col in _BR_MASTER_COLS:
                csv_key = col.lstrip("_")
                if csv_key in ("br_no", "br_date", "br_type"):
                    continue
                raw = (row.get(csv_key) or "").strip()
                if not raw:
                    continue
                kind = _col_type(BrMaster, csv_key)
                coerced = _coerce(raw, kind)
                if coerced is not None:
                    kwargs[col] = coerced  # Python attr name (handles _availed_remarks)
            db.add(BrMaster(**kwargs))
            existing_brs.add(key)
            br_inserted += 1
        db.flush()

    # ── Restore br_items ──────────────────────────────────────────────────────
    br_items_inserted = br_items_skipped = 0
    if "br_items.csv" in zf.namelist():
        existing_br_items = {
            (r[0], str(r[1]), r[2])
            for r in db.query(BrItems.br_no, BrItems.br_date, BrItems.items_sno).all()
        }
        bi_text = zf.read("br_items.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(bi_text)):
            try:
                br_no_val = int(row.get("br_no") or 0)
                items_sno_val = int(row.get("items_sno") or 0)
            except ValueError:
                continue
            if not br_no_val:
                continue
            br_date_val = _coerce((row.get("br_date") or "").strip(), "date")
            if br_date_val is None:
                continue
            item_key = (br_no_val, str(br_date_val), items_sno_val)
            if item_key in existing_br_items:
                br_items_skipped += 1
                continue
            kwargs = {"br_no": br_no_val, "br_date": br_date_val, "items_sno": items_sno_val}
            for col in _BR_ITEMS_COLS:
                if col in ("br_no", "br_date", "items_sno"):
                    continue
                raw = (row.get(col) or "").strip()
                if not raw:
                    continue
                kind = _col_type(BrItems, col)
                coerced = _coerce(raw, kind)
                if coerced is not None:
                    kwargs[col] = coerced
            db.add(BrItems(**kwargs))
            existing_br_items.add(item_key)
            br_items_inserted += 1
        db.flush()

    # ── Restore dr_master ─────────────────────────────────────────────────────
    dr_inserted = dr_skipped = 0
    if "dr_master.csv" in zf.namelist():
        existing_drs = {
            (r[0], r[1] or 0)
            for r in db.query(DrMaster.dr_no, DrMaster.dr_year).all()
        }
        dr_text = zf.read("dr_master.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(dr_text)):
            try:
                dr_no_val = int(row.get("dr_no") or 0)
            except ValueError:
                continue
            if not dr_no_val:
                continue
            dr_date_val = _coerce((row.get("dr_date") or "").strip(), "date")
            if dr_date_val is None:
                continue
            dr_type_val = (row.get("dr_type") or "").strip()
            if not dr_type_val:
                continue
            dr_year_val = _coerce((row.get("dr_year") or "").strip(), "int") or 0
            key = (dr_no_val, dr_year_val)
            if key in existing_drs:
                dr_skipped += 1
                continue
            kwargs = {"dr_no": dr_no_val, "dr_date": dr_date_val, "dr_type": dr_type_val}
            for col in _DR_MASTER_COLS:
                if col in ("dr_no", "dr_date", "dr_type"):
                    continue
                raw = (row.get(col) or "").strip()
                if not raw:
                    continue
                kind = _col_type(DrMaster, col)
                coerced = _coerce(raw, kind)
                if coerced is not None:
                    kwargs[col] = coerced
            db.add(DrMaster(**kwargs))
            existing_drs.add(key)
            dr_inserted += 1
        db.flush()

    # ── Restore dr_items ──────────────────────────────────────────────────────
    dr_items_inserted = dr_items_skipped = 0
    if "dr_items.csv" in zf.namelist():
        existing_dr_items = {
            (r[0], str(r[1]), r[2])
            for r in db.query(DrItems.dr_no, DrItems.dr_date, DrItems.items_sno).all()
        }
        di_text = zf.read("dr_items.csv").decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(di_text)):
            try:
                dr_no_val = int(row.get("dr_no") or 0)
                items_sno_val = int(row.get("items_sno") or 0)
            except ValueError:
                continue
            if not dr_no_val:
                continue
            dr_date_val = _coerce((row.get("dr_date") or "").strip(), "date")
            if dr_date_val is None:
                continue
            item_key = (dr_no_val, str(dr_date_val), items_sno_val)
            if item_key in existing_dr_items:
                dr_items_skipped += 1
                continue
            kwargs = {"dr_no": dr_no_val, "dr_date": dr_date_val, "items_sno": items_sno_val}
            for col in _DR_ITEMS_COLS:
                if col in ("dr_no", "dr_date", "items_sno"):
                    continue
                raw = (row.get(col) or "").strip()
                if not raw:
                    continue
                kind = _col_type(DrItems, col)
                coerced = _coerce(raw, kind)
                if coerced is not None:
                    kwargs[col] = coerced
            db.add(DrItems(**kwargs))
            existing_dr_items.add(item_key)
            dr_items_inserted += 1
        db.flush()

    db.commit()
    post_import_optimise(db)
    # Close the zip before unlinking — required on Windows (open handles block delete)
    try:
        if zf is not None:
            zf.close()
    except Exception:
        pass
    try:
        os.unlink(_zip_tmp)
    except OSError:
        pass
    bust_all_master_caches()  # master tables were just written — invalidate all caches
    return {
        "master_inserted": master_inserted,
        "master_skipped": master_skipped,
        "items_inserted": items_inserted,
        "items_skipped": items_skipped,
        "statutes_inserted": statutes_inserted,
        "statutes_skipped": statutes_skipped,
        "ptc_inserted": ptc_inserted,
        "ptc_skipped": ptc_skipped,
        "brc_inserted": brc_inserted,
        "brc_skipped": brc_skipped,
        "sia_inserted": sia_inserted,
        "sia_skipped": sia_skipped,
        "users_inserted": users_inserted,
        "users_skipped": users_skipped,
        "br_inserted": br_inserted,
        "br_skipped": br_skipped,
        "br_items_inserted": br_items_inserted,
        "br_items_skipped": br_items_skipped,
        "dr_inserted": dr_inserted,
        "dr_skipped": dr_skipped,
        "dr_items_inserted": dr_items_inserted,
        "dr_items_skipped": dr_items_skipped,
        "tables": registry_counts,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Admin Config Backup / Restore — TEMPLATES & RULES ONLY (no OS / case data).
#
# Use case: edit print templates / baggage rules on a test machine, ship just
# those edits to the production machine without copying any operational data.
#
# Tables included (the admin-editable content tables):
#   • print_template_config       — versioned OS print headings & paragraphs
#   • baggage_rules_config        — versioned numeric baggage limits
#   • special_item_allowances     — versioned per-item allowances
#   • legal_statutes              — IPC/COFEPOSA/etc. lookup with goods clauses
#
# Format: a single JSON file with a versioned envelope. Restore is INSERT-only
# by composite natural key — existing rows on the destination are never
# overwritten or deleted, so reapplying the same backup is idempotent.
# ──────────────────────────────────────────────────────────────────────────────

_CONFIG_BACKUP_FORMAT = 1

def _row_to_dict(row, cols: list) -> dict:
    out = {}
    for c in cols:
        v = getattr(row, c, None)
        if isinstance(v, (date, datetime)):
            out[c] = v.isoformat()
        else:
            out[c] = v
    return out


@router.get("/config/backup", dependencies=[Depends(require_admin)])
def admin_config_backup(db: Session = Depends(get_db)):
    """Export admin config tables (templates / rules / allowances / statutes)
    as a JSON file. Does NOT include any OS, BR, DR, user or installation data."""
    import json as _json

    ptc_cols = ["field_key", "field_label", "field_value",
                "effective_from", "created_by", "created_at"]
    brc_cols = ["rule_key", "rule_label", "rule_value", "rule_uqc",
                "effective_from", "created_by", "created_at"]
    sia_cols = ["item_name", "keywords", "allowance_qty", "allowance_uqc",
                "effective_from", "active", "created_by", "created_at"]
    statute_cols = ["keyword", "display_name", "is_prohibited",
                    "supdt_goods_clause", "adjn_goods_clause", "legal_reference"]

    payload = {
        "format_version": _CONFIG_BACKUP_FORMAT,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "kind": "admin_config_only",
        "note": "Templates & rules only — no OS, BR, DR, user or installation data.",
        "tables": {
            "print_template_config": [
                _row_to_dict(r, ptc_cols)
                for r in db.query(PrintTemplateConfig)
                    .order_by(PrintTemplateConfig.field_key,
                              PrintTemplateConfig.effective_from).all()
            ],
            "baggage_rules_config": [
                _row_to_dict(r, brc_cols)
                for r in db.query(BaggageRulesConfig)
                    .order_by(BaggageRulesConfig.rule_key,
                              BaggageRulesConfig.effective_from).all()
            ],
            "special_item_allowances": [
                _row_to_dict(r, sia_cols)
                for r in db.query(SpecialItemAllowance)
                    .order_by(SpecialItemAllowance.item_name,
                              SpecialItemAllowance.effective_from).all()
            ],
            "legal_statutes": [
                _row_to_dict(r, statute_cols)
                for r in db.query(LegalStatute).order_by(LegalStatute.keyword).all()
            ],
        },
    }

    body = _json.dumps(payload, indent=2, default=str)
    filename = f"cops_config_backup_{date.today().isoformat()}.json"
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Encoding": "identity",
        },
    )


@router.post("/config/restore", dependencies=[Depends(require_admin)])
def admin_config_restore(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Restore admin config from a JSON file produced by /admin/config/backup.
    INSERT-only by composite natural key — existing rows are never overwritten
    or deleted. OS/BR/DR/user data is never touched."""
    import json as _json

    try:
        raw = file.file.read()
        payload = _json.loads(raw.decode("utf-8-sig"))
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Invalid JSON file. Expected a config backup produced by /admin/config/backup.")

    if not isinstance(payload, dict) or payload.get("kind") != "admin_config_only":
        raise HTTPException(status_code=400,
                            detail="This file is not an admin config backup. "
                                   "Use the OS Backup/Restore screen for full backups.")

    fmt = payload.get("format_version")
    if fmt != _CONFIG_BACKUP_FORMAT:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported config backup version: {fmt}. "
                                   f"This server expects version {_CONFIG_BACKUP_FORMAT}.")

    tables = payload.get("tables") or {}

    def _to_date(v):
        if not v:
            return None
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        s = str(v)[:10]
        try:
            return date.fromisoformat(s)
        except ValueError:
            return None

    def _to_dt(v):
        if not v:
            return None
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError:
            return None

    counts = {
        "print_template_config":  {"inserted": 0, "skipped": 0},
        "baggage_rules_config":   {"inserted": 0, "skipped": 0},
        "special_item_allowances":{"inserted": 0, "skipped": 0},
        "legal_statutes":         {"inserted": 0, "skipped": 0},
    }

    # ── print_template_config ────────────────────────────────────────────────
    ptc_rows = tables.get("print_template_config") or []
    if ptc_rows:
        existing = {
            (r[0], r[1]) for r in db.query(
                PrintTemplateConfig.field_key, PrintTemplateConfig.effective_from
            ).all()
        }
        for row in ptc_rows:
            key = (row.get("field_key") or "").strip()
            eff = _to_date(row.get("effective_from"))
            if not key or eff is None:
                counts["print_template_config"]["skipped"] += 1
                continue
            if (key, eff) in existing:
                counts["print_template_config"]["skipped"] += 1
                continue
            db.add(PrintTemplateConfig(
                field_key=key,
                field_label=(row.get("field_label") or None),
                field_value=(row.get("field_value") or ""),
                effective_from=eff,
                created_by=(row.get("created_by") or None),
                created_at=_to_dt(row.get("created_at")),
            ))
            existing.add((key, eff))
            counts["print_template_config"]["inserted"] += 1

    # ── baggage_rules_config ─────────────────────────────────────────────────
    brc_rows = tables.get("baggage_rules_config") or []
    if brc_rows:
        existing = {
            (r[0], r[1]) for r in db.query(
                BaggageRulesConfig.rule_key, BaggageRulesConfig.effective_from
            ).all()
        }
        for row in brc_rows:
            key = (row.get("rule_key") or "").strip()
            eff = _to_date(row.get("effective_from"))
            try:
                rule_val = float(row.get("rule_value"))
            except (TypeError, ValueError):
                rule_val = None
            if not key or eff is None or rule_val is None:
                counts["baggage_rules_config"]["skipped"] += 1
                continue
            if (key, eff) in existing:
                counts["baggage_rules_config"]["skipped"] += 1
                continue
            db.add(BaggageRulesConfig(
                rule_key=key,
                rule_label=(row.get("rule_label") or None),
                rule_value=rule_val,
                rule_uqc=(row.get("rule_uqc") or None),
                effective_from=eff,
                created_by=(row.get("created_by") or None),
                created_at=_to_dt(row.get("created_at")),
            ))
            existing.add((key, eff))
            counts["baggage_rules_config"]["inserted"] += 1

    # ── special_item_allowances ──────────────────────────────────────────────
    sia_rows = tables.get("special_item_allowances") or []
    if sia_rows:
        existing = {
            (r[0], r[1]) for r in db.query(
                SpecialItemAllowance.item_name, SpecialItemAllowance.effective_from
            ).all()
        }
        for row in sia_rows:
            item_name = (row.get("item_name") or "").strip()
            eff = _to_date(row.get("effective_from"))
            try:
                qty = float(row.get("allowance_qty"))
            except (TypeError, ValueError):
                qty = None
            if not item_name or eff is None or qty is None:
                counts["special_item_allowances"]["skipped"] += 1
                continue
            if (item_name, eff) in existing:
                counts["special_item_allowances"]["skipped"] += 1
                continue
            db.add(SpecialItemAllowance(
                item_name=item_name,
                keywords=(row.get("keywords") or None),
                allowance_qty=qty,
                allowance_uqc=(row.get("allowance_uqc") or None),
                effective_from=eff,
                active=(row.get("active") or "Y"),
                created_by=(row.get("created_by") or None),
                created_at=_to_dt(row.get("created_at")),
            ))
            existing.add((item_name, eff))
            counts["special_item_allowances"]["inserted"] += 1

    # ── legal_statutes (keyword is unique — INSERT new only) ─────────────────
    statute_rows = tables.get("legal_statutes") or []
    if statute_rows:
        existing_kw = {r[0] for r in db.query(LegalStatute.keyword).all()}
        for row in statute_rows:
            kw = (row.get("keyword") or "").strip()
            display = (row.get("display_name") or "").strip()
            if not kw or not display:
                counts["legal_statutes"]["skipped"] += 1
                continue
            if kw in existing_kw:
                counts["legal_statutes"]["skipped"] += 1
                continue
            db.add(LegalStatute(
                keyword=kw,
                display_name=display,
                is_prohibited=bool(row.get("is_prohibited") or False),
                supdt_goods_clause=(row.get("supdt_goods_clause") or ""),
                adjn_goods_clause=(row.get("adjn_goods_clause") or ""),
                legal_reference=(row.get("legal_reference") or ""),
            ))
            existing_kw.add(kw)
            counts["legal_statutes"]["inserted"] += 1

    db.commit()

    return {
        "ok": True,
        "format_version": fmt,
        "exported_at": payload.get("exported_at"),
        "counts": counts,
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
        if not (1990 <= os_year <= date.today().year + 1):
            os_date_parsed = _parse_date(row.get("os_date")) if row.get("os_date") else None
            os_year = os_date_parsed.year if os_date_parsed else None
        if not os_year:
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
        if not (1990 <= os_year <= date.today().year + 1):
            os_date_parsed = _parse_date(row.get("os_date")) if row.get("os_date") else None
            os_year = os_date_parsed.year if os_date_parsed else None
        if not os_year:
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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Import directly from an uploaded MS-Access .mdb file.
    Works on Windows (via pyodbc + Microsoft Access ODBC driver) and
    Linux/macOS (via mdbtools mdb-export).
    Only inserts missing records — never overwrites existing data.
    """
    import os, shutil, tempfile
    from app.services.mdb_import import import_from_mdb

    if not (file.filename or "").lower().endswith(".mdb"):
        raise HTTPException(status_code=400, detail="File must be an .mdb file.")

    # Write the uploaded bytes to a temp file so mdb_import can open it by path.
    try:
        with tempfile.NamedTemporaryFile(suffix=".mdb", delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {e}")

    try:
        result = import_from_mdb(tmp_path, db)
    except RuntimeError as e:
        _log.error("MDB import failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    bust_all_master_caches()  # MDB import writes master tables — invalidate all caches
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


class RemarksTemplateUpdate(BaseModel):
    value: str


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
def get_pit_config(ref_date: date, db: Session = Depends(get_db), _user=Depends(get_current_active_user)):
    """Return the active config as of ref_date. Requires active user session."""
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
        created_at=datetime.now(timezone.utc),
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
        created_at=datetime.now(timezone.utc),
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
        created_at=datetime.now(timezone.utc),
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


# ── Full SQLite database backup / restore ─────────────────────────────────────

def _get_sqlite_path() -> str:
    """
    Resolve the absolute filesystem path of the SQLite .db file.
    Raises HTTPException if the database is not SQLite.
    """
    import os
    from sqlalchemy.engine import make_url
    url = make_url(settings.DATABASE_URL)
    if url.drivername not in ("sqlite", "sqlite+pysqlite"):
        raise HTTPException(
            status_code=400,
            detail="Full-database backup/restore is only supported for SQLite deployments.",
        )
    db_path = url.database  # e.g. "/abs/path/to/cops_br_database.db" or "./cops_br_database.db"
    if db_path.startswith("./") or not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    return db_path


@router.get("/backup/export-fulldb")
def admin_export_fulldb(_=Depends(require_admin)):
    """
    Download a complete binary copy of the SQLite database.
    Uses backup() to create a consistent, WAL-flushed snapshot —
    safe to download while the server is running.
    If SQLCipher encryption is active the exported file is also encrypted
    with the same AES-256 key (open with DB Browser + SQLCipher plugin).
    Every table, every row, every setting is included.
    """
    db_path = _get_sqlite_path()
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found on disk.")

    cipher = get_cipher_module()
    db_key = get_db_key()
    hex_pragma = f"PRAGMA key = \"x'{db_key}'\"" if db_key else None

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)
    src = dst = None
    try:
        if cipher and db_key:
            src = cipher.connect(db_path)
            src.execute(hex_pragma)
            src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            dst = cipher.connect(tmp_path)
            dst.execute(hex_pragma)
            src.backup(dst)
        else:
            src = _stdlib_sqlite3.connect(db_path)
            src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            dst = _stdlib_sqlite3.connect(tmp_path)
            src.backup(dst)
        # Close before reading so WAL is fully flushed to tmp_path
        src.close(); src = None
        dst.close(); dst = None
    finally:
        # Always close connections before unlink — open handles block delete on Windows
        for conn in (src, dst):
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    suffix = "_enc" if (cipher and db_key) else ""
    filename = f"cops_fulldb_{date.today().isoformat()}{suffix}.db"
    # Stream directly from disk — no memory copy.  BackgroundTask deletes
    # the temp file after the last byte has been sent to the client.
    def _safe_unlink(p: str):
        try:
            os.unlink(p)
        except OSError:
            pass

    return FileResponse(
        tmp_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Encoding": "identity"},
        background=BackgroundTask(_safe_unlink, tmp_path),
    )


@router.post("/backup/restore-fulldb")
def admin_restore_fulldb(file: UploadFile = File(...), _=Depends(require_admin)):
    """
    Restore the complete database from a full-DB backup (.db file).
    Accepts both encrypted (SQLCipher) and plaintext SQLite backups.
    Overwrites ALL tables — use with care.
    The server remains operational; connections are recycled automatically
    after the restore completes.
    """
    from app.database import engine

    db_path = _get_sqlite_path()
    cipher = get_cipher_module()
    db_key = get_db_key()
    hex_pragma = f"PRAGMA key = \"x'{db_key}'\"" if db_key else None

    # Stream the entire upload to a temp file
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)
    try:
        _MAX_DB = 500 * 1024 * 1024  # 500 MB
        _written = 0
        with open(tmp_path, "wb") as f:
            for _chunk in iter(lambda: file.file.read(1024 * 1024), b""):
                _written += len(_chunk)
                if _written > _MAX_DB:
                    raise HTTPException(status_code=413, detail="Upload too large (max 500 MB).")
                f.write(_chunk)

        # Validate: try opening the uploaded file
        # Accept either an encrypted SQLCipher file or a plaintext SQLite file.
        opened_as_cipher = False
        if cipher and db_key:
            try:
                chk = cipher.connect(tmp_path)
                chk.execute(hex_pragma)
                chk.execute("SELECT count(*) FROM sqlite_master")
                chk.close()
                opened_as_cipher = True
            except Exception:
                pass

        if not opened_as_cipher:
            try:
                chk = _stdlib_sqlite3.connect(tmp_path)
                chk.execute("SELECT count(*) FROM sqlite_master")
                chk.close()
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is not a valid SQLite database (plaintext or encrypted).",
                )

        # Snapshot current users before overwriting so we can re-merge them
        # after the restore (prevents local machine users from being wiped).
        _local_users: list[dict] = []
        try:
            _snap_con = (cipher.connect(db_path) if (cipher and db_key) else _stdlib_sqlite3.connect(db_path))
            if cipher and db_key:
                _snap_con.execute(hex_pragma)
            _snap_cur = _snap_con.execute(
                "SELECT user_name, user_desig, user_id, user_pwd, created_by, "
                "created_on, user_status, user_role, closed_on FROM users"
            )
            for _row in _snap_cur.fetchall():
                _local_users.append({
                    "user_name": _row[0], "user_desig": _row[1], "user_id": _row[2],
                    "user_pwd": _row[3], "created_by": _row[4], "created_on": _row[5],
                    "user_status": _row[6], "user_role": _row[7], "closed_on": _row[8],
                })
            _snap_con.close()
        except Exception:
            _local_users = []

        # Close all pooled connections before overwriting
        engine.dispose()

        if cipher and db_key:
            if opened_as_cipher:
                # Encrypted → encrypted (same key): direct cipher backup
                src = dst = None
                try:
                    src = cipher.connect(tmp_path)
                    src.execute(hex_pragma)
                    dst = cipher.connect(db_path)
                    dst.execute(hex_pragma)
                    src.backup(dst)
                finally:
                    for _c in (src, dst):
                        try:
                            if _c: _c.close()
                        except Exception:
                            pass
            else:
                # Plaintext → encrypted: copy then encrypt in-place
                src = dst = None
                try:
                    src = _stdlib_sqlite3.connect(tmp_path)
                    dst = _stdlib_sqlite3.connect(db_path)
                    src.backup(dst)
                finally:
                    for _c in (src, dst):
                        try:
                            if _c: _c.close()
                        except Exception:
                            pass
                migrate_plaintext_to_encrypted(db_path, db_key)
        else:
            src = dst = None
            try:
                src = _stdlib_sqlite3.connect(tmp_path)
                dst = _stdlib_sqlite3.connect(db_path)
                src.backup(dst)
            finally:
                for _c in (src, dst):
                    try:
                        if _c: _c.close()
                    except Exception:
                        pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    # Re-merge local users that were not present in the backup.
    # This prevents users registered on this machine from being wiped out.
    if _local_users:
        try:
            _merge_con = (cipher.connect(db_path) if (cipher and db_key) else _stdlib_sqlite3.connect(db_path))
            if cipher and db_key:
                _merge_con.execute(hex_pragma)
            _existing_ids = {r[0] for r in _merge_con.execute("SELECT user_id FROM users").fetchall()}
            for _u in _local_users:
                if _u["user_id"] not in _existing_ids:
                    _merge_con.execute(
                        "INSERT INTO users (user_name, user_desig, user_id, user_pwd, "
                        "created_by, created_on, user_status, user_role, closed_on) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            _u["user_name"], _u["user_desig"], _u["user_id"],
                            _u["user_pwd"], _u["created_by"], _u["created_on"],
                            _u["user_status"], _u["user_role"], _u["closed_on"],
                        ),
                    )
            _merge_con.commit()
            _merge_con.close()
        except Exception:
            pass  # best-effort — don't fail the restore if merge has issues

    bust_all_master_caches()  # full DB replaced — invalidate all in-memory caches
    return {
        "message": (
            "Database fully restored. "
            "All data has been replaced with the backup. "
            "Refresh your browser to continue."
        )
    }


# ── Remarks Templates ─────────────────────────────────────────────────────────
# Stored in PrintTemplateConfig with special field_key prefix "remarks_".
# No versioning needed — only the single row per key is ever written.

_REMARKS_TPL_DEFAULTS: dict = {
    # ── Opening paragraphs ───────────────────────────────────────────────────
    "remarks_export_supdt_opening": (
        "Departure — SUPDT Opening",
        (
            "On the basis of specific intelligence/information received by the department, "
            "the pax was detained at the Departure Hall on {date} while about to depart to "
            "{city} by flight no. {flight_no}."
        ),
    ),
    "remarks_import_supdt_opening": (
        "Arrival — SUPDT Opening",
        "The pax arrived on {date} by flight no. {flight_no} from {city}.",
    ),
    # ── SUPDT closing paragraphs (indirect language — section nos indicate outcome) ──
    "remarks_supdt_import_confs_closing": (
        "Arrival — SUPDT Closing (Absolute Confiscation)",
        (
            "The aforesaid goods were not declared to the Customs authorities at the time of "
            "arrival as required under Section 77 of the Customs Act, 1962, and the pax was "
            "unable to produce any valid import authorization/permit for the same. "
            "The said goods being absolutely prohibited from import are liable for confiscation "
            "under Sections 111(d), 111(l), 111(m) and 111(o) of the Customs Act, 1962 read "
            "with Section 3(3) of the Foreign Trade (Development & Regulation) Act, 1992, for "
            "improper importation. The pax has also rendered himself/herself liable for penal "
            "action under Section 112(a) of the Customs Act, 1962. Put up for Adjudication please."
        ),
    ),
    "remarks_supdt_import_rf_closing": (
        "Arrival — SUPDT Closing (Redemption Fine)",
        (
            "The aforesaid goods were not declared to the Customs authorities at the time of "
            "arrival as required under Section 77 of the Customs Act, 1962. The said goods, "
            "being commercial in nature and non-bonafide baggage, are liable for confiscation "
            "under Sections 111(d), 111(l) and 111(m) of the Customs Act, 1962 read with "
            "Section 3(3) of the Foreign Trade (Development & Regulation) Act, 1992. "
            "The pax has also rendered himself/herself liable for penal action under Section 112 "
            "of the Customs Act, 1962. Put up for Adjudication please."
        ),
    ),
    "remarks_supdt_import_ref_closing": (
        "Arrival — SUPDT Closing (Re-export)",
        (
            "The aforesaid goods were not declared to the Customs authorities at the time of "
            "arrival as required under Section 77 of the Customs Act, 1962, and the pax was "
            "unable to produce any valid import authorization/permit for the same. "
            "The said goods being restricted for import under the applicable DGFT "
            "notification/policy are liable for confiscation under Sections 111(d), 111(l), "
            "111(m) and 111(o) of the Customs Act, 1962 read with Section 3(3) of the Foreign "
            "Trade (Development & Regulation) Act, 1992. The pax has also rendered "
            "himself/herself liable for penal action under Section 112(a) of the Customs Act, "
            "1962. Put up for Adjudication please."
        ),
    ),
    "remarks_supdt_export_confs_closing": (
        "Departure — SUPDT Closing (Absolute Confiscation)",
        (
            "The aforesaid goods were not declared to the Customs authorities at the time of "
            "departure as required under Section 40 of the Customs Act, 1962, and the pax was "
            "unable to produce any valid export authorization/permit. "
            "The said goods being absolutely prohibited from export are liable for confiscation "
            "under Section 113 of the Customs Act, 1962 read with Section 3(3) of the Foreign "
            "Trade (Development & Regulation) Act, 1992, for improper exportation. "
            "The pax has also rendered himself/herself liable for penal action under Section 114 "
            "of the Customs Act, 1962. Put up for Adjudication please."
        ),
    ),
    "remarks_supdt_export_rf_closing": (
        "Departure — SUPDT Closing (Redemption Fine)",
        (
            "The aforesaid goods were not declared to the Customs authorities at the time of "
            "departure as required under Section 40 of the Customs Act, 1962. "
            "The said goods, being in violation of export regulations, are liable for "
            "confiscation under Section 113 of the Customs Act, 1962 read with Section 3(3) of "
            "the Foreign Trade (Development & Regulation) Act, 1992. "
            "The pax has also rendered himself/herself liable for penal action under Section 114 "
            "of the Customs Act, 1962. Put up for Adjudication please."
        ),
    ),
    # ── AC disposal paragraphs (explicit orders — {items} placeholder replaced at runtime) ─
    "remarks_ac_import_confs_disposal": (
        "Arrival — AC Disposal (Absolute Confiscation)",
        (
            "{items} being absolutely prohibited from import cannot be allowed to be redeemed "
            "and are hereby absolutely confiscated under Sections 111(d), 111(l), 111(m) and "
            "111(o) of the Customs Act, 1962 read with Section 3(3) of the FT(D&R) Act, 1992."
        ),
    ),
    "remarks_ac_import_rf_disposal": (
        "Arrival — AC Disposal (Redemption Fine)",
        (
            "{items} are allowed to be redeemed on payment of the applicable Customs duty and "
            "Redemption Fine as imposed under Section 125 of the Customs Act, 1962."
        ),
    ),
    "remarks_ac_import_ref_disposal": (
        "Arrival — AC Disposal (Re-export)",
        (
            "{items} are directed to be re-exported within the time stipulated by the Customs "
            "authorities, on payment of Re-export Fine as imposed under Section 125 of the "
            "Customs Act, 1962."
        ),
    ),
    "remarks_ac_export_confs_disposal": (
        "Departure — AC Disposal (Absolute Confiscation)",
        (
            "{items} being absolutely prohibited from export cannot be allowed to be redeemed "
            "and are hereby absolutely confiscated under Section 113 of the Customs Act, 1962."
        ),
    ),
    "remarks_ac_export_rf_disposal": (
        "Departure — AC Disposal (Redemption Fine)",
        (
            "{items} are allowed to be redeemed on payment of the applicable Redemption Fine "
            "as imposed under Section 125 of the Customs Act, 1962."
        ),
    ),
}


@router.get("/config/remarks-templates")
def get_remarks_templates(db: Session = Depends(get_db)):
    """Public — no auth required. Returns current remarks opening template text."""
    from datetime import date as _date
    today = _date.today()
    result = {}
    for key, (label, default) in _REMARKS_TPL_DEFAULTS.items():
        row = (
            db.query(PrintTemplateConfig)
            .filter(
                PrintTemplateConfig.field_key == key,
                PrintTemplateConfig.effective_from <= today,
            )
            .order_by(PrintTemplateConfig.effective_from.desc())
            .first()
        )
        result[key] = {
            "id": row.id if row else None,
            "label": label,
            "value": row.field_value if row else default,
        }
    return result


@router.put("/config/remarks-templates/{key}")
def update_remarks_template(
    key: str,
    body: RemarksTemplateUpdate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin — update or create a remarks template. Placeholders: {date}, {city}, {flight_no}."""
    from datetime import date as _date, datetime as _dt, timezone
    if key not in _REMARKS_TPL_DEFAULTS:
        raise HTTPException(status_code=404, detail="Unknown template key.")
    value = body.value.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Template text cannot be empty.")
    row = db.query(PrintTemplateConfig).filter(PrintTemplateConfig.field_key == key).first()
    if row:
        row.field_value = value
    else:
        label, _ = _REMARKS_TPL_DEFAULTS[key]
        db.add(PrintTemplateConfig(
            field_key=key,
            field_label=label,
            field_value=value,
            effective_from=_date(1900, 1, 1),
            created_by=admin.get("sub", "admin"),
            created_at=_dt.now(timezone.utc),
        ))
    db.commit()
    return {"message": "Updated"}


# ══════════════════════════════════════════════════════════════════════════════
# Hard-Purge OS Case
# ══════════════════════════════════════════════════════════════════════════════

class PurgeOSRequest(BaseModel):
    os_no: str
    os_year: int
    admin_password: str


@router.post("/purge-os")
def purge_os_case(
    body: PurgeOSRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """
    IRREVERSIBLE hard-delete of a single OS case and ALL related data.
    Removes every trace from cops_master, cops_items, appeal, UOS staging,
    report staging, BR/DR records, warehouse, mahazar, and all archive tables.
    Admin password is re-verified before execution as an extra security layer.
    """
    import json as _json

    # Re-verify admin password (JWT alone is not sufficient for destructive ops)
    if not verify_admin_credentials(_ADMIN_USERNAME, body.admin_password):
        raise HTTPException(status_code=403, detail="Admin password incorrect.")

    os_no = body.os_no.strip()
    if not os_no:
        raise HTTPException(status_code=400, detail="OS number cannot be blank.")

    case = db.query(CopsMaster).filter(
        CopsMaster.os_no == os_no,
        CopsMaster.os_year == body.os_year,
    ).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"OS {os_no}/{body.os_year} not found."
        )

    # Collect linked BR numbers (initial BR + post-adjudication BRs)
    br_nos: list = []
    if case.br_no_num:
        try:
            br_nos.append(int(case.br_no_num))
        except (ValueError, TypeError):
            pass
    if case.post_adj_br_entries:
        try:
            for entry in _json.loads(case.post_adj_br_entries):
                no_val = entry.get("no") or entry.get("br_no")
                if no_val:
                    br_nos.append(int(no_val))
        except Exception:
            pass

    # Collect linked DR number
    dr_no_int = None
    if case.dr_no:
        try:
            dr_no_int = int(str(case.dr_no).strip())
        except (ValueError, TypeError):
            pass

    # Integer form of os_no for os_master / item_trans (legacy integer keys)
    os_no_int = None
    try:
        os_no_int = int(os_no)
    except (ValueError, TypeError):
        pass

    deleted: dict = {}

    def _del(sql: str, **params) -> int:
        r = db.execute(text(sql), params)
        return r.rowcount if r.rowcount is not None else 0

    # ── 1. cops_items and archive/temp copies ─────────────────────────────────
    deleted["cops_items"]         = _del("DELETE FROM cops_items WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)
    deleted["cops_items_deleted"] = _del("DELETE FROM cops_items_deleted WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)
    deleted["cops_items_temp"]    = _del("DELETE FROM cops_items_temp WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)

    # ── 2. Appeal (items first, then master) ──────────────────────────────────
    deleted["appeal_items"]  = _del("DELETE FROM appeal_items WHERE os_no = :n", n=os_no)
    deleted["appeal_master"] = _del("DELETE FROM appeal_master WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)

    # ── 3. UOS staging ────────────────────────────────────────────────────────
    deleted["uos_items"]  = _del("DELETE FROM uos_items WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)
    deleted["uos_master"] = _del("DELETE FROM uos_master WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)

    # ── 4. Report staging ─────────────────────────────────────────────────────
    deleted["os_rpt_items"]            = _del("DELETE FROM os_rpt_items WHERE os_no = :n", n=os_no)
    deleted["os_rpt_master"]           = _del("DELETE FROM os_rpt_master WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)
    deleted["os_item_compare_remarks"] = _del("DELETE FROM os_item_compare_remarks WHERE os_no = :n", n=os_no)

    # ── 5. os_master / item_trans (integer key + exact date for precision) ─────
    if os_no_int is not None and case.os_date:
        deleted["os_master"]          = _del("DELETE FROM os_master WHERE osnumber = :n AND osdate = :d", n=os_no_int, d=case.os_date)
        deleted["os_master_deleted"]  = _del("DELETE FROM os_master_deleted WHERE osnumber = :n AND osdate = :d", n=os_no_int, d=case.os_date)
        deleted["item_trans"]         = _del("DELETE FROM item_trans WHERE item_os_no = :n AND item_osdate = :d", n=os_no_int, d=case.os_date)
        deleted["item_trans_deleted"] = _del("DELETE FROM item_trans_deleted WHERE item_os_no = :n AND item_osdate = :d", n=os_no_int, d=case.os_date)

    # ── 6. Baggage Receipts (by specific BR numbers stored on the case) ────────
    br_del = 0
    br_items_del = 0
    for brn in set(br_nos):
        br_items_del += _del("DELETE FROM br_items WHERE br_no = :b", b=brn)
        br_del       += _del("DELETE FROM br_master WHERE br_no = :b AND os_no = :n", b=brn, n=os_no)
        _del("DELETE FROM old_br_items WHERE br_no = :b", b=brn)
        _del("DELETE FROM old_br_master WHERE br_no = :b", b=brn)
    if br_items_del:
        deleted["br_items"]  = br_items_del
    if br_del:
        deleted["br_master"] = br_del

    # ── 7. Detention Receipt (by the DR number stored on the case) ─────────────
    if dr_no_int is not None:
        deleted["dr_items"]  = _del("DELETE FROM dr_items WHERE dr_no = :d", d=dr_no_int)
        deleted["dr_master"] = _del("DELETE FROM dr_master WHERE dr_no = :d AND os_no = :n", d=dr_no_int, n=os_no)

    # ── 8. Warehouse — general (cascade via sub-query on wh_no) ───────────────
    _del("DELETE FROM wh_items WHERE wh_no IN (SELECT wh_no FROM wh_master WHERE os_no = :n)", n=os_no)
    _del("DELETE FROM wh_release WHERE wh_no IN (SELECT wh_no FROM wh_master WHERE os_no = :n)", n=os_no)
    _del("DELETE FROM wh_location_change WHERE wh_no IN (SELECT wh_no FROM wh_master WHERE os_no = :n)", n=os_no)
    deleted["wh_master"] = _del("DELETE FROM wh_master WHERE os_no = :n", n=os_no)

    # ── 9. Valuables warehouse ────────────────────────────────────────────────
    _del("DELETE FROM valuables_items WHERE wh_no IN (SELECT wh_no FROM valuables_master WHERE os_no = :n)", n=os_no)
    deleted["valuables_master"] = _del("DELETE FROM valuables_master WHERE os_no = :n", n=os_no)

    # ── 10. Mahazar / forwarding memo ─────────────────────────────────────────
    deleted["mahazar_items"]  = _del("DELETE FROM mahazar_items WHERE os_no = :n", n=os_no)
    deleted["mahazar_master"] = _del("DELETE FROM mahazar_master WHERE os_no = :n", n=os_no)

    # ── 11. cops_master archive and temp copies ────────────────────────────────
    deleted["cops_master_deleted"] = _del("DELETE FROM cops_master_deleted WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)
    deleted["cops_master_temp"]    = _del("DELETE FROM cops_master_temp WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)

    # ── 12. Primary record — must be last ─────────────────────────────────────
    deleted["cops_master"] = _del("DELETE FROM cops_master WHERE os_no = :n AND os_year = :y", n=os_no, y=body.os_year)

    try:
        db.commit()
    except Exception as _exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Purge failed during commit: {_exc}. No data was deleted.")

    total = sum(v for v in deleted.values() if isinstance(v, int))
    _log.warning(
        "ADMIN HARD-PURGE: OS %s/%s permanently deleted by '%s'. Total rows: %d. Breakdown: %s",
        os_no, body.os_year, admin.get("sub", "?"), total, deleted,
    )

    return {
        "message": f"OS {os_no}/{body.os_year} has been permanently deleted.",
        "total_rows_deleted": total,
        "breakdown": {k: v for k, v in sorted(deleted.items()) if v and v > 0},
    }
