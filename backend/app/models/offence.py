"""
Offence/Seizure Case Models.
Tables: cops_master (65+ cols), cops_items (23 cols), os_master, item_trans
"""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, Text, Index
from app.database import Base


class CopsMaster(Base):
    """
    COPS — Offence/Seizure Cases (Main).
    Includes original legacy fields + new fields added in modernization.
    """
    __tablename__ = "cops_master"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Identifiers ──
    os_no = Column(String(20), nullable=False, index=True)
    os_date = Column(Date, nullable=False, index=True)
    os_year = Column(Integer)
    location_code = Column(String(20))
    shift = Column(String(20))
    detention_date = Column(Date)
    case_type = Column(String(100))

    # ── Booking Officer ──
    booked_by = Column(String(200))

    # ── Passenger Details ──
    pax_name = Column(String(200))
    pax_name_modified_by_vig = Column(String(200))  # Legacy: name correction by vigilance
    pax_nationality = Column(String(100))
    passport_no = Column(String(50), index=True)
    passport_date = Column(Date)
    pp_issue_place = Column(String(200))            # Legacy: passport_issue_place
    pax_address1 = Column(String(300))
    pax_address2 = Column(String(300))
    pax_address3 = Column(String(300))
    pax_date_of_birth = Column(Date)
    pax_status = Column(String(50))
    residence_at = Column(String(200))
    country_of_departure = Column(String(200))      # Arrived From
    port_of_dep_dest = Column(String(200))          # Legacy: port_of_departure
    date_of_departure = Column(String(50))          # N.A. or date string
    stay_abroad_days = Column(Integer)              # Legacy: abroad_stay
    pax_image_filename = Column(String(200))        # Legacy: pax photo filename

    # ── Flight ──
    flight_no = Column(String(50), index=True)
    flight_date = Column(Date)

    # ── Item Summary ──
    total_items = Column(Integer, default=0)
    total_items_value = Column(Float, default=0.0)
    total_fa_value = Column(Float, default=0.0)     # Legacy: Total Free Allowance value
    dutiable_value = Column(Float, default=0.0)     # Set by adjudicator: dutiable portion
    redeemed_value = Column(Float, default=0.0)     # Set by adjudicator: redeemed on RF
    re_export_value = Column(Float, default=0.0)    # Set by adjudicator: re-exported
    confiscated_value = Column(Float, default=0.0)  # Set by adjudicator: confiscated

    # ── Financial (Adjudication amounts) ──
    total_duty_amount = Column(Float, default=0.0)  # Customs Duty (calc from items by SDO)
    rf_amount = Column(Float, default=0.0)          # Redemption Fine (set by adjudicator)
    pp_amount = Column(Float, default=0.0)          # Personal Penalty (set by adjudicator)
    ref_amount = Column(Float, default=0.0)         # Re-Export Fine (set by adjudicator)
    br_amount = Column(Float, default=0.0)          # Other Taxes (new — set by adjudicator)
    wh_amount = Column(Float, default=0.0)          # Legacy: Warehouse charges
    other_amount = Column(Float, default=0.0)       # Legacy: Other charges
    total_payable = Column(Float, default=0.0)      # duty + rf + ref + pp + br

    # ── B.R. Linkage (Legacy) ──
    br_no_str = Column(String(50))                  # Legacy: BR number as string
    br_no_num = Column(Float)                       # Legacy: BR number as number
    br_date_str = Column(String(60))                # Legacy: BR date
    br_amount_str = Column(String(50))              # Legacy: BR amount as string

    # ── Status ──
    is_legacy = Column(String(1), default="N")  # 'Y' = imported from old VB6 module; excluded from pending list
    is_draft = Column(String(5), default="N")
    os_printed = Column(String(5), default="N")
    os_category = Column(String(50))                # Legacy: goods category (elec_goods, gold, etc.)
    online_os = Column(String(5))                   # Legacy: Y/N
    adjudication_date = Column(Date)
    adjudication_time = Column(DateTime)
    adj_offr_name = Column(String(200))
    adj_offr_designation = Column(String(200))
    adjn_offr_remarks = Column(Text)                # Max 700 characters enforced in API
    adjn_offr_remarks1 = Column(Text)               # Legacy: extra adjudication remarks
    online_adjn = Column(String(5))                 # Y/N

    # ── Administrative ──
    unique_no = Column(Integer)
    entry_deleted = Column(String(5), default="N")
    bkup_taken = Column(String(5), default="N")
    # Soft-delete audit — who deleted, why, and when
    deleted_by = Column(String(100))        # user_id of the DC/AC who deleted
    deleted_reason = Column(Text)           # mandatory reason (min 5 chars)
    deleted_on = Column(Date)               # date of deletion

    # ── Detention Details ──
    detained_by = Column(String(200))
    seal_no = Column(String(50))
    nationality = Column(String(100))
    seizure_date = Column(Date)                     # Legacy: date of seizure

    # ── DR Linkage ──
    dr_no = Column(String(20))
    dr_year = Column(Integer)
    total_drs = Column(Integer, default=0)

    # ── Previous Cases ──
    previous_os_details = Column(Text)
    previous_visits = Column(Text)
    father_name = Column(String(200))
    old_passport_no = Column(String(50))
    total_pkgs = Column(Integer, default=0)
    supdts_remarks = Column(Text)                   # Legacy: supdt_remarks1
    supdt_remarks2 = Column(String(200))            # Legacy: extra supdt remarks
    closure_ind = Column(String(5))

    # ── Post-Adjudication Metadata (BR / DR receipts) ──
    # Set by SDO AFTER the adjudication order is issued.
    # Never auto-filled; never modified by the adjudication workflow.
    post_adj_br_entries = Column(Text, nullable=True)   # JSON: [{"no":"123","date":"2026-03-15"},…]
    post_adj_dr_no      = Column(String(50), nullable=True)
    post_adj_dr_date    = Column(Date, nullable=True)

    # ── Workflow Exits (Quash/Reject) ──
    quashed = Column(String(1), default='N')
    quashed_by = Column(String(255))
    quash_reason = Column(Text)
    quash_date = Column(Date)
    rejected = Column(String(1), default='N')
    reject_reason = Column(Text)

    __table_args__ = (
        # Composite lookup: most GET /os/{no}/{year} and adjudication queries use both
        Index('ix_cops_master_os_no_year', 'os_no', 'os_year'),
        # Adjudication list filters: is_draft + entry_deleted are in every list query
        Index('ix_cops_master_draft_deleted', 'entry_deleted', 'is_draft'),
        # Adjudicated cases ordered/filtered by adjudication_date
        Index('ix_cops_master_adjudication_date', 'adjudication_date'),
        # Quashed/rejected filter used in quashed endpoint and pending filter
        Index('ix_cops_master_quashed_rejected', 'quashed', 'rejected'),
    )


