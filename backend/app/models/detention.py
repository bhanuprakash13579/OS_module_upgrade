"""
Detention Receipt Models.
Tables: dr_master (33 cols), dr_items (16 cols)
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text
from app.database import Base


class DrMaster(Base):
    """
    Detention Receipts — Main. 33 columns.
    DR types: Bagg, AIU, MHB, Other
    """
    __tablename__ = "dr_master"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Identifiers ──
    dr_no = Column(Integer, nullable=False, index=True)
    dr_date = Column(Date, nullable=False, index=True)
    dr_year = Column(Integer)
    dr_type = Column(String(20), nullable=False)  # Bagg / AIU / MHB / Other

    # ── Passenger ──
    pax_name = Column(String(200))
    passport_no = Column(String(50), index=True)
    passport_date = Column(Date)
    pax_address1 = Column(String(300))
    pax_address2 = Column(String(300))
    pax_address3 = Column(String(300))

    # ── Travel ──
    port_of_departure = Column(String(200))
    flight_no = Column(String(20), index=True)
    flight_date = Column(Date)

    # ── Values ──
    total_items_value = Column(Float, default=0.0)

    # ── Closure ──
    closure_ind = Column(String(5))               # Y = closed, ' ' = open
    closure_remarks = Column(Text)
    closure_date = Column(Date)
    closed_batch_date = Column(Date)
    closed_batch_shift = Column(String(20))

    # ── Warehouse Link ──
    warehouse_no = Column(String(50))

    # ── Administrative ──
    entry_deleted = Column(String(5), default="N", index=True)
    unique_no = Column(Integer)
    location_code = Column(String(20))
    login_id = Column(String(50))

    # ── Detention Details ──
    detained_by = Column(String(200))
    detained_pkg_no = Column(String(50))
    detained_pkg_type = Column(String(50))
    seal_no = Column(String(50))
    dr_printed = Column(String(5), default="N")
    detention_reasons = Column(Text)

    # ── Seizure/OS Link ──
    seizure_date = Column(Date)
    os_no = Column(String(20))
    receipt_by_who = Column(String(200))


class DrItems(Base):
    """
    Detention Receipt Items. 16 columns.
    """
    __tablename__ = "dr_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    dr_no = Column(Integer, nullable=False, index=True)
    dr_date = Column(Date)
    dr_type = Column(String(20))

    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    items_value = Column(Float, default=0.0)
    items_fa = Column(Float, default=0.0)
    items_release_category = Column(String(50))

    receipt_by_who = Column(String(5))             # D=Duty Paid, Y=Handed Over
    item_closure_remarks = Column(Text)
    detained_pkg_no = Column(String(50))
    detained_pkg_type = Column(String(50))

    unique_no = Column(Integer)
    location_code = Column(String(20))
