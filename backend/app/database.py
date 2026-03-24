"""
SQLAlchemy database engine, session factory, and Base declarative class.
Supports both PostgreSQL (production) and SQLite (offline/desktop).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# ── Engine ───────────────────────────────────────────────────────
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    # pool_pre_ping sends SELECT 1 before every checkout — needed for network
    # databases (PostgreSQL) but pure overhead for local SQLite files.
    pool_pre_ping=not settings.DATABASE_URL.startswith("sqlite"),
)

# Enable WAL mode for SQLite (better concurrent reads)
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        # ── Performance PRAGMAs ──────────────────────────────────────
        # synchronous=NORMAL is safe with WAL mode and ~2× faster for writes
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 32 MB page cache (default is ~2000 pages ≈ 8 MB)
        cursor.execute("PRAGMA cache_size=-32000")
        # Memory-mapped I/O: disabled for Windows compatibility (causes C-level segfaults
        # with PyInstaller + Uvicorn + Windows Defender interfering with page locks)
        # cursor.execute("PRAGMA mmap_size=268435456")
        cursor.close()


# ── Session ──────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency ───────────────────────────────────────────────────
def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
