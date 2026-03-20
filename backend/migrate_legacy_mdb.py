#!/usr/bin/env python3
"""
Legacy .mdb → SQLite Migration Script for COPS OS Cases.

Extracts cops_master and cops_items from an MS Access .mdb file
and inserts them into the new SQLite database with field name mapping.

Usage:
    python migrate_legacy_mdb.py --source "/path/to/file.mdb"
    python migrate_legacy_mdb.py --source "/path/to/file.mdb" --dry-run
    python migrate_legacy_mdb.py --source "/path/to/file.mdb" --db "./cops_br_database.db"

Requirements:
    - mdbtools (apt install mdbtools)
    - Python 3.8+
"""

import argparse
import csv
import io
import os
import subprocess
import sqlite3
import sys
from datetime import datetime, date


# ═══════════════════════════════════════════════════════════════════
# Field Mapping: old Access column name → new SQLite column name
# ═══════════════════════════════════════════════════════════════════

MASTER_FIELD_MAP = {
    # Direct matches (same name in both)
    "unique_no": "unique_no",
    "os_no": "os_no",
    "os_year": "os_year",
    "os_date": "os_date",
    "pax_name": "pax_name",
    "pax_name_modified_by_vig": "pax_name_modified_by_vig",
    "pax_address1": "pax_address1",
    "pax_address2": "pax_address2",
    "pax_address3": "pax_address3",
    "father_name": "father_name",
    "pax_date_of_birth": "pax_date_of_birth",
    "passport_no": "passport_no",
    "passport_date": "passport_date",
    "pax_nationality": "pax_nationality",
    "flight_no": "flight_no",
    "previous_visits": "previous_visits",
    "adj_offr_name": "adj_offr_name",
    "adj_offr_designation": "adj_offr_designation",
    "location_code": "location_code",
    "flight_date": "flight_date",
    "total_items": "total_items",
    "total_duty_amount": "total_duty_amount",
    "total_items_value": "total_items_value",
    "total_fa_value": "total_fa_value",
    "rf_amount": "rf_amount",
    "pp_amount": "pp_amount",
    "ref_amount": "ref_amount",
    "wh_amount": "wh_amount",
    "other_amount": "other_amount",
    "br_amount": "br_amount",
    "booked_by": "booked_by",
    "adjn_offr_remarks": "adjn_offr_remarks",
    "adjn_offr_remarks1": "adjn_offr_remarks1",
    "redeemed_value": "redeemed_value",
    "confiscated_value": "confiscated_value",
    "dutiable_value": "dutiable_value",
    "re_export_value": "re_export_value",
    "pax_image_filename": "pax_image_filename",
    "adjudication_date": "adjudication_date",
    "total_payable": "total_payable",
    "os_category": "os_category",
    "bkup_taken": "bkup_taken",
    "date_of_departure": "date_of_departure",
    "residence_at": "residence_at",
    "online_os": "online_os",
    "online_adjn": "online_adjn",
    "dr_no": "dr_no",
    "dr_year": "dr_year",
    "entry_deleted": "entry_deleted",
    "os_printed": "os_printed",
    "old_passport_no": "old_passport_no",
    "previous_os_details": "previous_os_details",
    "total_drs": "total_drs",
    "pax_status": "pax_status",
    "country_of_departure": "country_of_departure",
    "seizure_date": "seizure_date",

    # ── Renamed Fields ──
    "passport_issue_place": "pp_issue_place",
    "port_of_departure": "port_of_dep_dest",
    "abroad_stay": "stay_abroad_days",
    "supdt_remarks1": "supdts_remarks",
    "supdt_remarks2": "supdt_remarks2",

    # ── BR Linkage (renamed to avoid clash with "Other Taxes" br_amount) ──
    "br_no_str": "br_no_str",
    "br_no": "br_no_num",
    "br_date": "br_date_str",
    "br_amount_str": "br_amount_str",

    # ── Skipped ──
    # "table_name" — internal VB6 flag, not useful
}

ITEMS_FIELD_MAP = {
    "unique_no": "unique_no",
    "os_no": "os_no",
    "items_sno": "items_sno",
    "items_desc": "items_desc",
    "items_qty": "items_qty",
    "items_uqc": "items_uqc",
    "items_value": "items_value",
    "items_fa": "items_fa",
    "items_duty": "items_duty",
    "os_year": "os_year",
    "location_code": "location_code",
    "items_duty_type": "items_duty_type",
    "items_category": "items_category",
    "items_sub_category": "items_sub_category",
    "items_release_category": "items_release_category",
    "os_date": "os_date",
    "bkup_taken": "bkup_taken",
    "items_dr_no": "items_dr_no",
    "items_dr_year": "items_dr_year",
    "entry_deleted": "entry_deleted",
}


