"""
Appeal Models.
Tables: appeal_master, appeal_items
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text
from app.database import Base


class AppealMaster(Base):
    """
    Appeal Master — same structure as cops_master + appeal-specific fields.
    Only for online O.S. cases (online_adjn='Y').
    """
    __tablename__ = "appeal_master"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── O.S. Reference ──
    os_no = Column(String(20), nullable=False, index=True)
    os_date = Column(Date, nullable=False)
    os_year = Column(Integer)
    location_code = Column(String(20))

    # ── Passenger ──
    pax_name = Column(String(200))
    pax_nationality = Column(String(100))
    passport_no = Column(String(50), index=True)
    passport_date = Column(Date)
    pax_address1 = Column(String(300))
    pax_address2 = Column(String(300))
    pax_address3 = Column(String(300))
    pax_date_of_birth = Column(Date)
    pax_status = Column(String(50))
    residence_at = Column(String(200))
    country_of_departure = Column(String(200))

    # ── Flight ──
    flight_no = Column(String(20))
    flight_date = Column(Date)

    # ── Values ──
    total_items = Column(Integer, default=0)
    total_items_value = Column(Float, default=0.0)
    dutiable_value = Column(Float, default=0.0)
    redeemed_value = Column(Float, default=0.0)
    re_export_value = Column(Float, default=0.0)
    confiscated_value = Column(Float, default=0.0)
    total_duty_amount = Column(Float, default=0.0)
    rf_amount = Column(Float, default=0.0)
    pp_amount = Column(Float, default=0.0)
    ref_amount = Column(Float, default=0.0)
    br_amount = Column(Float, default=0.0)
    total_payable = Column(Float, default=0.0)

    # ── Adjudication ──
    online_adjn = Column(String(5))           # Y/N
    adjudication_date = Column(Date)
    adj_offr_name = Column(String(200))
    adj_offr_designation = Column(String(200))
    adjn_offr_remarks = Column(Text)

    # ── Status ──
    unique_no = Column(Integer)
    entry_deleted = Column(String(5), default="N")
    bkup_taken = Column(String(5), default="N")


class AppealItems(Base):
    """Appeal Items."""
    __tablename__ = "appeal_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    os_no = Column(String(20), nullable=False, index=True)
    os_date = Column(Date)
    dr_no = Column(Integer)

    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    items_value = Column(Float, default=0.0)
    items_fa = Column(Float, default=0.0)
    items_duty = Column(Float, default=0.0)
    items_duty_type = Column(String(50))
    items_category = Column(String(50))

    unique_no = Column(Integer)
    location_code = Column(String(20))
