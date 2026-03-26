"""
MDB Import Service — reads cops_master and cops_items directly from an
MS-Access .mdb file using mdbtools (mdb-export), maps legacy column names
to the new schema, and inserts missing records into the SQLite DB.

Column name differences between MDB and new schema:
  MDB                  → New DB
  ─────────────────────────────────────────────
  abroad_stay          → stay_abroad_days
  supdt_remarks1       → supdts_remarks
  passport_issue_place → pp_issue_place
  port_of_departure    → port_of_dep_dest
  br_no                → br_no_num
  br_date              → br_date_str  (stored as text)
  br_amount            → (already in br_amount; same field)
  table_name           → (skipped — not in new schema)
  adj_offr_designation → adj_offr_designation (same)
  unique_no            → unique_no (same)
"""

import csv
import io
import logging
import subprocess
import sys
from datetime import datetime, date as _date
from typing import Optional

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from app.models.offence import CopsMaster, CopsItems
from app.api.backup import _existing_os_keys, _existing_item_keys, _parse_date, _flt, post_import_optimise, set_bulk_pragma

_CURRENT_YEAR = _date.today().year


def _sanitize_year(raw_year: int, fallback_date: Optional[_date]) -> Optional[int]:
    """
    Reject impossible os_year values that are legacy data-entry errors
    (e.g. 20004 instead of 2004, caused by a stuck key or double-digit).

    Valid range: 1990 – current_year + 1.
    When out of range, uses fallback_date.year (the os_date column) which is
    always a proper calendar date and therefore reliable.
    Returns None only when both the raw year and the fallback date are unusable.
    """
    if 1990 <= raw_year <= _CURRENT_YEAR + 1:
        return raw_year
    if fallback_date is not None:
        return fallback_date.year
    return None


# ── Column rename map: MDB name → new DB column name ──────────────────────────
_MASTER_RENAME = {
    "abroad_stay":          "stay_abroad_days",
    "supdt_remarks1":       "supdts_remarks",
    "passport_issue_place": "pp_issue_place",
    "port_of_departure":    "port_of_dep_dest",
    "br_no":                "br_no_num",
    "br_date":              "br_date_str",
}

# Columns from MDB that don't exist in new schema — skip them
_MASTER_SKIP = {"table_name"}


def _flt_safe(val) -> Optional[float]:
    try:
        v = str(val or "").strip()
        return float(v) if v else None
    except (ValueError, TypeError):
        return None


def _int_safe(val) -> Optional[int]:
    try:
        v = str(val or "").strip()
        return int(float(v)) if v else None
    except (ValueError, TypeError):
        return None


def _str_safe(val) -> Optional[str]:
    v = str(val or "").strip()
    return v if v else None


def _export_table(mdb_path: str, table: str):
    """
    Read a table from the MDB file and return an iterable of row dicts.
    - Windows: uses pyodbc with the Microsoft Access ODBC driver.
    - Linux/macOS: uses mdb-export (mdbtools).
    All values are returned as strings to keep the rest of the parsing code
    unchanged regardless of platform.
    """
    if sys.platform == "win32":
        return _export_table_pyodbc(mdb_path, table)
    return _export_table_mdbtools(mdb_path, table)


def _export_table_mdbtools(mdb_path: str, table: str) -> csv.DictReader:
    """Linux/macOS: run mdb-export and return a DictReader over the output."""
    result = subprocess.run(
        ["mdb-export", mdb_path, table],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"mdb-export failed for {table}: {result.stderr}")
    return csv.DictReader(io.StringIO(result.stdout))


