from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func, and_, cast, Integer
from collections import defaultdict
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.database import get_db
from app.models.offence import CopsMaster, CopsItems
from app.services.auth import get_current_user
from app.models.auth import User

router = APIRouter(prefix="/api/os-query", tags=["OS Query"])

# ── Schemas ──

class OSQueryRequest(BaseModel):
    # Core identifiers
    os_no: Optional[str] = None
    os_year: Optional[int] = None
    dr_no: Optional[str] = None
    dr_year: Optional[int] = None
    
    # Dates
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    
    # Passenger info
    pax_name: Optional[str] = None
    passport_no: Optional[str] = None
    flight_no: Optional[str] = None
    
    # Flight/Route
    port_of_dep_dest: Optional[str] = None
    country_of_departure: Optional[str] = None
    
    # Values
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Goods
    item_desc: Optional[str] = None
    
    # Pagination
    page: int = 1
    limit: int = 100

class OSQueryItemResponse(BaseModel):
    items_sno: int
    items_desc: Optional[str]
    items_qty: float
    items_uqc: Optional[str]
    items_value: float
    items_fa: float = 0.0                   # Free Allowance (value-mode)
    items_fa_type: str = 'value'            # 'value' | 'qty' — critical for FA calculation
    items_fa_qty: Optional[float] = None    # FA quantity (qty-mode)
    items_fa_uqc: Optional[str] = None      # FA unit (qty-mode)
    items_duty_type: Optional[str]
    items_release_category: Optional[str] = None   # CONFS/RF/REF — needed for print confiscation calc
    value_per_piece: float = 0.0
    cumulative_duty_rate: float = 0.0

    class Config:
        from_attributes = True

class OSQueryResponse(BaseModel):
    os_no: str
    os_year: int
    os_date: date
    pax_name: Optional[str]
    passport_no: Optional[str]
    flight_no: Optional[str]
    flight_date: Optional[date]
    total_items_value: float
    total_duty_amount: float
    total_payable: float
    adjudication_date: Optional[date]
    is_draft: str
    
    # OSPrintView Extended Fields
    booked_by: Optional[str] = None            # Used in OS No. display (e.g. "AIU 12/2026")
    os_printed: str = "N"                      # Print-lock flag read by handlePrint()
    shift: Optional[str] = None
    detention_date: Optional[date] = None
    father_name: Optional[str] = None
    pax_address1: Optional[str] = None
    pax_address2: Optional[str] = None
    pax_address3: Optional[str] = None
    passport_date: Optional[date] = None
    port_of_dep_dest: Optional[str] = None
    country_of_departure: Optional[str] = None
    pax_nationality: Optional[str] = None
    nationality: Optional[str] = None
    date_of_departure: Optional[str] = None
    stay_abroad_days: Optional[int] = None
    residence_at: Optional[str] = None
    previous_visits: Optional[str] = None
    confiscated_value: float = 0.0
    redeemed_value: float = 0.0
    re_export_value: float = 0.0
    rf_amount: float = 0.0
    ref_amount: float = 0.0
    pp_amount: float = 0.0
    supdts_remarks: Optional[str] = None
    adjn_offr_remarks: Optional[str] = None
    adj_offr_name: Optional[str] = None
    adj_offr_designation: Optional[str] = None

    items: List[OSQueryItemResponse] = []

    class Config:
        from_attributes = True

class OSQueryPaginatedResponse(BaseModel):
    items: List[OSQueryResponse]
    total_count: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ── Endpoints ──

