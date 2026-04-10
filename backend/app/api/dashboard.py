from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date

from app.database import get_db
from app.models.baggage import BrMaster
from app.models.detention import DrMaster
from app.models.offence import CopsMaster
from app.models.auth import User
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    Aggregates realtime metrics for the application Dashboard.
    Uses SQL aggregation — no full-table loads into Python memory.
    """
    today = date.today()

    # 1. BR stats today — one aggregation query
    br_stats = db.query(
        func.count(BrMaster.id).label("count"),
        func.coalesce(func.sum(BrMaster.total_payable), 0).label("revenue"),
    ).filter(BrMaster.br_date == today, BrMaster.entry_deleted != 'Y').one()
    br_count   = br_stats.count
    br_revenue = float(br_stats.revenue)

    # 2. OS stats today — single query with conditional aggregation (was two queries)
    os_stats = db.query(
        func.count(CopsMaster.id).label("total"),
        func.sum(case(
            (
                CopsMaster.adjudication_date.is_(None) &
                CopsMaster.adj_offr_name.is_(None),
                1
            ),
            else_=0
        )).label("pending"),
    ).filter(
        CopsMaster.os_date == today,
        CopsMaster.entry_deleted != 'Y',
    ).one()
    os_count   = os_stats.total   or 0
    os_pending = int(os_stats.pending or 0)

    # 3. DR active today — one count query
    dr_active = db.query(func.count(DrMaster.id)).filter(
        DrMaster.dr_date == today,
        DrMaster.entry_deleted != 'Y',
        DrMaster.closure_ind != 'Y',
    ).scalar() or 0

    # 4. Recent transactions — fetch only the few rows needed
    recent_brs = db.query(BrMaster).filter(
        BrMaster.br_date == today, BrMaster.entry_deleted != 'Y'
    ).order_by(BrMaster.id.desc()).limit(2).all()

    recent_os = db.query(CopsMaster).filter(
        CopsMaster.os_date == today, CopsMaster.entry_deleted != 'Y'
    ).order_by(CopsMaster.id.desc()).limit(2).all()

    recent_drs = db.query(DrMaster).filter(
        DrMaster.dr_date == today, DrMaster.entry_deleted != 'Y'
    ).order_by(DrMaster.id.desc()).limit(1).all()

    recent = []
    for br in recent_brs:
        recent.append({"type": "BR", "number": f"{br.br_no}/{br.br_year}", "details": f"{br.pax_name} / {br.flight_no}", "amount": f"₹ {br.total_payable}", "status": "Paid" if br.br_printed == 'Y' else "Pending"})
    for os in recent_os:
        # Status check must match _pending_filters() in offence.py — a case
        # is adjudicated if EITHER adjudication_date or adj_offr_name is set.
        _os_status = 'Adjudicated' if (os.adjudication_date or os.adj_offr_name) else ('Quashed' if os.quashed == 'Y' else ('Rejected' if os.rejected == 'Y' else 'Pending'))
        recent.append({"type": "OS", "number": f"{os.os_no}/{os.os_year}", "details": f"{os.pax_name} / {os.flight_no}", "amount": f"₹ {os.total_items_value}", "status": _os_status})
    for dr in recent_drs:
        recent.append({"type": "DR", "number": f"{dr.dr_no}/{dr.dr_year}", "details": f"{dr.pax_name} / {dr.flight_no}", "amount": "-", "status": "Warehoused" if dr.closure_ind != 'Y' else "Closed"})

    return {
        "br_revenue": br_revenue,
        "br_count": br_count,
        "os_count": os_count,
        "os_pending": os_pending,
        "dr_active": dr_active,
        "duty_collections": br_revenue,
        "recent_transactions": recent,
    }
