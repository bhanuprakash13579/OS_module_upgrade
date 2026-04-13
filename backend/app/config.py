"""
Application configuration — environment variables + legacy constants.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


def _resolve_db_url() -> str:
    """
    Resolve the SQLite database path.
    Priority:
      1. DATABASE_URL env var (explicit override / PostgreSQL)
      2. COPS_DB_PATH env var  (set by Tauri when running as desktop app)
      3. Fallback: ./cops_br_database.db  (dev / script usage)
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    cops_db_path = os.environ.get("COPS_DB_PATH")
    if cops_db_path:
        return f"sqlite:///{cops_db_path}"
    return "sqlite:///./cops_br_database.db"


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "COPS Customs Application"
    APP_VERSION: str = "3.0.11"
    # Set COPS_ENV=production in the environment (or .env file) to enable prod mode.
    # Anything else (including the default) is treated as development.
    COPS_ENV: str = "production"
    DEBUG: bool = True  # corrected after instantiation based on COPS_ENV
    SECRET_KEY: str = "cops-customs-secret-key-change-in-production"  # overridden at runtime by derive_secret_key()
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hour shift

    # ── Database ─────────────────────────────────────────────────
    # Resolved at startup — see _resolve_db_url() above.
    # Override via DATABASE_URL env var for PostgreSQL.
    DATABASE_URL: str = _resolve_db_url()

    # ── Legacy Access DB Passwords (for .mdb import) ─────────────
    LEGACY_DB_PASSWORDS: dict = {
        "cops_br_database.mdb": "brchn0312",
        "reports_db.mdb": "brmdu0113",
        "stats.mdb": "export0512",
        "ip_config.mdb": "locip6",
        "os_data_compare.mdb": "oswhchk",
        "seizures.mdb": "sezare108",
    }

    # ── Legacy Business Constants ────────────────────────────────
    ADJUDICATION_VALUE_LIMIT: float = 500000.0  # ₹5,00,000
    GOLD_MERIT_RATE: float = 35.0               # 35%
    SILVER_MERIT_RATE: float = 35.0              # 35%
    MIN_HANDLING_CHARGE_PER_PKG: float = 20.0    # ₹20
    GOLD_CONCESSION_MIN_DAYS_ABROAD: int = 180
    TR_MIN_DAYS_ABROAD: int = 90
    GOLD_FA_LIMIT: float = 50000.0              # ₹50,000 for 20gm
    JEWELLERY_FA_LIMIT: float = 100000.0        # ₹1,00,000 for 40gm
    BR_MAX_DIGITS: int = 8
    ADJN_REMARKS_MAX_CHARS: int = 3000   # Matches old module's txtDCRem MaxLength (3000)
    SUPDT_REMARKS_MAX_CHARS: int = 1500  # Matches old module's txtSupRem MaxLength (1500, sdo_2023.exe)
    AIDC_CUTOFF_DATE: str = "2021-02-01"        # AIDC = 0% before this
    DUTY_TIER_RATES: list = [35.0, 4.0, 8.0]

    # ── Default Margins ──────────────────────────────────────────
    DEFAULT_BR_TOP_MARGIN: float = 0.310
    DEFAULT_DR_TOP_MARGIN: float = 0.310

    # ── Default Shift ────────────────────────────────────────────
    # Matches old module: 7-19 day / 19-7 night
    DEFAULT_DAY_SHIFT_FROM: int = 7
    DEFAULT_DAY_SHIFT_TO: int = 19
    DEFAULT_NIGHT_SHIFT_FROM: int = 19
    DEFAULT_NIGHT_SHIFT_TO: int = 7

    # ── CORS ─────────────────────────────────────────────────────
    # Dev origins (Vite) are only included outside of production to avoid
    # exposing the desktop app's backend to localhost web pages in production.
    CORS_ORIGINS: list = [
        *(
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:1420",
                "http://127.0.0.1:1420",
            ]
            if os.environ.get("COPS_ENV", "production").strip().lower() != "production"
            else []
        ),
        "tauri://localhost",         # Tauri v2 macOS/Linux
        "http://tauri.localhost",    # Tauri v2 fallback
        "https://tauri.localhost",   # Tauri v2 Windows (uses HTTPS custom protocol)
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
settings.DEBUG = settings.COPS_ENV.strip().lower() != "production"