@router.post("/search", response_model=OSQueryPaginatedResponse)
def search_os_cases(
    query: OSQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query Offence/Seizure records based on dynamic filters.
    Requires SDO, DC, AC, or Admin roles.
    """
    
    # Start with base query — always exclude soft-deleted master records
    if query.item_desc:
        q = db.query(CopsMaster).join(
            CopsItems, 
            and_(CopsMaster.os_no == CopsItems.os_no, CopsMaster.os_year == CopsItems.os_year)
        )
    else:
        q = db.query(CopsMaster)

    # Always exclude soft-deleted cases
    q = q.filter(or_(CopsMaster.entry_deleted == None, CopsMaster.entry_deleted != "Y"))

    # ── Identifiers ──
    if query.os_no:
        q = q.filter(CopsMaster.os_no == query.os_no)
    if query.os_year:
        q = q.filter(CopsMaster.os_year == query.os_year)
    if query.dr_no:
        q = q.filter(CopsMaster.dr_no == query.dr_no)
    if query.dr_year:
        q = q.filter(CopsMaster.dr_year == query.dr_year)

    # ── Dates ──
    if query.from_date:
        q = q.filter(CopsMaster.os_date >= query.from_date)
    if query.to_date:
        q = q.filter(CopsMaster.os_date <= query.to_date)

    # ── Passenger Info ──
    if query.pax_name:
        q = q.filter(CopsMaster.pax_name.ilike(f"%{query.pax_name}%"))
        
    if query.passport_no:
        # Check both current passport and legacy/old passport fields
        pno = query.passport_no
        q = q.filter(
            or_(
                CopsMaster.passport_no.ilike(f"%{pno}%"),
                CopsMaster.old_passport_no.ilike(f"%{pno}%")
            )
        )
        
    if query.flight_no:
        q = q.filter(CopsMaster.flight_no.ilike(f"%{query.flight_no}%"))

    # ── Route Info ──
    if query.port_of_dep_dest:
        q = q.filter(CopsMaster.port_of_dep_dest.ilike(f"%{query.port_of_dep_dest}%"))
        
    # Arrived From / Country of departure
    if query.country_of_departure:
        q = q.filter(CopsMaster.country_of_departure.ilike(f"%{query.country_of_departure}%"))

    # ── Values ──
    if query.min_value is not None:
        q = q.filter(CopsMaster.total_items_value >= query.min_value)
    if query.max_value is not None:
        q = q.filter(CopsMaster.total_items_value <= query.max_value)

    # ── Goods ──
    if query.item_desc:
        q = q.filter(CopsItems.items_desc.ilike(f"%{query.item_desc}%"))

    # To avoid duplicates if searching by item description
    if query.item_desc:
        q = q.distinct()

    # Order by newest first
    q = q.order_by(desc(CopsMaster.os_year), desc(CopsMaster.os_no))
    
    # Pagination calculations
    total_count = q.count()
    limit = max(1, min(query.limit, 500))  # Cap page size at 500
    page = max(1, query.page)
    total_pages = (total_count + limit - 1) // limit
    
    # Fetch current page
    offset = (page - 1) * limit
    results = q.offset(offset).limit(limit).all()

    # Bulk-load items for all results in ONE query (eliminates N+1)
    items_map: dict = defaultdict(list)
    if results:
        keys = list({(r.os_no, r.os_year) for r in results})
        pair_filter = or_(*[and_(CopsItems.os_no == no, CopsItems.os_year == yr) for no, yr in keys])
        all_items = db.query(CopsItems).filter(
            pair_filter,
            or_(CopsItems.entry_deleted == None, CopsItems.entry_deleted != "Y")
        ).order_by(CopsItems.os_no, CopsItems.os_year, CopsItems.items_sno).all()
        for item in all_items:
            items_map[(item.os_no, item.os_year)].append(item)

    response_data = []
    for case in results:
        items = items_map.get((case.os_no, case.os_year), [])

        case_dict = {
            "os_no": case.os_no,
            "os_year": case.os_year,
            "os_date": case.os_date,
            "pax_name": case.pax_name,
            "father_name": case.father_name,
            "passport_no": case.passport_no,
            "flight_no": case.flight_no,
            "flight_date": case.flight_date,
            "total_items_value": case.total_items_value or 0.0,
            "total_duty_amount": case.total_duty_amount or 0.0,
            "total_payable": case.total_payable or 0.0,
            "adjudication_date": case.adjudication_date,
            "is_draft": case.is_draft,
            "booked_by": case.booked_by,
            "os_printed": case.os_printed or "N",
            "shift": case.shift,
            "detention_date": case.detention_date,
            "pax_address1": case.pax_address1,
            "pax_address2": case.pax_address2,
            "pax_address3": case.pax_address3,
            "passport_date": case.passport_date,
            "port_of_dep_dest": case.port_of_dep_dest,
            "country_of_departure": case.country_of_departure,
            "pax_nationality": case.pax_nationality,
            "nationality": case.nationality,
            "date_of_departure": case.date_of_departure,
            "stay_abroad_days": case.stay_abroad_days,
            "residence_at": case.residence_at,
            "previous_visits": case.previous_visits,
            "confiscated_value": case.confiscated_value or 0.0,
            "redeemed_value": case.redeemed_value or 0.0,
            "re_export_value": case.re_export_value or 0.0,
            "rf_amount": case.rf_amount or 0.0,
            "ref_amount": case.ref_amount or 0.0,
            "pp_amount": case.pp_amount or 0.0,
            "supdts_remarks": (" ".join(filter(bool, [case.supdts_remarks, case.supdt_remarks2]))).strip() or None,
            "adjn_offr_remarks": (" ".join(filter(bool, [case.adjn_offr_remarks, case.adjn_offr_remarks1]))).strip() or None,
            "adj_offr_name": case.adj_offr_name,
            "adj_offr_designation": case.adj_offr_designation,
            "items": [
                {
                    "items_sno": i.items_sno,
                    "items_desc": i.items_desc,
                    "items_qty": i.items_qty or 0.0,
                    "items_uqc": i.items_uqc,
                    "items_value": i.items_value or 0.0,
                    "items_fa": i.items_fa or 0.0,
                    "items_fa_type": i.items_fa_type or 'value',
                    "items_fa_qty": i.items_fa_qty,
                    "items_fa_uqc": i.items_fa_uqc,
                    "items_release_category": i.items_release_category,
                    "items_duty_type": i.items_duty_type,
                    "value_per_piece": i.value_per_piece or 0.0,
                    "cumulative_duty_rate": i.cumulative_duty_rate or 0.0,
                } for i in items
            ]
        }
        
        response_data.append(OSQueryResponse.model_validate(case_dict))
        
    return OSQueryPaginatedResponse(
        items=response_data,
        total_count=total_count,
        page=page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