class CopsItems(Base):
    """
    COPS — Seized Items. 20 columns.
    """
    __tablename__ = "cops_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    os_no = Column(String(20), nullable=False, index=True)
    os_date = Column(Date, nullable=True)
    os_year = Column(Integer)
    location_code = Column(String(20))

    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    value_per_piece = Column(Float, default=0.0)
    items_value = Column(Float, default=0.0) # Total Value
    items_fa      = Column(Float, default=0.0)
    items_fa_type = Column(String(10), default='value')  # 'value' or 'qty'
    items_fa_qty  = Column(Float, nullable=True)
    items_fa_uqc  = Column(String(20), nullable=True)
    cumulative_duty_rate = Column(Float, default=0.0) # percentage
    items_duty = Column(Float, default=0.0)
    items_duty_type = Column(String(100))
    items_category = Column(String(100))
    items_release_category = Column(String(100))
    items_sub_category = Column(String(100))
    items_dr_no = Column(Integer, default=0)
    items_dr_year = Column(Integer, default=0)

    unique_no = Column(Integer)
    entry_deleted = Column(String(5), default="N")
    bkup_taken = Column(String(5), default="N")

    __table_args__ = (
        Index('ix_cops_items_os_no_year', 'os_no', 'os_year'),
    )


class OsMaster(Base):
    """
    O.S. Registration — Local tracking.
    Minimal table for local OS number assignment.
    """
    __tablename__ = "os_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    osdate = Column(Date, nullable=False)
    osnumber = Column(Integer, nullable=False)
    location_code = Column(String(20))


class ItemTrans(Base):
    """
    Item Transactions — Local.
    """
    __tablename__ = "item_trans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_osdate = Column(Date)
    item_os_no = Column(Integer)
    item_lcode = Column(String(20))
    item_no = Column(Integer)
    item_qty = Column(Float, default=0.0)
    item_uqc = Column(String(20))
    item_value = Column(Float, default=0.0)
