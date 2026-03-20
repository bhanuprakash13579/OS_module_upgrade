import os
import sys
import subprocess
import sqlite3
import pandas as pd
from datetime import datetime
from pydantic import ValidationError

sys.path.append('/home/bhanu/Desktop/OS_module_upgrade/backend')
from app.database import SessionLocal, engine
from app.models.offence import CopsMaster, CopsItems, OsMaster, ItemTrans
from app.models.auth import User  # Needed so tables trigger create

MDB_FILE = "/home/bhanu/Documents/os_db_3/cops_br_database.mdb"

def export_table_to_df(table_name):
    print(f"Exporting {table_name} from MDB...")
    csv_data = subprocess.check_output(['mdb-export', MDB_FILE, table_name]).decode('utf-8')
    # Save temp csv to load with pandas to handle quoting correctly
    with open(f"/tmp/{table_name}.csv", "w") as f:
        f.write(csv_data)
    return pd.read_csv(f"/tmp/{table_name}.csv", dtype=str)

def clean_date(date_str):
    if pd.isna(date_str) or not str(date_str).strip() or str(date_str).strip().lower() == 'na':
        return None
    try:
        # Access dates usually export as MM/DD/YY HH:MM:SS or similar
        return datetime.strptime(str(date_str).split(' ')[0], '%m/%d/%y').date()
    except:
        try:
            return datetime.strptime(str(date_str).split(' ')[0], '%d/%m/%Y').date()
        except:
            return None

def clean_float(val):
    if pd.isna(val) or not str(val).strip():
        return 0.0
    try:
        return float(str(val).replace(',', '').strip())
    except:
        return 0.0

def clean_int(val):
    if pd.isna(val) or not str(val).strip():
        return 0
    try:
        return int(float(str(val).replace(',', '').strip()))
    except:
        return 0