# ═══════════════════════════════════════════════════════════════════
# Date Parsing
# ═══════════════════════════════════════════════════════════════════

def parse_access_date(value: str) -> str | None:
    """
    Parse MS Access date formats into ISO format (YYYY-MM-DD).
    Access exports dates like: "07/09/12 00:00:00" or "10/27/09 00:00:00"
    Also handles: "MM/DD/YYYY", "YYYY-MM-DD", DOB text like "01/06/1955"
    """
    if not value or value.strip() in ("", "0"):
        return None

    value = value.strip().strip('"')
    if not value:
        return None

    # Try multiple formats
    formats = [
        "%m/%d/%y %H:%M:%S",    # 07/09/12 00:00:00 (2-digit year)
        "%m/%d/%Y %H:%M:%S",    # 07/09/2012 00:00:00
        "%m/%d/%y",              # 07/09/12
        "%m/%d/%Y",              # 07/09/2012
        "%d/%m/%Y",              # 09/07/2012 (DD/MM/YYYY)
        "%Y-%m-%d %H:%M:%S",    # 2012-07-09 00:00:00
        "%Y-%m-%d",              # 2012-07-09
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            # Sanity check: if 2-digit year parses to 20xx but data is from 19xx
            # Python's %y treats 00-68 as 2000-2068, 69-99 as 1969-1999
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If nothing worked, return None (but log it)
    return None


def safe_float(value: str) -> float | None:
    """Safely convert to float, returning None for empty/invalid."""
    if not value or value.strip() in ("", "0"):
        try:
            return float(value.strip()) if value.strip() else None
        except (ValueError, TypeError):
            return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        return None


def safe_int(value: str) -> int | None:
    """Safely convert to int, returning None for empty/invalid."""
    if not value or value.strip() == "":
        return None
    try:
        f = float(value.strip())
        return int(f)
    except (ValueError, TypeError):
        return None


def safe_str(value: str) -> str | None:
    """Clean string value — strip quotes, whitespace, return None for empty."""
    if value is None:
        return None
    value = value.strip().strip('"').strip()
    return value if value else None


# ═══════════════════════════════════════════════════════════════════
# Export from MDB
# ═══════════════════════════════════════════════════════════════════

def export_table_csv(mdb_path: str, table_name: str) -> list[dict]:
    """Export a table from .mdb to list of dicts using mdb-export."""

    print(f"  Exporting '{table_name}' from {os.path.basename(mdb_path)}...")

    result = subprocess.run(
        ["mdb-export", mdb_path, table_name],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        print(f"    ERROR: mdb-export failed: {result.stderr}")
        return []

    reader = csv.DictReader(io.StringIO(result.stdout))
    rows = list(reader)
    print(f"    Exported {len(rows)} rows")
    return rows


# ═══════════════════════════════════════════════════════════════════
# Date Fields (which columns need date parsing)
# ═══════════════════════════════════════════════════════════════════

MASTER_DATE_FIELDS = {
    "os_date", "passport_date", "flight_date", "adjudication_date",
    "seizure_date", "pax_date_of_birth"
}

ITEMS_DATE_FIELDS = {"os_date"}

MASTER_FLOAT_FIELDS = {
    "unique_no", "total_items", "total_duty_amount", "total_items_value",
    "total_fa_value", "rf_amount", "pp_amount", "ref_amount", "wh_amount",
    "other_amount", "br_amount", "redeemed_value", "confiscated_value",
    "dutiable_value", "re_export_value", "total_payable",
    "br_no", "br_amount_str", "abroad_stay", "total_drs"
}

MASTER_INT_FIELDS = {
    "os_year", "total_items", "abroad_stay", "total_drs"
}

ITEMS_FLOAT_FIELDS = {
    "unique_no", "items_qty", "items_value", "items_fa", "items_duty",
    "items_dr_no", "items_dr_year"
}

ITEMS_INT_FIELDS = {
    "os_year", "items_sno", "items_dr_no", "items_dr_year"
}


# ═══════════════════════════════════════════════════════════════════
# Transform Row
# ═══════════════════════════════════════════════════════════════════

def transform_master_row(old_row: dict) -> dict:
    """Transform old Access row to new SQLite row using field mapping."""
    new_row = {}

    for old_col, new_col in MASTER_FIELD_MAP.items():
        value = old_row.get(old_col, None)

        if value is None:
            continue

        # Apply type conversion based on old column name
        if old_col in MASTER_DATE_FIELDS:
            value = parse_access_date(value)
        elif old_col in MASTER_INT_FIELDS:
            value = safe_int(value)
        elif old_col in MASTER_FLOAT_FIELDS:
            value = safe_float(value)
        else:
            value = safe_str(value)

        if value is not None:
            new_row[new_col] = value

    return new_row


def transform_items_row(old_row: dict) -> dict:
    """Transform old Access items row to new SQLite row."""
    new_row = {}

    for old_col, new_col in ITEMS_FIELD_MAP.items():
        value = old_row.get(old_col, None)

        if value is None:
            continue

        if old_col in ITEMS_DATE_FIELDS:
            value = parse_access_date(value)
        elif old_col in ITEMS_INT_FIELDS:
            value = safe_int(value)
        elif old_col in ITEMS_FLOAT_FIELDS:
            value = safe_float(value)
        else:
            value = safe_str(value)

        if value is not None:
            new_row[new_col] = value

    return new_row


# ═══════════════════════════════════════════════════════════════════
# Existing-Key Loaders  (pre-check deduplication — no UNIQUE constraint needed)
# ═══════════════════════════════════════════════════════════════════

def load_existing_master_keys(conn: sqlite3.Connection) -> set:
    """Return set of (os_no, os_year, location_code) already in cops_master."""
    rows = conn.execute(
        "SELECT os_no, os_year, location_code FROM cops_master"
    ).fetchall()
    return {(str(r[0] or ""), int(r[1] or 0), str(r[2] or "")) for r in rows}


def load_existing_item_keys(conn: sqlite3.Connection) -> set:
    """Return set of (os_no, os_year, location_code, items_sno) already in cops_items."""
    rows = conn.execute(
        "SELECT os_no, os_year, location_code, items_sno FROM cops_items"
    ).fetchall()
    return {(str(r[0] or ""), int(r[1] or 0), str(r[2] or ""), int(r[3] or 0)) for r in rows}


# ═══════════════════════════════════════════════════════════════════
# Insert Into SQLite
# ═══════════════════════════════════════════════════════════════════

def batch_insert(conn: sqlite3.Connection, table: str, rows: list[dict],
                 existing_keys: set,
                 key_fn,
                 batch_size: int = 500) -> tuple[int, int, int]:
    """
    Insert rows in batches, skipping any whose key already exists in the DB.
    Returns (inserted, skipped, errors).

    existing_keys  — set of keys already in the DB (pre-loaded for speed)
    key_fn         — callable(row_dict) -> hashable key for deduplication
    """
    inserted = 0
    skipped = 0
    errors = 0
    total = len(rows)

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]

        for row in batch:
            if not row:
                skipped += 1
                continue

            key = key_fn(row)
            if key in existing_keys:
                skipped += 1
                continue

            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            values = list(row.values())

            try:
                conn.execute(
                    f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                    values
                )
                existing_keys.add(key)   # prevent in-batch duplicates too
                inserted += 1
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"    ERROR row: {e}")
                    if errors == 5:
                        print(f"    ... suppressing further error details")

        conn.commit()
        pct = min(100, int((i + len(batch)) / total * 100))
        print(f"    Progress: {pct}% ({inserted} inserted, {skipped} skipped, {errors} errors)")

    return inserted, skipped, errors


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy .mdb OS data to new SQLite database"
    )
    parser.add_argument(
        "--source", required=True,
        help="Path to the .mdb file to migrate from"
    )
    parser.add_argument(
        "--db", default="./cops_br_database.db",
        help="Path to the target SQLite database (default: ./cops_br_database.db)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and validate data without inserting into database"
    )
    parser.add_argument(
        "--tables", default="both",
        choices=["master", "items", "both"],
        help="Which tables to migrate (default: both)"
    )

    args = parser.parse_args()

    # Validate source file
    if not os.path.exists(args.source):
        print(f"ERROR: Source file not found: {args.source}")
        sys.exit(1)

    # Check mdb-export is available
    try:
        subprocess.run(["mdb-export", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        print("ERROR: mdb-export not found. Install mdbtools: sudo apt install mdbtools")
        sys.exit(1)

    print("=" * 60)
    print("LEGACY .MDB → SQLite MIGRATION")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Target: {args.db}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'LIVE INSERT'}")
    print(f"Tables: {args.tables}")
    print()

    # ── Step 1: Export from MDB ──
    master_rows = []
    items_rows = []

    if args.tables in ("master", "both"):
        raw_master = export_table_csv(args.source, "cops_master")
        print(f"  Transforming {len(raw_master)} master rows...")
        master_rows = [transform_master_row(r) for r in raw_master]
        master_rows = [r for r in master_rows if r.get("os_no")]  # drop empty
        print(f"  Valid master rows: {len(master_rows)}")

        # Show sample
        if master_rows:
            sample = master_rows[0]
            print(f"\n  Sample row: os_no={sample.get('os_no')}, "
                  f"os_year={sample.get('os_year')}, "
                  f"pax_name={sample.get('pax_name')}, "
                  f"passport_no={sample.get('passport_no')}")
        print()

    if args.tables in ("items", "both"):
        raw_items = export_table_csv(args.source, "cops_items")
        print(f"  Transforming {len(raw_items)} items rows...")
        items_rows = [transform_items_row(r) for r in raw_items]
        items_rows = [r for r in items_rows if r.get("os_no")]
        print(f"  Valid items rows: {len(items_rows)}")
        print()

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN COMPLETE — No data was written to the database.")
        print(f"  Would insert: {len(master_rows)} master rows, {len(items_rows)} items rows")
        print("=" * 60)

        # Show year distribution
        if master_rows:
            years = {}
            for r in master_rows:
                y = r.get("os_year", "?")
                years[y] = years.get(y, 0) + 1
            print("\n  OS Year Distribution:")
            for y in sorted(years.keys(), key=lambda x: x if isinstance(x, int) else 0):
                if isinstance(y, int) and 1900 <= y <= 2100:
                    print(f"    {y}: {years[y]} cases")
        return

    # ── Step 2: Insert into SQLite ──
    if not os.path.exists(args.db):
        print(f"ERROR: Target database not found: {args.db}")
        print("  Start the backend first to create the database, then run this script.")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=WAL")  # Better write performance

    print("=" * 60)
    print("INSERTING DATA")
    print("=" * 60)

    if master_rows:
        print(f"\n  Loading existing cops_master keys from DB...")
        existing_master = load_existing_master_keys(conn)
        print(f"  Found {len(existing_master)} existing master records — will skip duplicates")
        print(f"\n  Inserting {len(master_rows)} cops_master rows...")
        m_ins, m_skip, m_err = batch_insert(
            conn, "cops_master", master_rows,
            existing_keys=existing_master,
            key_fn=lambda r: (str(r.get("os_no", "")), int(r.get("os_year") or 0), str(r.get("location_code") or "")),
        )
        print(f"\n  cops_master: {m_ins} inserted, {m_skip} skipped, {m_err} errors")

    if items_rows:
        print(f"\n  Loading existing cops_items keys from DB...")
        existing_items = load_existing_item_keys(conn)
        print(f"  Found {len(existing_items)} existing item records — will skip duplicates")
        print(f"\n  Inserting {len(items_rows)} cops_items rows...")
        i_ins, i_skip, i_err = batch_insert(
            conn, "cops_items", items_rows,
            existing_keys=existing_items,
            key_fn=lambda r: (str(r.get("os_no", "")), int(r.get("os_year") or 0), str(r.get("location_code") or ""), int(r.get("items_sno") or 0)),
        )
        print(f"\n  cops_items: {i_ins} inserted, {i_skip} skipped, {i_err} errors")

    conn.close()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)

    # ── Verify ──
    conn = sqlite3.connect(args.db)
    m_count = conn.execute("SELECT COUNT(*) FROM cops_master").fetchone()[0]
    i_count = conn.execute("SELECT COUNT(*) FROM cops_items").fetchone()[0]
    print(f"\n  Final counts:")
    print(f"    cops_master: {m_count} total rows")
    print(f"    cops_items:  {i_count} total rows")

    # Show recent records
    recent = conn.execute(
        "SELECT os_no, os_year, pax_name, passport_no FROM cops_master "
        "ORDER BY os_year DESC, CAST(os_no AS INTEGER) DESC LIMIT 5"
    ).fetchall()
    if recent:
        print(f"\n  Most recent records:")
        for r in recent:
            print(f"    OS {r[0]}/{r[1]} — {r[2]} (PP: {r[3]})")

    conn.close()


if __name__ == "__main__":
    main()
