"""
COPS Customs Application — FastAPI Entry Point.
Handles startup (DB table creation, seed data), CORS, and route registration.

LAN access: the server binds to 0.0.0.0:8000. Other PCs on the same physical
network can open a browser and navigate to http://<master-pc-ip>:8000 to use
the app. Static files (the React build) are served from the frontend_dist/
folder that is bundled alongside the Python binary by PyInstaller.
"""
from contextlib import asynccontextmanager
from datetime import date
import logging
import os
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.security.passwords import pwd_context
from app.security.device import is_device_registered, is_lan_ip, derive_secret_key
import app.state as state

# ── Derive machine-specific JWT secret at startup ────────────────────────────
# Replaces the static fallback in config.py so JWTs are always tied to this
# specific machine's hardware fingerprint. Even if an attacker extracts the
# binary and finds _BINDING_SECRET, they cannot forge tokens valid on this box.
settings.SECRET_KEY = derive_secret_key()

# Import ALL models so they are registered with Base.metadata
import app.models  # noqa: F401

# Initialize logger
logger = logging.getLogger(__name__)

def apply_sqlite_migrations():
    """
    Lightweight SQLite schema migrations for offline/desktop mode.
    SQLAlchemy `create_all()` does not add new columns to existing tables.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    # Columns to add for legacy migration compatibility
    LEGACY_COLS = [
        ("pax_name_modified_by_vig", "TEXT"),
        ("pax_image_filename", "TEXT"),
        ("total_fa_value", "REAL DEFAULT 0"),
        ("wh_amount", "REAL DEFAULT 0"),
        ("other_amount", "REAL DEFAULT 0"),
        ("br_no_str", "TEXT"),
        ("br_no_num", "REAL"),
        ("br_date_str", "TEXT"),
        ("br_amount_str", "TEXT"),
        ("os_category", "TEXT"),
        ("online_os", "TEXT"),
        ("adjn_offr_remarks1", "TEXT"),
        ("seizure_date", "DATE"),
        ("supdt_remarks2", "TEXT"),
        ("supdts_remarks", "TEXT"),
        # Soft-delete audit trail
        ("deleted_by", "TEXT"),
        ("deleted_reason", "TEXT"),
        ("deleted_on", "DATE"),
    ]

    TABLES_TO_MIGRATE = ["cops_master", "cops_master_deleted", "cops_master_temp"]

    with engine.connect() as conn:
        try:
            for table in TABLES_TO_MIGRATE:
                # Check if table exists
                exists = conn.execute(text(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                )).fetchone()
                if not exists:
                    continue

                cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                col_names = {c[1] for c in cols}

                for col_name, col_type in LEGACY_COLS:
                    if col_name not in col_names:
                        conn.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                        ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"SQLite migration error: {e}")

    # ── shift_timing_master: fix 10/22 → 7/19 for existing installs ──────────
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                UPDATE shift_timing_master
                SET day_shift_from_hrs=7, day_shift_to_hrs=19,
                    night_shift_from_hrs=19, night_shift_to_hrs=7
                WHERE day_shift_from_hrs=10 AND day_shift_to_hrs=22
            """))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"shift_timing migration error: {e}")

    # ── feature_flags: add prod_mode + session_timeout_minutes ───────────────
    with engine.connect() as conn:
        try:
            cols = conn.execute(text("PRAGMA table_info(feature_flags)")).fetchall()
            col_names = {c[1] for c in cols}
            if "prod_mode" not in col_names:
                conn.execute(text("ALTER TABLE feature_flags ADD COLUMN prod_mode BOOLEAN DEFAULT 0"))
            if "session_timeout_minutes" not in col_names:
                conn.execute(text("ALTER TABLE feature_flags ADD COLUMN session_timeout_minutes INTEGER DEFAULT 480"))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"feature_flags migration error: {e}")

    # ── allowed_devices: new table for IP/MAC whitelist ──────────────────────
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS allowed_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    ip_address TEXT,
                    mac_address TEXT,
                    hostname TEXT,
                    added_by TEXT DEFAULT 'sysadmin',
                    added_on DATE,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    notes TEXT
                )
            """))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"allowed_devices migration error: {e}")

    # ── cops_items.os_date: drop NOT NULL constraint (SQLite table rebuild) ──
    with engine.connect() as conn:
        try:
            pragma = conn.execute(text("PRAGMA table_info(cops_items)")).fetchall()
            # col[3] = notnull flag; col[1] = name
            os_date_col = next((c for c in pragma if c[1] == "os_date"), None)
            if os_date_col and os_date_col[3] == 1:  # still NOT NULL
                # Rebuild table without the NOT NULL on os_date
                conn.execute(text("PRAGMA foreign_keys=OFF"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS cops_items_new AS
                    SELECT * FROM cops_items WHERE 0
                """))
                conn.execute(text("DROP TABLE IF EXISTS cops_items_new"))
                conn.execute(text("""
                    CREATE TABLE cops_items_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        os_no VARCHAR(20) NOT NULL,
                        os_date DATE,
                        os_year INTEGER,
                        location_code VARCHAR(20),
                        items_sno INTEGER NOT NULL,
                        items_desc TEXT,
                        items_qty FLOAT DEFAULT 0,
                        items_uqc VARCHAR(20),
                        value_per_piece FLOAT DEFAULT 0,
                        items_value FLOAT DEFAULT 0,
                        items_fa FLOAT DEFAULT 0,
                        cumulative_duty_rate FLOAT DEFAULT 0,
                        items_duty FLOAT DEFAULT 0,
                        items_duty_type VARCHAR(100),
                        items_category VARCHAR(100),
                        items_release_category VARCHAR(100),
                        items_sub_category VARCHAR(100),
                        items_dr_no INTEGER DEFAULT 0,
                        items_dr_year INTEGER DEFAULT 0,
                        unique_no INTEGER,
                        entry_deleted VARCHAR(5) DEFAULT 'N',
                        bkup_taken VARCHAR(5) DEFAULT 'N'
                    )
                """))
                conn.execute(text("INSERT INTO cops_items_new SELECT * FROM cops_items"))
                conn.execute(text("DROP TABLE cops_items"))
                conn.execute(text("ALTER TABLE cops_items_new RENAME TO cops_items"))
                conn.execute(text("PRAGMA foreign_keys=ON"))
                conn.commit()
                print("✅ cops_items.os_date NOT NULL constraint removed")
        except Exception as e:
            conn.rollback()
            print(f"cops_items migration error: {e}")

    # ── cops_items: add FA type/qty/uqc columns ───────────────────────────────
    with engine.connect() as conn:
        for col, ddl in [
            ("items_fa_type", "ALTER TABLE cops_items ADD COLUMN items_fa_type VARCHAR(10) DEFAULT 'value'"),
            ("items_fa_qty",  "ALTER TABLE cops_items ADD COLUMN items_fa_qty REAL"),
            ("items_fa_uqc",  "ALTER TABLE cops_items ADD COLUMN items_fa_uqc VARCHAR(20)"),
        ]:
            try:
                conn.execute(text(ddl))
                conn.commit()
            except Exception:
                conn.rollback()  # column already exists — safe to ignore

    # ── Versioned config tables ───────────────────────────────────────────────
    _CONFIG_TABLES = {
        "print_template_config": """
            CREATE TABLE IF NOT EXISTS print_template_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_key TEXT NOT NULL,
                field_label TEXT,
                field_value TEXT NOT NULL,
                effective_from DATE NOT NULL,
                created_by TEXT,
                created_at DATETIME
            )
        """,
        "baggage_rules_config": """
            CREATE TABLE IF NOT EXISTS baggage_rules_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_key TEXT NOT NULL,
                rule_label TEXT,
                rule_value REAL NOT NULL,
                rule_uqc TEXT,
                effective_from DATE NOT NULL,
                created_by TEXT,
                created_at DATETIME
            )
        """,
        "special_item_allowances": """
            CREATE TABLE IF NOT EXISTS special_item_allowances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                keywords TEXT,
                allowance_qty REAL NOT NULL,
                allowance_uqc TEXT,
                effective_from DATE NOT NULL,
                active TEXT DEFAULT 'Y',
                created_by TEXT,
                created_at DATETIME
            )
        """,
    }
    with engine.connect() as conn:
        try:
            for tbl, ddl in _CONFIG_TABLES.items():
                conn.execute(text(ddl))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"config tables migration error: {e}")

    # ── print_template_config: remove all system-seeded rows ─────────────────
    # Legacy OS cases must use the hardcoded fallback headings in the app code.
    # Only admin-added entries (effective_from >= a real date) should be in the
    # table.  Rows with effective_from = '1900-01-01' were seeded by mistake and
    # would silently override every historical case on any DB that still has them.
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "DELETE FROM print_template_config WHERE created_by = 'system'"
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"print_template_config cleanup error: {e}")