def _export_table_pyodbc(mdb_path: str, table: str) -> list:
    """
    Windows: read via pyodbc with the Microsoft Access ODBC driver.
    Returns a list of dicts with lowercased column names and string values,
    matching the output shape of csv.DictReader so the rest of the code is
    completely unchanged.

    Requires one of:
      • "Microsoft Access Driver (*.mdb, *.accdb)" — comes with the free
        Microsoft Access Database Engine 2016 Redistributable (64-bit).
        Download: https://www.microsoft.com/en-us/download/details.aspx?id=54920
      • "Microsoft Access Driver (*.mdb)" — the older JET driver,
        pre-installed on 32-bit Windows XP/7/8.
    If Microsoft Office (any version) is installed the driver is already present.
    """
    try:
        import pyodbc
    except ImportError:
        raise RuntimeError(
            "pyodbc is not installed. "
            "Run: pip install pyodbc"
        )

    available = set(pyodbc.drivers())
    driver = None
    for candidate in [
        "Microsoft Access Driver (*.mdb, *.accdb)",
        "Microsoft Access Driver (*.mdb)",
    ]:
        if candidate in available:
            driver = candidate
            break

    if driver is None:
        raise RuntimeError(
            "Microsoft Access ODBC driver not found on this Windows machine.\n"
            "Please download and install the free 'Microsoft Access Database Engine "
            "2016 Redistributable' from:\n"
            "  https://www.microsoft.com/en-us/download/details.aspx?id=54920\n"
            "Then restart the application and try again.\n"
            "(If Microsoft Office is already installed, try the 32-bit vs 64-bit "
            "version of the redistributable that matches your Office installation.)"
        )

    conn_str = f"Driver={{{driver}}};Dbq={mdb_path};Exclusive=No;ReadOnly=1;"
    try:
        conn = pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        raise RuntimeError(
            f"Could not open the .mdb file with the Access ODBC driver.\n"
            f"Error: {e}\n\n"
            f"Common causes:\n"
            f"  • 32-bit/64-bit mismatch: if Microsoft Office is 32-bit, install the\n"
            f"    32-bit Access Database Engine (or vice versa for 64-bit Python).\n"
            f"  • The file may be damaged or in an unsupported Access format.\n"
            f"  • Try opening the file in Microsoft Access first to verify it opens."
        )
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM [{table}]")
        columns = [col[0].lower() for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            # Convert every value to str so _str_safe / _flt_safe / _parse_date
            # work identically to the mdbtools CSV path.
            rows.append(dict(zip(columns, [str(v) if v is not None else "" for v in row])))
        return rows
    except pyodbc.Error as e:
        raise RuntimeError(f"Error reading table '{table}' from .mdb file: {e}")
    finally:
        conn.close()


def _existing_deleted_keys(db: Session) -> set:
    """Returns keys of masters currently marked entry_deleted='Y' in the DB."""
    rows = db.query(
        CopsMaster.os_no,
        CopsMaster.os_year,
        CopsMaster.location_code,
    ).filter(CopsMaster.entry_deleted == "Y").all()
    return {((r[0] or "").strip(), r[1], (r[2] or "").strip()) for r in rows}


def import_from_mdb(mdb_path: str, db: Session) -> dict:
    """
    Import cops_master, cops_master_deleted, and cops_items from an MDB file
    into the SQLite DB. Returns a summary dict with inserted/skipped counts.

    Blank items_sno (common in legacy data) is handled by assigning a
    sequential counter per case so all items are preserved.

    Active records in cops_master always win over deleted records — if the DB
    has a case marked deleted but cops_master has it as active, it is updated.
    """
    set_bulk_pragma(db)

    existing_masters = _existing_os_keys(db)
    deleted_masters  = _existing_deleted_keys(db)   # subset of existing_masters
    existing_items   = _existing_item_keys(db)

    master_inserted = master_skipped = master_invalid = 0
    master_reactivated = 0
    deleted_inserted = deleted_skipped = 0
    items_inserted  = items_skipped  = items_invalid  = 0

    # os_date lookup: (os_no, os_year, location_code) → date
    # Used to fill items.os_date when the MDB item row has no date
    _master_date_cache: dict = {}

    # Per-case item counter: used to assign sequential sno when items_sno is blank.
    # Key: (os_no, os_year, location_code), Value: next available sno.
    _case_sno_counter: dict = {}

    # ── cops_master ────────────────────────────────────────────────────────────
    for row in _export_table(mdb_path, "cops_master"):
        os_no = (row.get("os_no") or "").strip()
        if not os_no:
            master_invalid += 1
            continue
        try:
            os_year = int(float(row.get("os_year") or 0))
        except (ValueError, TypeError):
            master_invalid += 1
            continue
        os_date_parsed = _parse_date(row.get("os_date"))
        os_year = _sanitize_year(os_year, os_date_parsed)
        if os_year is None:
            master_invalid += 1
            continue

        location_code = (row.get("location_code") or "").strip()
        key = (os_no, os_year, location_code)
        mdb_entry_deleted = _str_safe(row.get("entry_deleted")) or "N"

        if key in existing_masters:
            # If DB has this as deleted but MDB cops_master has it as active →
            # overwrite ALL fields with the new active record's data.
            if key in deleted_masters and mdb_entry_deleted != "Y":
                db.query(CopsMaster).filter(
                    CopsMaster.os_no == os_no,
                    CopsMaster.os_year == os_year,
                    CopsMaster.location_code == location_code,
                ).update({
                    "os_date":                  os_date_parsed,
                    "pax_name":                 _str_safe(row.get("pax_name")),
                    "pax_name_modified_by_vig": _str_safe(row.get("pax_name_modified_by_vig")),
                    "pax_address1":             _str_safe(row.get("pax_address1")),
                    "pax_address2":             _str_safe(row.get("pax_address2")),
                    "pax_address3":             _str_safe(row.get("pax_address3")),
                    "father_name":              _str_safe(row.get("father_name")),
                    "pax_date_of_birth":        _parse_date(row.get("pax_date_of_birth")) if row.get("pax_date_of_birth") else None,
                    "passport_no":              _str_safe(row.get("passport_no")),
                    "passport_date":            _parse_date(row.get("passport_date")) if row.get("passport_date") else None,
                    "pax_nationality":          _str_safe(row.get("pax_nationality")),
                    "pax_status":               _str_safe(row.get("pax_status")),
                    "residence_at":             _str_safe(row.get("residence_at")),
                    "country_of_departure":     _str_safe(row.get("country_of_departure")),
                    "date_of_departure":        _str_safe(row.get("date_of_departure")),
                    "old_passport_no":          _str_safe(row.get("old_passport_no")),
                    "previous_visits":          _str_safe(row.get("previous_visits")),
                    "stay_abroad_days":         _int_safe(row.get("abroad_stay")),
                    "supdts_remarks":           _str_safe(row.get("supdt_remarks1")),
                    "pp_issue_place":           _str_safe(row.get("passport_issue_place")),
                    "port_of_dep_dest":         _str_safe(row.get("port_of_departure")),
                    "br_no_num":                _flt_safe(row.get("br_no")),
                    "br_date_str":              _str_safe(row.get("br_date")),
                    "flight_no":                _str_safe(row.get("flight_no")),
                    "flight_date":              _parse_date(row.get("flight_date")) if row.get("flight_date") else None,
                    "adj_offr_name":            _str_safe(row.get("adj_offr_name")),
                    "adj_offr_designation":     _str_safe(row.get("adj_offr_designation")),
                    "adjn_offr_remarks":        _str_safe(row.get("adjn_offr_remarks")),
                    "adjn_offr_remarks1":       _str_safe(row.get("adjn_offr_remarks1")),
                    "booked_by":                _str_safe(row.get("booked_by")),
                    "total_items":              _int_safe(row.get("total_items")),
                    "total_items_value":        _flt_safe(row.get("total_items_value")) or 0.0,
                    "total_fa_value":           _flt_safe(row.get("total_fa_value")) or 0.0,
                    "total_duty_amount":        _flt_safe(row.get("total_duty_amount")) or 0.0,
                    "total_payable":            _flt_safe(row.get("total_payable")) or 0.0,
                    "dutiable_value":           _flt_safe(row.get("dutiable_value")) or 0.0,
                    "redeemed_value":           _flt_safe(row.get("redeemed_value")) or 0.0,
                    "re_export_value":          _flt_safe(row.get("re_export_value")) or 0.0,
                    "confiscated_value":        _flt_safe(row.get("confiscated_value")) or 0.0,
                    "rf_amount":                _flt_safe(row.get("rf_amount")) or 0.0,
                    "pp_amount":                _flt_safe(row.get("pp_amount")) or 0.0,
                    "ref_amount":               _flt_safe(row.get("ref_amount")) or 0.0,
                    "br_amount":                _flt_safe(row.get("br_amount")) or 0.0,
                    "wh_amount":                _flt_safe(row.get("wh_amount")) or 0.0,
                    "other_amount":             _flt_safe(row.get("other_amount")) or 0.0,
                    "br_no_str":                _str_safe(row.get("br_no_str")),
                    "br_amount_str":            _str_safe(row.get("br_amount_str")),
                    "adjudication_date":        _parse_date(row.get("adjudication_date")) if row.get("adjudication_date") else None,
                    "os_category":              _str_safe(row.get("os_category")),
                    "online_os":                _str_safe(row.get("online_os")),
                    "online_adjn":              _str_safe(row.get("online_adjn")),
                    "entry_deleted":            None,
                    "deleted_by":               None,
                    "deleted_reason":           None,
                    "deleted_on":               None,
                    "os_printed":               _str_safe(row.get("os_printed")),
                    "bkup_taken":               _str_safe(row.get("bkup_taken")),
                    "dr_no":                    _str_safe(row.get("dr_no")),
                    "dr_year":                  _int_safe(row.get("dr_year")),
                    "total_drs":                _int_safe(row.get("total_drs")),
                    "previous_os_details":      _str_safe(row.get("previous_os_details")),
                    "seizure_date":             _parse_date(row.get("seizure_date")) if row.get("seizure_date") else None,
                    "supdt_remarks2":           _str_safe(row.get("supdt_remarks2")),
                    "unique_no":                _int_safe(row.get("unique_no")),
                    "pax_image_filename":       _str_safe(row.get("pax_image_filename")),
                })
                deleted_masters.discard(key)
                master_reactivated += 1
            else:
                master_skipped += 1
            continue

        m = CopsMaster(
            os_no=os_no,
            os_year=os_year,
            location_code=location_code,
            os_date=os_date_parsed,
            # Passenger
            pax_name=_str_safe(row.get("pax_name")),
            pax_name_modified_by_vig=_str_safe(row.get("pax_name_modified_by_vig")),
            pax_address1=_str_safe(row.get("pax_address1")),
            pax_address2=_str_safe(row.get("pax_address2")),
            pax_address3=_str_safe(row.get("pax_address3")),
            father_name=_str_safe(row.get("father_name")),
            pax_date_of_birth=_parse_date(row.get("pax_date_of_birth")) if row.get("pax_date_of_birth") else None,
            passport_no=_str_safe(row.get("passport_no")),
            passport_date=_parse_date(row.get("passport_date")) if row.get("passport_date") else None,
            pax_nationality=_str_safe(row.get("pax_nationality")),
            pax_status=_str_safe(row.get("pax_status")),
            residence_at=_str_safe(row.get("residence_at")),
            country_of_departure=_str_safe(row.get("country_of_departure")),
            date_of_departure=_str_safe(row.get("date_of_departure")),
            old_passport_no=_str_safe(row.get("old_passport_no")),
            previous_visits=_str_safe(row.get("previous_visits")),
            # Renamed columns
            stay_abroad_days=_int_safe(row.get("abroad_stay")),
            supdts_remarks=_str_safe(row.get("supdt_remarks1")),
            pp_issue_place=_str_safe(row.get("passport_issue_place")),
            port_of_dep_dest=_str_safe(row.get("port_of_departure")),
            br_no_num=_flt_safe(row.get("br_no")),
            br_date_str=_str_safe(row.get("br_date")),
            # Flight
            flight_no=_str_safe(row.get("flight_no")),
            flight_date=_parse_date(row.get("flight_date")) if row.get("flight_date") else None,
            # Officer
            adj_offr_name=_str_safe(row.get("adj_offr_name")),
            adj_offr_designation=_str_safe(row.get("adj_offr_designation")),
            adjn_offr_remarks=_str_safe(row.get("adjn_offr_remarks")),
            adjn_offr_remarks1=_str_safe(row.get("adjn_offr_remarks1")),
            booked_by=_str_safe(row.get("booked_by")),
            # Financials
            total_items=_int_safe(row.get("total_items")),
            total_items_value=_flt_safe(row.get("total_items_value")) or 0.0,
            total_fa_value=_flt_safe(row.get("total_fa_value")) or 0.0,
            total_duty_amount=_flt_safe(row.get("total_duty_amount")) or 0.0,
            total_payable=_flt_safe(row.get("total_payable")) or 0.0,
            dutiable_value=_flt_safe(row.get("dutiable_value")) or 0.0,
            redeemed_value=_flt_safe(row.get("redeemed_value")) or 0.0,
            re_export_value=_flt_safe(row.get("re_export_value")) or 0.0,
            confiscated_value=_flt_safe(row.get("confiscated_value")) or 0.0,
            rf_amount=_flt_safe(row.get("rf_amount")) or 0.0,
            pp_amount=_flt_safe(row.get("pp_amount")) or 0.0,
            ref_amount=_flt_safe(row.get("ref_amount")) or 0.0,
            br_amount=_flt_safe(row.get("br_amount")) or 0.0,
            wh_amount=_flt_safe(row.get("wh_amount")) or 0.0,
            other_amount=_flt_safe(row.get("other_amount")) or 0.0,
            br_no_str=_str_safe(row.get("br_no_str")),
            br_amount_str=_str_safe(row.get("br_amount_str")),
            # Status
            adjudication_date=_parse_date(row.get("adjudication_date")) if row.get("adjudication_date") else None,
            os_category=_str_safe(row.get("os_category")),
            online_os=_str_safe(row.get("online_os")),
            online_adjn=_str_safe(row.get("online_adjn")),
            entry_deleted=_str_safe(row.get("entry_deleted")),
            os_printed=_str_safe(row.get("os_printed")),
            bkup_taken=_str_safe(row.get("bkup_taken")),
            # DR linkage
            dr_no=_str_safe(row.get("dr_no")),
            dr_year=_int_safe(row.get("dr_year")),
            total_drs=_int_safe(row.get("total_drs")),
            # Misc
            previous_os_details=_str_safe(row.get("previous_os_details")),
            seizure_date=_parse_date(row.get("seizure_date")) if row.get("seizure_date") else None,
            supdt_remarks2=_str_safe(row.get("supdt_remarks2")),
            unique_no=_int_safe(row.get("unique_no")),
            pax_image_filename=_str_safe(row.get("pax_image_filename")),
            is_draft="N",
        )
        db.add(m)
        existing_masters.add(key)
        _master_date_cache[key] = m.os_date
        master_inserted += 1

    db.commit()

    # ── cops_master_deleted ────────────────────────────────────────────────────
    # Import deleted/seized records from the legacy deleted table.
    # These are stored as entry_deleted='Y' in cops_master.
    try:
        for row in _export_table(mdb_path, "cops_master_deleted"):
            os_no = (row.get("os_no") or "").strip()
            if not os_no:
                continue
            try:
                os_year = int(float(row.get("os_year") or 0))
            except (ValueError, TypeError):
                continue
            del_os_date_parsed = _parse_date(row.get("os_date"))
            os_year = _sanitize_year(os_year, del_os_date_parsed)
            if os_year is None:
                continue

            location_code = (row.get("location_code") or "").strip()
            key = (os_no, os_year, location_code)
            if key in existing_masters:
                deleted_skipped += 1
                continue

            m = CopsMaster(
                os_no=os_no,
                os_year=os_year,
                location_code=location_code,
                os_date=del_os_date_parsed,
                pax_name=_str_safe(row.get("pax_name")),
                pax_name_modified_by_vig=_str_safe(row.get("pax_name_modified_by_vig")),
                pax_address1=_str_safe(row.get("pax_address1")),
                pax_address2=_str_safe(row.get("pax_address2")),
                pax_address3=_str_safe(row.get("pax_address3")),
                father_name=_str_safe(row.get("father_name")),
                pax_date_of_birth=_parse_date(row.get("pax_date_of_birth")) if row.get("pax_date_of_birth") else None,
                passport_no=_str_safe(row.get("passport_no")),
                passport_date=_parse_date(row.get("passport_date")) if row.get("passport_date") else None,
                pax_nationality=_str_safe(row.get("pax_nationality")),
                pax_status=_str_safe(row.get("pax_status")),
                residence_at=_str_safe(row.get("residence_at")),
                country_of_departure=_str_safe(row.get("country_of_departure")),
                date_of_departure=_str_safe(row.get("date_of_departure")),
                stay_abroad_days=_int_safe(row.get("abroad_stay")),
                supdts_remarks=_str_safe(row.get("supdt_remarks1")),
                pp_issue_place=_str_safe(row.get("passport_issue_place")),
                port_of_dep_dest=_str_safe(row.get("port_of_departure")),
                br_no_num=_flt_safe(row.get("br_no")),
                br_date_str=_str_safe(row.get("br_date")),
                flight_no=_str_safe(row.get("flight_no")),
                flight_date=_parse_date(row.get("flight_date")) if row.get("flight_date") else None,
                adj_offr_name=_str_safe(row.get("adj_offr_name")),
                adj_offr_designation=_str_safe(row.get("adj_offr_designation")),
                adjn_offr_remarks=_str_safe(row.get("adjn_offr_remarks")),
                adjn_offr_remarks1=_str_safe(row.get("adjn_offr_remarks1")),
                booked_by=_str_safe(row.get("booked_by")),
                total_items=_int_safe(row.get("total_items")),
                total_items_value=_flt_safe(row.get("total_items_value")) or 0.0,
                total_fa_value=_flt_safe(row.get("total_fa_value")) or 0.0,
                total_duty_amount=_flt_safe(row.get("total_duty_amount")) or 0.0,
                total_payable=_flt_safe(row.get("total_payable")) or 0.0,
                dutiable_value=_flt_safe(row.get("dutiable_value")) or 0.0,
                redeemed_value=_flt_safe(row.get("redeemed_value")) or 0.0,
                re_export_value=_flt_safe(row.get("re_export_value")) or 0.0,
                confiscated_value=_flt_safe(row.get("confiscated_value")) or 0.0,
                rf_amount=_flt_safe(row.get("rf_amount")) or 0.0,
                pp_amount=_flt_safe(row.get("pp_amount")) or 0.0,
                ref_amount=_flt_safe(row.get("ref_amount")) or 0.0,
                br_amount=_flt_safe(row.get("br_amount")) or 0.0,
                wh_amount=_flt_safe(row.get("wh_amount")) or 0.0,
                other_amount=_flt_safe(row.get("other_amount")) or 0.0,
                br_no_str=_str_safe(row.get("br_no_str")),
                br_amount_str=_str_safe(row.get("br_amount_str")),
                adjudication_date=_parse_date(row.get("adjudication_date")) if row.get("adjudication_date") else None,
                os_category=_str_safe(row.get("os_category")),
                online_os=_str_safe(row.get("online_os")),
                online_adjn=_str_safe(row.get("online_adjn")),
                entry_deleted="Y",  # Mark as deleted
                os_printed=_str_safe(row.get("os_printed")),
                bkup_taken=_str_safe(row.get("bkup_taken")),
                dr_no=_str_safe(row.get("dr_no")),
                dr_year=_int_safe(row.get("dr_year")),
                total_drs=_int_safe(row.get("total_drs")),
                previous_os_details=_str_safe(row.get("previous_os_details")),
                seizure_date=_parse_date(row.get("seizure_date")) if row.get("seizure_date") else None,
                supdt_remarks2=_str_safe(row.get("supdt_remarks2")),
                unique_no=_int_safe(row.get("unique_no")),
                pax_image_filename=_str_safe(row.get("pax_image_filename")),
                is_draft="N",
            )
            db.add(m)
            existing_masters.add(key)
            deleted_inserted += 1

        db.commit()
    except Exception as e:
        db.rollback()
        # cops_master_deleted table may not exist in all MDB versions — that's OK
        logger.info("cops_master_deleted import skipped: %s", e)

    # ── cops_items ─────────────────────────────────────────────────────────────
    for row in _export_table(mdb_path, "cops_items"):
        os_no = (row.get("os_no") or "").strip()
        if not os_no:
            items_invalid += 1
            continue
        try:
            os_year = int(float(row.get("os_year") or 0))
        except (ValueError, TypeError):
            items_invalid += 1
            continue
        # Use item's own os_date as fallback; if missing, use the parent master's date
        item_os_date_for_year = _parse_date(row.get("os_date")) if row.get("os_date") else None
        if item_os_date_for_year is None:
            # peek into master cache with a temporary key (location_code not yet parsed)
            _loc_tmp = (row.get("location_code") or "").strip()
            item_os_date_for_year = _master_date_cache.get((os_no, os_year, _loc_tmp))
        os_year = _sanitize_year(os_year, item_os_date_for_year)
        if os_year is None:
            items_invalid += 1
            continue

        # Parse items_sno — blank/zero means legacy data without serial numbers.
        # Assign a per-case sequential counter to avoid key collisions.
        items_sno_raw = (row.get("items_sno") or "").strip()
        try:
            items_sno = int(float(items_sno_raw)) if items_sno_raw else 0
        except (ValueError, TypeError):
            items_sno = 0

        location_code = (row.get("location_code") or "").strip()
        case_key = (os_no, os_year, location_code)

        if items_sno == 0:
            # Assign next sequential sno for this case
            _case_sno_counter[case_key] = _case_sno_counter.get(case_key, 0) + 1
            items_sno = _case_sno_counter[case_key]

        key = (os_no, os_year, location_code, items_sno)
        if key in existing_items:
            items_skipped += 1
            continue

        item_date = _parse_date(row.get("os_date")) if row.get("os_date") else None
        if item_date is None:
            item_date = _master_date_cache.get((os_no, os_year, location_code))
        if item_date is None:
            item_date = _date.today()

        item = CopsItems(
            os_no=os_no,
            os_year=os_year,
            location_code=location_code,
            items_sno=items_sno,
            os_date=item_date,
            items_desc=_str_safe(row.get("items_desc")),
            items_qty=_flt_safe(row.get("items_qty")),
            items_uqc=_str_safe(row.get("items_uqc")),
            items_value=_flt_safe(row.get("items_value")) or 0.0,
            items_fa=_flt_safe(row.get("items_fa")) or 0.0,
            items_duty=_flt_safe(row.get("items_duty")) or 0.0,
            items_duty_type=_str_safe(row.get("items_duty_type")),
            items_category=_str_safe(row.get("items_category")),
            items_sub_category=_str_safe(row.get("items_sub_category")),
            items_release_category=_str_safe(row.get("items_release_category")),
            items_dr_no=_int_safe(row.get("items_dr_no")),
            items_dr_year=_int_safe(row.get("items_dr_year")),
            bkup_taken=_str_safe(row.get("bkup_taken")),
            unique_no=_int_safe(row.get("unique_no")),
        )
        db.add(item)
        existing_items.add(key)
        items_inserted += 1

    db.commit()

    post_import_optimise(db)

    return {
        "master_inserted":     master_inserted,
        "master_skipped":      master_skipped,
        "master_reactivated":  master_reactivated,
        "master_invalid":      master_invalid,
        "deleted_inserted":    deleted_inserted,
        "deleted_skipped":     deleted_skipped,
        "items_inserted":      items_inserted,
        "items_skipped":       items_skipped,
        "items_invalid":       items_invalid,
    }
