from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.baggage import BrMaster
from app.models.detention import DrMaster
from app.models.offence import CopsMaster

router = APIRouter()

@router.get("/search")
def universal_query(
    passport: Optional[str] = None,
    name: Optional[str] = None,
    flight: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Cross-references Passenger history across B.R., O.S., and D.R.
    Strictly follows legacy application logic: matching by Passport No, Partial Name, or Flight No.
    """
    
    br_results = []
    os_results = []
    dr_results = []
    
    # If no filters provided, return empty payload
    if not passport and not name and not flight:
        return {"br": [], "os": [], "dr": []}
    
    # --- Baggage Receipts Query ---
    br_query = db.query(BrMaster).filter(BrMaster.entry_deleted == "N")
    if passport:
        br_query = br_query.filter(BrMaster.passport_no == passport)
    if name:
        br_query = br_query.filter(BrMaster.pax_name.ilike(f"%{name}%"))
    if flight:
        br_query = br_query.filter(BrMaster.flight_no == flight)
        
    for br in br_query.order_by(BrMaster.br_date.desc()).limit(50).all():
        br_results.append({
            "br_no": f"{br.br_no}/{br.br_year}",
            "date": br.br_date.isoformat(),
            "amount": br.total_payable or 0.0,
            "status": "Printed" if br.br_printed == "Y" else "Open"
        })

    # --- Detention Receipts Query ---
    dr_query = db.query(DrMaster).filter(DrMaster.entry_deleted == "N")
    if passport:
        dr_query = dr_query.filter(DrMaster.passport_no == passport)
    if name:
        dr_query = dr_query.filter(DrMaster.pax_name.ilike(f"%{name}%"))
    if flight:
        dr_query = dr_query.filter(DrMaster.flight_no == flight)
        
    for dr in dr_query.order_by(DrMaster.dr_date.desc()).limit(50).all():
        dr_results.append({
            "dr_no": f"{dr.dr_no}/{dr.dr_year}",
            "date": dr.dr_date.isoformat(),
            "amount": dr.total_items_value or 0.0,
            "status": "Closed" if dr.closure_ind == "Y" else "Active"
        })

    # --- Offence Cases Query ---
    os_query = db.query(CopsMaster).filter(CopsMaster.entry_deleted == "N")
    if passport:
        os_query = os_query.filter(CopsMaster.passport_no == passport)
    if name:
        os_query = os_query.filter(CopsMaster.pax_name.ilike(f"%{name}%"))
    if flight:
        os_query = os_query.filter(CopsMaster.flight_no == flight)
        
    for os in os_query.order_by(CopsMaster.os_date.desc()).limit(50).all():
        os_results.append({
            "os_no": f"{os.os_no}/{os.os_year}",
            "date": os.os_date.isoformat(),
            "val": os.total_assessed_value or 0.0,
            "status": os.current_status or "Apprehended"
        })

    return {
        "br": br_results,
        "os": os_results,
        "dr": dr_results
    }
