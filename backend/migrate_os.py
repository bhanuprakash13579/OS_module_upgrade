import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('cops_br_database.db')
        cursor = conn.cursor()

        # Add columns to cops_master
        master_columns = [
            ("shift", "VARCHAR(20)"),
            ("detention_date", "DATE"),
            ("case_type", "VARCHAR(100)"),
            ("pp_issue_place", "VARCHAR(200)"),
            ("port_of_dep_dest", "VARCHAR(200)"),
            ("date_of_departure", "VARCHAR(50)"),
            ("stay_abroad_days", "INTEGER"),
            ("is_draft", "VARCHAR(5) DEFAULT 'N'")
        ]

        for col, col_type in master_columns:
            try:
                cursor.execute(f"ALTER TABLE cops_master ADD COLUMN {col} {col_type}")
                print(f"Added {col} to cops_master")
            except sqlite3.OperationalError as e:
                # Ignore duplicate column error
                if "duplicate column name" in str(e).lower():
                    print(f"Column {col} already exists in cops_master")
                else:
                    raise e
                    
        # Add columns to cops_items
        items_columns = [
            ("value_per_piece", "FLOAT DEFAULT 0.0"),
            ("cumulative_duty_rate", "FLOAT DEFAULT 0.0")
        ]

        for col, col_type in items_columns:
            try:
                cursor.execute(f"ALTER TABLE cops_items ADD COLUMN {col} {col_type}")
                print(f"Added {col} to cops_items")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"Column {col} already exists in cops_items")
                else:
                    raise e

        # Also need to widen flight_no from 20 to 50 if possible in sqlite, 
        # but SQLite doesn't strictly enforce VARCHAR length, so it's fine.

        conn.commit()
        conn.close()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
