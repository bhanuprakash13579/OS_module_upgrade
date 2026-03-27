"""
Device binding & LAN-only security.

How it works
────────────
1. On the authorized machine the admin clicks "Register This Device" in the
   hidden admin page.  This writes a `machine.key` file into the same
   AppData folder as the database.

2. On every startup the Python server checks:
     a. Does machine.key exist?
     b. Does its content match an HMAC of the current machine's MAC address?
   If either check fails → the server starts, but every API call returns 403.

3. A LAN-only middleware rejects HTTP requests that come from outside
   private IP ranges (blocks internet / VPN / other-network access).

Threat model this covers
────────────────────────
• Someone copies the .exe to another PC           → no machine.key → blocked
• Someone copies .exe + machine.key               → MAC mismatch  → blocked
• Someone copies .exe + machine.key + DB          → MAC mismatch  → blocked
• App accessed over the internet / non-LAN        → middleware     → blocked
"""

import hashlib
import hmac
import ipaddress
import os
import platform
import uuid
from pathlib import Path

# ── Binding secret ────────────────────────────────────────────────────────────
# Read from BINDING_SECRET env variable (set via GitHub Secret at build time).
# Falls back to a local-dev placeholder — never used in production builds.
_BINDING_SECRET: bytes = os.environb.get(
    b"BINDING_SECRET",
    b"cops-dev-only-fallback-do-not-use-in-prod",
)


# ═══════════════════════════════════════════════════════════════════
# Fingerprint helpers
# ═══════════════════════════════════════════════════════════════════

def _get_mac_address() -> str:
    """Return the primary MAC address as a hex string."""
    return hex(uuid.getnode())


_fingerprint_cache: str | None = None

def _compute_fingerprint() -> str:
    """
    Compute a machine-specific fingerprint:
        HMAC-SHA256( _BINDING_SECRET, "MAC:hostname" )
    Tied to both the hardware MAC and the hostname so that even
    a VM clone with spoofed MAC is harder to fake.
    Result is cached for the lifetime of the process — MAC and hostname
    do not change at runtime, and uuid.getnode() can be slow on Windows.
    """
    global _fingerprint_cache
    if _fingerprint_cache is not None:
        return _fingerprint_cache
    mac = _get_mac_address()
    hostname = platform.node().lower()
    message = f"{mac}:{hostname}".encode()
    _fingerprint_cache = hmac.new(_BINDING_SECRET, message, hashlib.sha256).hexdigest()
    return _fingerprint_cache


# ═══════════════════════════════════════════════════════════════════
# Key file helpers
# ═══════════════════════════════════════════════════════════════════

def _key_path() -> Path:
    """
    Resolve the path to machine.key.
    Stored alongside the database in the AppData folder when running
    as a packaged Tauri app, or next to the DB in dev mode.
    """
    cops_db = os.environ.get("COPS_DB_PATH", "./cops_br_database.db")
    return Path(cops_db).parent / "machine.key"


_registered_cache: bool | None = None

def is_device_registered() -> bool:
    """Return True if machine.key exists and matches current hardware.
    Result is cached — file I/O + HMAC on every HTTP request adds latency.
    Cache is invalidated when register_device() is called."""
    global _registered_cache
    if _registered_cache is not None:
        return _registered_cache
    path = _key_path()
    if not path.exists():
        _registered_cache = False
        return False
    try:
        stored = path.read_text().strip()
        expected = _compute_fingerprint()
        _registered_cache = hmac.compare_digest(stored, expected)
    except Exception:
        _registered_cache = False
    return _registered_cache


def register_device() -> str:
    """
    Write machine.key for the current device.
    Returns the fingerprint string (for admin confirmation display).
    """
    global _registered_cache
    fingerprint = _compute_fingerprint()
    path = _key_path()
    path.write_text(fingerprint)
    _registered_cache = True  # invalidate / update cache immediately
    return fingerprint


def derive_secret_key() -> str:
    """
    Derive a machine-specific JWT signing secret at runtime.
    Combines the binding secret + MAC + hostname → 64-char hex string.
    This means JWTs signed on one machine are invalid on any other machine,
    even if an attacker extracts the binary and finds the binding secret.
    """
    mac = _get_mac_address()
    hostname = platform.node().lower()
    message = f"jwt-secret:{mac}:{hostname}".encode()
    return hmac.new(_BINDING_SECRET, message, hashlib.sha256).hexdigest()


def get_zip_password() -> bytes:
    """
    Return the AES-256 ZIP backup encryption password (= _BINDING_SECRET bytes).

    The user types exactly this string in 7-Zip / WinRAR when opening an
    exported CSV backup ZIP.  It is the same string defined in _BINDING_SECRET
    in this file — always findable in the GitHub source.

    Example (7-Zip): File → Open Archive → enter password:
      cops-chennai-customs-binding-2024-!@#secure
    """
    return _BINDING_SECRET


def derive_db_key() -> str:
    """
    Derive the AES-256 SQLCipher database encryption key.

    Algorithm: PBKDF2-HMAC-SHA256(password=_BINDING_SECRET, salt=fixed_salt, iterations=100_000)
    Returns a 64-char lowercase hex string (= 32 bytes = AES-256 key).

    Design rationale
    ────────────────
    • Key is constant for all instances built from the same binary source.
    • An attacker who has only the .db file cannot read it — they need the
      compiled binary (which contains _BINDING_SECRET buried in PyInstaller
      byte-code) to derive this key.
    • The developer always has the source code → always knows _BINDING_SECRET
      → can always derive this key → can always decrypt a copied/recovered DB.
    • Deliberately NOT machine-specific (no MAC/hostname) so that if the
      hardware dies you can still recover the database on any new machine.

    Recovery procedure (DB Browser for SQLite + SQLCipher extension)
    ────────────────────────────────────────────────────────────────
      1. GET /api/backup/db-cipher-key  (admin auth required) → copy the hex
      2. Open the .db file in DB Browser → Open Database → select "SQLCipher"
      3. In the "Key format" drop-down choose "Raw key / Hex key"
      4. Paste the 64-char hex string → click OK
    """
    import hashlib
    _DB_CIPHER_SALT = b"cops-db-cipher-v1-2024-chennai-customs"
    key_bytes = hashlib.pbkdf2_hmac("sha256", _BINDING_SECRET, _DB_CIPHER_SALT, 100_000)
    return key_bytes.hex()  # 64-char hex = 256-bit AES key


def get_device_info() -> dict:
    """Return non-sensitive device info for the admin UI."""
    return {
        "mac": _get_mac_address(),
        "hostname": platform.node(),
        "registered": is_device_registered(),
        "key_path": str(_key_path()),
    }


# ═══════════════════════════════════════════════════════════════════
# LAN IP check
# ═══════════════════════════════════════════════════════════════════

_PRIVATE_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),    # loopback
    ipaddress.ip_network("10.0.0.0/8"),     # class A private
    ipaddress.ip_network("172.16.0.0/12"),  # class B private
    ipaddress.ip_network("192.168.0.0/16"), # class C private
    ipaddress.ip_network("::1/128"),        # IPv6 loopback
]


def is_lan_ip(ip: str) -> bool:
    """Return True if the IP is localhost or a private LAN address."""
    # Fast path: local desktop app always hits these — avoids ipaddress parsing
    if ip in ("127.0.0.1", "::1"):
        return True
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in _PRIVATE_RANGES)
    except ValueError:
        return False