def seed_initial_data():
    """
    Seeds required default data on first run:
    - Default shift timing (7-19 day, 19-7 night) — matches old module
    - Default print margins (0.310, 0.310)
    - Versioned print template config (Baggage Rules 1994 → 2016 → 2026)
    - Versioned baggage rules (FA limits, gold limits)
    - Special item allowances (liquor, cigarettes, cigars, laptop)
    """
    db = SessionLocal()
    try:
        from app.models.auth import User
        from app.models.config import (
            ShiftTimingMaster, MarginMaster, FeatureFlags,
            PrintTemplateConfig, BaggageRulesConfig, SpecialItemAllowance,
        )

        # ── User seeding disabled for bootstrap testing ──
        # existing = db.query(User).filter(User.user_id == "bhanu@gmail.com").first()
        # if not existing:
        #     db.add(User(
        #         user_name="Bhanu Prakash",
        #         user_desig="Inspector",
        #         user_id="bhanu@gmail.com",
        #         user_pwd=pwd_context.hash("bhanu"),
        #         created_by="system",
        #         created_on=date.today(),
        #         user_status="ACTIVE",
        #         user_role="SDO_Admin"
        #     ))

        # existing = db.query(User).filter(User.user_id == "harish@gmail.com").first()
        # if not existing:
        #     db.add(User(
        #         user_name="Harish",
        #         user_desig="Officer",
        #         user_id="harish@gmail.com",
        #         user_pwd=pwd_context.hash("harish"),
        #         created_by="system",
        #         created_on=date.today(),
        #         user_status="ACTIVE",
        #         user_role="SDO"
        #     ))

        # existing = db.query(User).filter(User.user_id == "sdo1").first()
        # if not existing:
        #     db.add(User(
        #         user_name="SDO Officer",
        #         user_desig="Superintendent",
        #         user_id="sdo1",
        #         user_pwd=pwd_context.hash("sdo123"),
        #         created_by="system",
        #         created_on=date.today(),
        #         user_status="ACTIVE",
        #         user_role="SDO"
        #     ))

        # existing = db.query(User).filter(User.user_id == "dc1").first()
        # if not existing:
        #     db.add(User(
        #         user_name="DC Officer",
        #         user_desig="Deputy Commissioner",
        #         user_id="dc1",
        #         user_pwd=pwd_context.hash("dc123"),
        #         created_by="system",
        #         created_on=date.today(),
        #         user_status="ACTIVE",
        #         user_role="DC"
        #     ))

        # ── Seed Default Shift Timing ──
        if db.query(ShiftTimingMaster).count() == 0:
            db.add(ShiftTimingMaster(
                day_shift_from_hrs=settings.DEFAULT_DAY_SHIFT_FROM,
                day_shift_to_hrs=settings.DEFAULT_DAY_SHIFT_TO,
                night_shift_from_hrs=settings.DEFAULT_NIGHT_SHIFT_FROM,
                night_shift_to_hrs=settings.DEFAULT_NIGHT_SHIFT_TO,
            ))

        # ── Seed Default Margins ──
        if db.query(MarginMaster).count() == 0:
            db.add(MarginMaster(
                br_top_margin=settings.DEFAULT_BR_TOP_MARGIN,
                dr_top_margin=settings.DEFAULT_DR_TOP_MARGIN,
            ))

        # ── Seed Feature Flags (all OFF by default) ──
        if db.query(FeatureFlags).count() == 0:
            db.add(FeatureFlags(apis_enabled=False))

        # Print Template Config is intentionally NOT seeded.
        # The hardcoded fallbacks in the app code serve as the legacy headings
        # (Baggage Rules 1994 era).  Admin adds entries only when rules change.

        # ── Seed Baggage Rules Config ─────────────────────────────────────────
        if db.query(BaggageRulesConfig).count() == 0:
            from datetime import date as _date
            _brc = [
                # General FA — Indian / OCI passport holders
                BaggageRulesConfig(rule_key="fa_indian_oci",
                    rule_label="General Free Allowance — Indian / OCI Passport",
                    rule_value=50000, rule_uqc="INR",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                BaggageRulesConfig(rule_key="fa_indian_oci",
                    rule_label="General Free Allowance — Indian / OCI Passport",
                    rule_value=75000, rule_uqc="INR",
                    effective_from=_date(2016, 4, 1), created_by="system"),
                # General FA — Foreign passport holders
                BaggageRulesConfig(rule_key="fa_foreign",
                    rule_label="General Free Allowance — Foreign Passport",
                    rule_value=25000, rule_uqc="INR",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                # Gold — male allowance (grams)
                BaggageRulesConfig(rule_key="gold_male_gms",
                    rule_label="Gold Free Allowance — Male (grams)",
                    rule_value=20, rule_uqc="GMS",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                # Gold — female allowance (grams)
                BaggageRulesConfig(rule_key="gold_female_gms",
                    rule_label="Gold Free Allowance — Female (grams)",
                    rule_value=40, rule_uqc="GMS",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                # Gold — minimum stay abroad (days) to qualify for gold FA
                BaggageRulesConfig(rule_key="gold_min_stay_days",
                    rule_label="Gold FA: Minimum Stay Abroad (days)",
                    rule_value=365, rule_uqc="DAYS",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                # Gold — value cap for male (INR; 0 = no cap)
                BaggageRulesConfig(rule_key="gold_value_cap_male",
                    rule_label="Gold FA Value Cap — Male (INR; 0 = no cap)",
                    rule_value=50000, rule_uqc="INR",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                BaggageRulesConfig(rule_key="gold_value_cap_male",
                    rule_label="Gold FA Value Cap — Male (INR; 0 = no cap)",
                    rule_value=0, rule_uqc="INR",
                    effective_from=_date(2024, 7, 23), created_by="system"),
                # Gold — value cap for female (INR; 0 = no cap)
                BaggageRulesConfig(rule_key="gold_value_cap_female",
                    rule_label="Gold FA Value Cap — Female (INR; 0 = no cap)",
                    rule_value=100000, rule_uqc="INR",
                    effective_from=_date(1900, 1, 1), created_by="system"),
                BaggageRulesConfig(rule_key="gold_value_cap_female",
                    rule_label="Gold FA Value Cap — Female (INR; 0 = no cap)",
                    rule_value=0, rule_uqc="INR",
                    effective_from=_date(2024, 7, 23), created_by="system"),
            ]
            db.add_all(_brc)

        # ── Seed Special Item Allowances ──────────────────────────────────────
        if db.query(SpecialItemAllowance).count() == 0:
            from datetime import date as _date
            _sia = [
                SpecialItemAllowance(item_name="Liquor",
                    keywords="liquor,whisky,whiskey,wine,beer,brandy,vodka,rum,gin,alcohol,scotch,champagne,cognac,bardinet,chivas,smirnoff,absolut,bacardi,bourbon",
                    allowance_qty=2, allowance_uqc="LTR",
                    effective_from=_date(1900, 1, 1), active='Y', created_by="system"),
                SpecialItemAllowance(item_name="Cigarettes",
                    keywords="cigarette,cigarettes,marlboro,dunhill,555,benson,hedges,gudang,garam,camel,winston,virginia,silk cut",
                    allowance_qty=100, allowance_uqc="NOS",
                    effective_from=_date(1900, 1, 1), active='Y', created_by="system"),
                SpecialItemAllowance(item_name="Cigars",
                    keywords="cigar,cigars,havana,cohiba,romeo,julieta",
                    allowance_qty=25, allowance_uqc="NOS",
                    effective_from=_date(1900, 1, 1), active='Y', created_by="system"),
                SpecialItemAllowance(item_name="Laptop / Notepad",
                    keywords="laptop,notebook,macbook,notepad,netbook",
                    allowance_qty=1, allowance_uqc="NOS",
                    effective_from=_date(1900, 1, 1), active='Y', created_by="system"),
            ]
            db.add_all(_sia)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


def _load_state_from_db():
    """
    Populate app.state from environment + DB.
    prod_mode is set by the COPS_ENV environment variable (code/deploy-time decision).
    The IP whitelist is admin-configurable at runtime via the DB.
    """
    from app.models.security import AllowedDevice

    # Mode is code-only — set COPS_ENV=production to enable
    state.prod_mode = settings.COPS_ENV.strip().lower() == "production"

    db = SessionLocal()
    try:
        devices = db.query(AllowedDevice).filter(AllowedDevice.is_active == True).all()
        state.allowed_ips = {d.ip_address for d in devices if d.ip_address}
        mode_label = "PRODUCTION" if state.prod_mode else "DEVELOPMENT"
        print(f"✅ App mode: {mode_label} | Whitelisted IPs: {len(state.allowed_ips)}")
    except Exception as e:
        print(f"State load error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables and seed data on startup."""
    # Create all 68 tables
    Base.metadata.create_all(bind=engine)
    print(f"✅ Created {len(Base.metadata.tables)} database tables")

    # Apply lightweight migrations (SQLite)
    apply_sqlite_migrations()

    # Seed default data
    seed_initial_data()
    print("✅ Seed data loaded (test users, shift timing, margins)")

    # Populate runtime state from DB
    _load_state_from_db()

    # mDNS LAN Replication Engine disabled — conflicts with uvicorn's event loop.
    # LAN access works via 0.0.0.0 binding without mDNS discovery.
    print("✅ LAN access ready (mDNS sync engine disabled)")

    yield  # Application runs here

    # Shutdown
    print("🛑 COPS Application shutting down")


# ── Create App ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="COPS Customs Application — Modernized from legacy VB6",
    lifespan=lifespan,
)

# ── Security Middleware ───────────────────────────────────────────
# Endpoints always allowed from any LAN IP (no device-registration required)
_OPEN_PATHS = {"/health", "/", "/api/features", "/api/mode"}
# Auth endpoints always open (LAN clients need to log in)
_OPEN_PREFIXES = ("/api/auth/",)
# Admin panel — master terminal (localhost) only
_LOCALHOST_ONLY_PREFIXES = ("/api/admin/",)
# These IPs are considered the master terminal
_LOCALHOST = {"127.0.0.1", "::1"}

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"

    # Always let CORS preflight through
    if request.method == "OPTIONS":
        return await call_next(request)

    # 1. LAN-only check — block non-private IPs (internet / VPN)
    if not is_lan_ip(client_ip):
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied: connections from outside the local network are not allowed."}
        )

    path = request.url.path
    is_localhost = client_ip in _LOCALHOST

    # 2. Admin panel — only the master terminal (localhost) may access it
    if any(path.startswith(p) for p in _LOCALHOST_ONLY_PREFIXES):
        if not is_localhost:
            return JSONResponse(
                status_code=403,
                content={"detail": "The admin panel is only accessible from the master terminal."}
            )
        return await call_next(request)

    # 3. Auth endpoints — open to all LAN clients (login, change-password, etc.)
    if path in _OPEN_PATHS or any(path.startswith(p) for p in _OPEN_PREFIXES):
        return await call_next(request)

    # 4. Device binding check — only enforced in production mode
    if state.prod_mode and not is_device_registered():
        return JSONResponse(
            status_code=403,
            content={"detail": "This device is not authorised. Please contact your administrator to register this device."}
        )

    # 4b. IP whitelist — only enforced in production mode (localhost always passes)
    if state.prod_mode and not is_localhost and client_ip not in state.allowed_ips:
        return JSONResponse(
            status_code=403,
            content={"detail": "Your device is not on the approved access list. Contact the administrator to add your IP address."}
        )

    # 5. Delete restriction for LAN browser clients
    #    LAN clients (slave terminals) can add and edit records freely,
    #    but only the master terminal may delete them.
    if not is_localhost and request.method == "DELETE":
        return JSONResponse(
            status_code=403,
            content={"detail": "Delete is not allowed from a slave terminal. Only the master terminal can delete records."}
        )

    return await call_next(request)


# ── CORS ─────────────────────────────────────────────────────────
# IMPORTANT: add_middleware(CORSMiddleware) must come AFTER @app.middleware("http")
# so that CORS is the outermost layer and adds headers even to early-return
# security responses (device-not-registered 403, LAN-only 403, etc.).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ─────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "device_registered": is_device_registered(),
    }


@app.get("/")
def root():
    return {"message": "COPS Customs Application API"}


@app.get("/api/features")
def get_features():
    """
    Public endpoint — no auth required.
    Returns which optional modules are currently enabled by the admin.
    Used by the landing page to conditionally show module cards.
    """
    from app.models.config import FeatureFlags
    db = SessionLocal()
    try:
        flags = db.query(FeatureFlags).first()
        return {"apis_enabled": bool(flags.apis_enabled) if flags else False}
    finally:
        db.close()


@app.get("/api/mode")
def get_mode():
    """
    Public endpoint — no auth required.
    Returns the current app mode so the frontend can show/hide the DEV MODE banner.
    """
    return {"prod_mode": state.prod_mode}


from app.api import auth, masters, baggage, offence, detention
from app.api import admin_api
from app.api import warehouse, mhb, fuel, appeal, revenue, sync, queries, reports, dashboard, os_query, backup
from app.api import apis

app.include_router(admin_api.router, prefix="/api/admin", tags=["System Admin"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(masters.router, prefix="/api/masters", tags=["Masters"])
app.include_router(baggage.router, prefix="/api/br", tags=["Baggage Receipts"])
app.include_router(offence.router, prefix="/api/os", tags=["Offence Cases"])
app.include_router(detention.router, prefix="/api/dr", tags=["Detention Receipts"])
app.include_router(warehouse.router, prefix="/api/warehouse", tags=["Warehouse"])
app.include_router(mhb.router, prefix="/api/mhb", tags=["MHB"])
app.include_router(fuel.router, prefix="/api/fuel", tags=["Fuel"])
app.include_router(appeal.router, prefix="/api/appeal", tags=["Appeal"])
app.include_router(revenue.router, prefix="/api/revenue", tags=["Revenue & Challans"])
app.include_router(sync.router, prefix="/api/sync", tags=["Synchronization"])
app.include_router(queries.router, prefix="/api/queries", tags=["Universal Query"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard Analytics"])
app.include_router(os_query.router)
app.include_router(backup.router, prefix="/api/backup", tags=["Backup & Restore"])
app.include_router(apis.router, prefix="/api/apis", tags=["APIS Matching"])


# ── Serve React frontend for LAN browser clients ─────────────────────────────
# When the server binds to 0.0.0.0, other PCs on the LAN can open a browser
# and navigate to http://<master-ip>:8000. FastAPI serves the compiled React
# build so they get the full UI without installing anything.
#
# Path resolution:
#   PyInstaller bundle  → sys._MEIPASS/frontend_dist/
#   Development mode    → ../../frontend/dist/  (relative to this file)

def _frontend_dist() -> str | None:
    if getattr(sys, 'frozen', False):
        # Running inside a PyInstaller bundle
        candidate = os.path.join(sys._MEIPASS, 'frontend_dist')
    else:
        # Development: this file is at backend/app/main.py
        candidate = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
        )
    return candidate if os.path.isdir(candidate) else None


_dist = _frontend_dist()
if _dist:
    _assets = os.path.join(_dist, 'assets')
    if os.path.isdir(_assets):
        app.mount('/assets', StaticFiles(directory=_assets), name='spa-assets')

    @app.get('/{full_path:path}', include_in_schema=False)
    def serve_spa(full_path: str):
        """Catch-all: serve index.html so React Router handles client-side routes."""
        return FileResponse(os.path.join(_dist, 'index.html'))
