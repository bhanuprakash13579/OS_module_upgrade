import os
import sys
import subprocess
import csv
import io
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Hardcoded extracted passwords from legacy application
KNOWN_PASSWORDS = [
    "brchn0312",
    "brmdu0113",
    "export0512",
    "locip6",
    "oswhchk",
    "sezare108"
]

# Legacy to Modern Column Mapping
TABLE_MAPPINGS = {
    "br_master": {
        "br_no": "receipt_no",
        "br_date": "date",
        "br_type": "receipt_type",
        "flight_no": "flight_number",
        "pax_name": "passenger_name",
        "passport_no": "passport_number",
        "total_duty_amount": "total_duty",
        "br_amount": "total_amount",
        "bkup_taken": "synced"
    },
    "cops_master": {
        "os_no": "offence_no",
        "os_date": "date",
        "total_duty_amount": "total_duty",
        "adjudication_date": "adjudication_date",
        "bkup_taken": "synced"
    }
}

def check_mdbtools_installed() -> bool:
    """Check if mdbtools is installed on the system."""
    try:
        subprocess.run(["mdb-export", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def get_tables(mdb_path: str, password: str) -> List[str]:
    """Get all tables from the MDB file."""
    cmd = ["mdb-tables", "-p", password, mdb_path]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        # mdb-tables outputs space-separated table names by default, but we can standard split
        tables = result.stdout.strip().split()
        return tables
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to read tables from {mdb_path} with provided password.")
        logger.error(e.stderr)
        return []

def extract_table_data(mdb_path: str, table_name: str, password: str) -> List[Dict[str, Any]]:
    """Extract all rows from a single table as a list of dictionaries."""
    cmd = ["mdb-export", "-d", ",", "-R", "\n", "-p", password, mdb_path, table_name]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        # Read the CSV output from mdb-export
        csv_data = result.stdout
        if not csv_data.strip():
            return []
            
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        logger.info(f"Extracted {len(rows)} rows from table '{table_name}'")
        return rows
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract table {table_name} from {mdb_path}")
        logger.error(e.stderr)
        return []

def unlock_and_validate_mdb(mdb_path: str) -> str:
    """Try all known passwords to unlock the database and return the successful password."""
    logger.info(f"Attempting to unlock legacy database: {mdb_path}")
    for pwd in KNOWN_PASSWORDS:
        tables = get_tables(mdb_path, pwd)
        if tables:
            logger.info(f"Successfully unlocked {mdb_path} using extracted password.")
            return pwd
    logger.error("Failed to unlock database with any known legacy password.")
    return ""

def migrate_database(mdb_path: str):
    """Main migration coordinator for a single MDB file."""
    if not os.path.exists(mdb_path):
        logger.error(f"Database file not found: {mdb_path}")
        return

    password = unlock_and_validate_mdb(mdb_path)
    if not password:
        return

    tables = get_tables(mdb_path, password)
    logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")

    # For each table, extract data and (eventually) insert into PostgreSQL/SQLite
    for table in tables:
        logger.info(f"Processing table: {table}")
        data = extract_table_data(mdb_path, table, password)
        if data:
            if table in TABLE_MAPPINGS:
                logger.info(f"Applying schema mapping for {table}...")
                mapping = TABLE_MAPPINGS[table]
                mapped_data = []
                for row in data:
                    new_row = {mapping.get(k, k.lower()): v for k, v in row.items()}
                    mapped_data.append(new_row)
                logger.info(f"Successfully mapped {len(mapped_data)} records for '{table}' ready for DB insertion.")
            else:
                logger.info(f"No specific mapping defined for {table}, importing raw.")

def main():
    if not check_mdbtools_installed():
        logger.error("mdbtools is not installed. Please run: sudo apt-get install mdbtools")
        sys.exit(1)

    if len(sys.argv) < 2:
        logger.info("Usage: python migrate_mdb.py <path_to_legacy_mdb_file>")
        sys.exit(1)

    mdb_file = sys.argv[1]
    migrate_database(mdb_file)

if __name__ == "__main__":
    main()