def run_migration():
    print("Connecting to SQLite...")
    db = SessionLocal()
    
    print("Wiping existing OS data (Keep Users & Masters intact)...")
    db.query(CopsItems).delete()
    db.query(CopsMaster).delete()
    db.query(OsMaster).delete()
    db.query(ItemTrans).delete()
    db.commit()

    # Load data
    df_master = export_table_to_df("cops_master")
    df_items = export_table_to_df("cops_items")

    print(f"Loaded {len(df_master)} master records and {len(df_items)} item records.")

    # Dedup master based on location_code, os_year, os_no
    # The legacy DB has massive duplication, we keep the first one
    df_master = df_master.drop_duplicates(subset=['location_code', 'os_year', 'os_no'])
    print(f"After master dedup: {len(df_master)} records.")

    df_items = df_items.drop_duplicates(subset=['location_code', 'os_year', 'os_no', 'items_sno'])
    print(f"After items dedup: {len(df_items)} records.")

    print("Inserting OS Masters...")
    inserted_masters = 0
    for _, row in df_master.iterrows():
        try:
            master = CopsMaster(
                os_no=str(row.get('os_no', '')),
                os_date=clean_date(row.get('os_date')) or datetime.now().date(),
                os_year=clean_int(row.get('os_year')),
                location_code=str(row.get('location_code', '')),
                booked_by=str(row.get('booked_by', '')) if not pd.isna(row.get('booked_by')) else '',
                pax_name=str(row.get('pax_name', '')) if not pd.isna(row.get('pax_name')) else '',
                passport_no=str(row.get('passport_no', '')) if not pd.isna(row.get('passport_no')) else '',
                passport_date=clean_date(row.get('passport_date')),
                flight_no=str(row.get('flight_no', '')) if not pd.isna(row.get('flight_no')) else '',
                flight_date=clean_date(row.get('flight_date')),
                total_items=clean_int(row.get('total_items')),
                total_items_value=clean_float(row.get('total_items_value')),
                total_fa_value=clean_float(row.get('total_fa_value')),
                total_duty_amount=clean_float(row.get('total_duty_amount')),
                total_payable=clean_float(row.get('total_payable')),
                entry_deleted=str(row.get('entry_deleted', 'N')) if not pd.isna(row.get('entry_deleted')) else 'N',
                pax_address1=str(row.get('pax_address1', '')) if not pd.isna(row.get('pax_address1')) else '',
                pax_address2=str(row.get('pax_address2', '')) if not pd.isna(row.get('pax_address2')) else '',
                pax_address3=str(row.get('pax_address3', '')) if not pd.isna(row.get('pax_address3')) else '',
                country_of_departure=str(row.get('country_of_departure', '')) if not pd.isna(row.get('country_of_departure')) else '',
                port_of_dep_dest=str(row.get('port_of_departure', '')) if not pd.isna(row.get('port_of_departure')) else '',
                previous_visits=str(row.get('previous_visits', '')) if not pd.isna(row.get('previous_visits')) else '',
                stay_abroad_days=clean_int(row.get('abroad_stay')),
                pax_status=str(row.get('pax_status', '')) if not pd.isna(row.get('pax_status')) else '',
                residence_at=str(row.get('residence_at', '')) if not pd.isna(row.get('residence_at')) else '',
                nationality=str(row.get('nationality', '')) if not pd.isna(row.get('nationality')) else '',
                pax_nationality=str(row.get('pax_nationality', '')) if not pd.isna(row.get('pax_nationality')) else '',
                dr_no=str(row.get('dr_no', '')) if not pd.isna(row.get('dr_no')) else '',
                dr_year=clean_int(row.get('dr_year')),
                rf_amount=clean_float(row.get('rf_amount')),
                pp_amount=clean_float(row.get('pp_amount')),
                ref_amount=clean_float(row.get('ref_amount')),
                confiscated_value=clean_float(row.get('confiscated_value')),
                redeemed_value=clean_float(row.get('redeemed_value')),
                dutiable_value=clean_float(row.get('dutiable_value')),
                re_export_value=clean_float(row.get('re_export_value')),
                adj_offr_name=str(row.get('adj_offr_name', '')) if not pd.isna(row.get('adj_offr_name')) else '',
                adj_offr_designation=str(row.get('adj_offr_designation', '')) if not pd.isna(row.get('adj_offr_designation')) else '',
                adjn_offr_remarks=str(row.get('adjn_offr_remarks', '')) if not pd.isna(row.get('adjn_offr_remarks')) else '',
                supdts_remarks=str(row.get('supdt_remarks1', '')) if not pd.isna(row.get('supdt_remarks1')) else '',
                os_printed=str(row.get('os_printed', 'N')) if not pd.isna(row.get('os_printed')) else 'N',
                online_os=str(row.get('online_os', 'N')) if not pd.isna(row.get('online_os')) else 'N',
                online_adjn=str(row.get('online_adjn', 'N')) if not pd.isna(row.get('online_adjn')) else 'N',
                closure_ind=str(row.get('closure_ind', '')) if not pd.isna(row.get('closure_ind')) else '',
                is_draft="N"
            )
            db.add(master)
            inserted_masters += 1
        except Exception as e:
            print(f"Error on master OS {row.get('os_no')}: {e}")

    db.commit()
    print(f"Inserted {inserted_masters} masters successfully.")

    print("Inserting OS Items...")
    inserted_items = 0
    for _, row in df_items.iterrows():
        try:
            qty = clean_float(row.get('items_qty'))
            total_val = clean_float(row.get('items_value'))
            
            # The user noted: legacy DB stored total value in items_value. 
            # We now need value_per_piece = total_val / qty
            per_piece = 0.0
            if qty > 0:
                per_piece = round(total_val / qty, 2)
            else:
                per_piece = total_val
                
            item = CopsItems(
                os_no=str(row.get('os_no', '')),
                os_date=clean_date(row.get('os_date')) or datetime.now().date(),
                os_year=clean_int(row.get('os_year')),
                location_code=str(row.get('location_code', '')),
                items_sno=clean_int(row.get('items_sno')),
                items_desc=str(row.get('items_desc', '')) if not pd.isna(row.get('items_desc')) else '',
                items_qty=qty,
                items_uqc=str(row.get('items_uqc', '')) if not pd.isna(row.get('items_uqc')) else '',
                items_value=total_val,  # Backend schema expects total here
                value_per_piece=per_piece,  # Computed from total
                items_fa=clean_float(row.get('items_fa')),
                items_duty=clean_float(row.get('items_duty')),
                items_duty_type=str(row.get('items_duty_type', '')) if not pd.isna(row.get('items_duty_type')) else '',
                items_category=str(row.get('items_category', '')) if not pd.isna(row.get('items_category')) else '',
                items_release_category=str(row.get('items_release_category', '')) if not pd.isna(row.get('items_release_category')) else '',
                items_sub_category=str(row.get('items_sub_category', '')) if not pd.isna(row.get('items_sub_category')) else '',
                entry_deleted=str(row.get('entry_deleted', 'N')) if not pd.isna(row.get('entry_deleted')) else 'N'
            )
            db.add(item)
            inserted_items += 1
        except Exception as e:
            print(f"Error on item {row.get('items_sno')} of OS {row.get('os_no')}: {e}")

    db.commit()
    print(f"Inserted {inserted_items} items successfully.")

    print("Migration complete!")
    db.close()

if __name__ == "__main__":
    run_migration()
