"""
Baggage Receipt Models — br_master (55 columns) + br_items (30 columns).
This is the largest and most critical transactional module.
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text
from app.database import Base


class BrMaster(Base):
    """
    Baggage Receipts — Main table.
    55 columns exactly matching legacy schema.
    BR types: Bagg, OS, OOS, SDO, Gold, Silv, Fuel, TR
    """
    __tablename__ = "br_master"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Core Identifiers ──
    br_no = Column(Integer, nullable=False, index=True)
    br_date = Column(Date, nullable=False, index=True)
    br_type = Column(String(20), nullable=False, index=True)  # Bagg/OS/OOS/SDO/Gold/Silv/Fuel/TR
    br_year = Column(Integer)
    br_shift = Column(String(20))  # Day / Night

    # ── Flight Details ──
    flight_no = Column(String(20), index=True)
    flight_date = Column(Date)

    # ── Passenger Details ──
    pax_name = Column(String(200))
    pax_nationality = Column(String(100))
    passport_no = Column(String(50), index=True)
    passport_date = Column(Date)
    passport_issue_place = Column(String(200))
    pax_address1 = Column(String(300))
    pax_address2 = Column(String(300))
    pax_address3 = Column(String(300))
    pax_date_of_birth = Column(Date)
    pax_status = Column(String(50))
    residence_at = Column(String(200))
    country_of_departure = Column(String(200))
    departure_date = Column(Date)

    # ── Linked Records ──
    os_no = Column(String(20))
    os_date = Column(Date)
    dr_no = Column(String(20))
    dr_date = Column(Date)

    # ── Financial: Values ──
    total_items_value = Column(Float, default=0.0)
    total_fa_value = Column(Float, default=0.0)
    total_duty_amount = Column(Float, default=0.0)
    rf_amount = Column(Float, default=0.0)       # Redemption Fine
    pp_amount = Column(Float, default=0.0)       # Personal Penalty
    ref_amount = Column(Float, default=0.0)      # Refund
    wh_amount = Column(Float, default=0.0)       # Warehouse charges
    other_amount = Column(Float, default=0.0)
    br_amount = Column(Float, default=0.0)       # Total payable

    # ── Bank & Batch ──
    challan_no = Column(String(50))
    bank_date = Column(Date)
    bank_shift = Column(String(20))
    batch_date = Column(Date, index=True)
    batch_shift = Column(String(20))

    # ── Administrative ──
    dc_code = Column(String(20))
    unique_no = Column(Integer)
    location_code = Column(String(20))
    login_id = Column(String(50))

    # ── Flags ──
    entry_deleted = Column(String(5), default="N", index=True)    # Y = soft-deleted
    bkup_taken = Column(String(5), default="N")       # Y = synced to server
    br_printed = Column(String(5), default="N")       # Y = locked
    ff_ind = Column(String(5))                         # Y = frequent flier

    # ── Extras ──
    image_filename = Column(String(500))
    table_name = Column(String(100))
    arrived_from = Column(String(200))
    br_amount_str = Column(String(200))   # Amount in string format
    br_no_str = Column(String(50))
    abroad_stay = Column(Integer)          # Days abroad
    total_fa_availed = Column(Float, default=0.0)
    actual_br_type = Column(String(20))    # Original type before change
    total_payable = Column(Float, default=0.0)
    _availed_remarks = Column("availed_remarks", Text)


class BrItems(Base):
    """
    Baggage Receipt Items — 30 columns.
    Duty components: BCD + CVD + Cess + HEC = total duty per item.
    """
    __tablename__ = "br_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Parent Reference ──
    br_no = Column(Integer, nullable=False, index=True)
    br_date = Column(Date, nullable=False)
    br_shift = Column(String(20))
    br_type = Column(String(20), nullable=False)

    # ── Item Details ──
    items_sno = Column(Integer, nullable=False)     # Serial number
    items_desc = Column(Text)                        # Description
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))                   # Unit of quantity code
    items_value = Column(Float, default=0.0)

    # ── Duty Components ──
    items_fa = Column(Float, default=0.0)            # Free Allowance
    items_bcd = Column(Float, default=0.0)           # Basic Customs Duty
    items_cvd = Column(Float, default=0.0)           # Countervailing Duty
    items_cess = Column(Float, default=0.0)          # Cess
    items_hec = Column(Float, default=0.0)           # Higher Education Cess
    items_duty = Column(Float, default=0.0)          # Total duty for this item
    items_duty_type = Column(String(50))             # Category code from item_cat_master
    items_category = Column(String(50))              # Under Duty / Free / etc.

    # ── DR Linkage ──
    items_dr_no = Column(Integer, default=0)
    items_dr_year = Column(Integer, default=0)
    items_release_category = Column(String(50))

    # ── Flight & Batch ──
    flight_no = Column(String(20))
    bank_date = Column(Date)
    bank_shift = Column(String(20))
    batch_date = Column(Date)
    batch_shift = Column(String(20))

    # ── Administrative ──
    unique_no = Column(Integer)
    location_code = Column(String(20))
    login_id = Column(String(50))
    entry_deleted = Column(String(5), default="N", index=True)
    bkup_taken = Column(String(5), default="N")
