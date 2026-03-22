from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from datetime import date
import csv
from io import StringIO
from typing import Optional

from app.database import get_db
from app.models.baggage import BrMaster
from app.models.detention import DrMaster
from app.models.offence import CopsMaster

router = APIRouter()

@router.get("/generate")
def generate_report(
    report_id: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    Generates CSV Reports for B.R., O.S., and D.R. Registers.
    """
    output = StringIO()
    writer = csv.writer(output)

    # Hard safety ceiling — prevents loading the entire DB into memory for
    # an accidentally wide date range. 50 000 rows is ~5 years of daily ops.
    ROW_LIMIT = 50_000

    if report_id == "r4":  # B.R. Register
        writer.writerow(["BR No", "Date", "Passenger Name", "Passport No", "Flight", "Total Assessed", "Total Payable", "Receipt No", "Status"])
        records = db.query(BrMaster).filter(BrMaster.br_date >= start_date, BrMaster.br_date <= end_date, BrMaster.entry_deleted == "N").limit(ROW_LIMIT).all()
        for r in records:
            writer.writerow([
                f"{r.br_no}/{r.br_year}", r.br_date, r.pax_name, r.passport_no, r.flight_no,
                r.total_items_value, r.total_payable, r.challan_no or '', "Printed" if r.br_printed == "Y" else "Open"
            ])
        filename = f"BR_Register_{start_date}_to_{end_date}.csv"

    elif report_id == "r5":  # O.S. Register
        writer.writerow(["OS No", "Date", "Passenger Name", "Passport No", "Flight", "Assessed Value", "Status"])
        records = db.query(CopsMaster).filter(CopsMaster.os_date >= start_date, CopsMaster.os_date <= end_date, CopsMaster.entry_deleted == "N").limit(ROW_LIMIT).all()
        for r in records:
            _status = 'Adjudicated' if r.adjudication_date else ('Quashed' if r.quashed == 'Y' else ('Rejected' if r.rejected == 'Y' else 'Pending'))
            writer.writerow([
                f"{r.os_no}/{r.os_year}", r.os_date, r.pax_name, r.passport_no, r.flight_no,
                r.total_items_value, _status
            ])
        filename = f"OS_Register_{start_date}_to_{end_date}.csv"

    elif report_id == "r6":  # D.R. Register
        writer.writerow(["DR No", "Date", "Passenger Name", "Passport No", "Flight", "Items Value", "Status"])
        records = db.query(DrMaster).filter(DrMaster.dr_date >= start_date, DrMaster.dr_date <= end_date, DrMaster.entry_deleted == "N").limit(ROW_LIMIT).all()
        for r in records:
            writer.writerow([
                f"{r.dr_no}/{r.dr_year}", r.dr_date, r.pax_name, r.passport_no, r.flight_no,
                r.total_items_value, "Closed" if r.closure_ind == "Y" else "Active"
            ])
        filename = f"DR_Register_{start_date}_to_{end_date}.csv"

    else:
        # Default placeholder for unimplemented reports
        writer.writerow(["Report ID", "Start Date", "End Date", "Message"])
        writer.writerow([report_id, start_date, end_date, "This report is pending full data migration mapping."])
        filename = f"Report_{report_id}_{start_date}.csv"

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
