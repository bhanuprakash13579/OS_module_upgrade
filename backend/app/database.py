"""
SQLAlchemy database engine, session factory, and Base declarative class.
Supports both PostgreSQL (production) and SQLite (offline/desktop).

SQLite mode: the database is transparently encrypted with AES-256 via SQLCipher
when the `sqlcipher3` package is available.  Without it the app falls back to
plain SQLite with a warning — all features still work.

Encryption key derivation
─────────────────────────
  derive_db_key()  →  PBKDF2-HMAC-SHA256(_BINDING_SECRET, fixed_salt, 100 000)

The key is the same for every instance built from the same source.  An attacker
who has only the .db file cannot decrypt it (they need the binary/source to
obtain _BINDING_SECRET).  You (the developer) always have the source → you can
always recover any database.

LAN sync is unaffected: slave nodes communicate via the HTTP API, never by
direct file access.
"""
import logging
import os
import sqlite3 as _stdlib_sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# ── Try to load SQLCipher ────────────────────────────────────────────────────

_cipher_module = None   # sqlcipher3 module if available
_DB_KEY: str | None = None  # 64-char hex key

if settings.DATABASE_URL.startswith("sqlite"):
    try:
        import sqlcipher3 as _cipher_module      # type: ignore[import]
        from app.security.device import derive_db_key
        _DB_KEY = derive_db_key()
        logger.info("SQLCipher available — database encryption is ENABLED.")
    except ImportError as _ie:
        import traceback as _tb
        _cipher_module = None
        _DB_KEY = None
        logger.warning(
            "sqlcipher3 package not found — database will NOT be encrypted. "
            "Install 'sqlcipher3' to enable AES-256 at-rest encryption. "
            "Import error detail: %s", _ie
        )
        logger.debug("sqlcipher3 import traceback:\n%s", _tb.format_exc())


# ── One-time plaintext → encrypted migration ─────────────────────────────────

def _migrate_plaintext_to_encrypted(db_path: str, db_key: str) -> None:
    """
    If the database file exists and is a plaintext SQLite file, encrypt it
    in place using SQLCipher's sqlcipher_export().  Called once before the
    engine is created so SQLAlchemy never sees an unencrypted connection.

    Detection logic
    ───────────────
    1. Try opening with the key → if readable, already encrypted → done.
    2. Try opening without any key (stdlib sqlite3) → if readable, it is
       plaintext → use ATTACH + sqlcipher_export() to create an encrypted
       copy, then replace the original file atomically.
    3. If both fail → file is corrupt or encrypted with a different key.
       Log a critical error and leave it untouched.

    Migration technique (sqlcipher_export)
    ───────────────────────────────────────
    PRAGMA rekey only works on already-encrypted databases. For a plaintext
    source we instead open it without a key (plaintext mode), ATTACH a new
    temp file as an encrypted database, run sqlcipher_export() to copy all
    data, DETACH, then os.replace() the temp file over the original.
    """
    if not os.path.exists(db_path):
        return  # brand-new install — will be created encrypted

    assert _cipher_module is not None, "should not be called without sqlcipher3"
    hex_pragma = f"PRAGMA key = \"x'{db_key}'\""

    # ── Step 1: try to read as already-encrypted ─────────────────────────────
    try:
        conn = _cipher_module.connect(db_path)
        conn.execute(hex_pragma)
        conn.execute("SELECT count(*) FROM sqlite_master")
        conn.close()
        logger.debug("Database already encrypted with SQLCipher — no migration needed.")
        return
    except Exception:
        pass  # not yet encrypted, continue

    # ── Step 2: verify it is readable as plaintext ────────────────────────────
    try:
        chk = _stdlib_sqlite3.connect(db_path)
        chk.execute("SELECT count(*) FROM sqlite_master")
        chk.close()
    except Exception:
        logger.critical(
            "Cannot open database as either encrypted or plaintext. "
            "The file may be corrupt or encrypted with a different key. "
            "NOT attempting migration to avoid data loss."
        )
        return

    # ── Step 3: plaintext confirmed — export to encrypted via sqlcipher_export ─
    logger.info("One-time migration: encrypting plaintext database with AES-256 (SQLCipher)…")
    import tempfile as _tempfile
    tmp_fd, tmp_path = _tempfile.mkstemp(suffix=".db", dir=os.path.dirname(db_path))
    try:
        os.close(tmp_fd)
        os.unlink(tmp_path)  # remove so sqlcipher3 creates it fresh
        # Open source as plaintext (no PRAGMA key = opens in unencrypted mode)
        conn = _cipher_module.connect(db_path)
        # Flush any WAL into the main file first
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        # ATTACH a new encrypted database and export all data into it
        conn.execute(f"ATTACH DATABASE '{tmp_path}' AS encrypted KEY \"x'{db_key}'\"")
        conn.execute("SELECT sqlcipher_export('encrypted')")
        conn.execute("DETACH DATABASE encrypted")
        conn.close()
        # Atomically replace the original with the encrypted copy
        os.replace(tmp_path, db_path)
        logger.info("Database encrypted successfully — all subsequent opens require the AES key.")
    except Exception as exc:
        logger.critical(
            "Failed to encrypt the database: %s. The original file has NOT been modified.",
            exc,
        )
        # Clean up temp file if it still exists
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass


