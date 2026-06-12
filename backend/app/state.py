"""
Runtime mutable application state — shared across modules.
All values are populated from the DB during lifespan startup and updated
live by the admin API without requiring a server restart.

Rules:
  - This module imports NOTHING from the app package (no circular imports).
  - Only main.py and admin_api.py write to these values.
  - All other modules read from them.
"""

# True = Production mode (whitelist enforced, rate limiting active, strict SQLite)
# False = Development mode (all security gates relaxed)
prod_mode: bool = False

# In-memory set of allowed IP addresses (refreshed from DB on every CRUD op)
# 127.0.0.1 and ::1 are always allowed in code — not stored here.
allowed_ips: set[str] = set()

# Trial configuration — loaded from DB at startup, updated live by admin endpoints.
# trial_expired is computed dynamically at each request using these values so that
# midnight expiry is detected without needing a server restart.
trial_disabled: bool = True          # True = no trial enforcement (permanent install)
trial_start_date: str | None = None  # ISO date string "YYYY-MM-DD"
trial_days: int = 30