# ── Resolve the SQLite file path ─────────────────────────────────────────────

def _resolve_db_path() -> str:
    """Resolve the absolute filesystem path from DATABASE_URL."""
    raw = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    return raw if os.path.isabs(raw) else os.path.abspath(raw)


# ── Build the SQLAlchemy engine ───────────────────────────────────────────────

if settings.DATABASE_URL.startswith("sqlite"):
    _db_path = _resolve_db_path()

    if _cipher_module and _DB_KEY:
        # ── Encrypted path ───────────────────────────────────────────────────
        _migrate_plaintext_to_encrypted(_db_path, _DB_KEY)

        _hex_pragma = f"PRAGMA key = \"x'{_DB_KEY}'\""

        def _make_cipher_conn():
            """
            Connection factory for SQLAlchemy pool.
            Opens the database via sqlcipher3 and sets the AES-256 key as the
            very first command — this is required by SQLCipher.
            """
            conn = _cipher_module.connect(_db_path, check_same_thread=False)  # type: ignore[union-attr]
            conn.execute(_hex_pragma)
            # Explicitly state page size 4096 since the DB was migrated from a stock SQLite database
            conn.execute("PRAGMA cipher_page_size = 4096")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-32000")
            return conn

        engine = create_engine(
            "sqlite://",          # dialect hint only; creator= overrides the connection
            creator=_make_cipher_conn,
            echo=settings.DEBUG,
            pool_pre_ping=False,  # pre_ping issues a SELECT 1 which needs no key on encrypted DB
        )

    else:
        # ── Plaintext fallback ───────────────────────────────────────────────
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.DEBUG,
            pool_pre_ping=False,
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-32000")
            cursor.close()

else:
    # ── PostgreSQL (or any other non-SQLite) ─────────────────────────────────
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )


# ── Session ──────────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base ─────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency ───────────────────────────────────────────────────────────────
def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Public helpers (used by backup.py) ───────────────────────────────────────

def get_cipher_module():
    """Return the sqlcipher3 module if encryption is active, else None."""
    return _cipher_module


def get_db_key() -> str | None:
    """Return the active SQLCipher hex key, or None if not encrypted."""
    return _DB_KEY


def get_db_path() -> str | None:
    """Return the absolute path to the SQLite file, or None for non-SQLite."""
    if settings.DATABASE_URL.startswith("sqlite"):
        return _resolve_db_path()
    return None


def migrate_plaintext_to_encrypted(db_path: str, db_key: str) -> None:
    """
    Public alias for _migrate_plaintext_to_encrypted.
    Used by the restore endpoint to encrypt a plaintext backup after restoring it.
    No-op if sqlcipher3 is not loaded.
    """
    if _cipher_module is not None:
        _migrate_plaintext_to_encrypted(db_path, db_key)
