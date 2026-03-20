"""
Audit / Delete-Tracking / Temp Staging Models.
22 tables for complete data lifecycle tracking — ZERO data loss guarantee.
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from typing import Any
from app.database import Base


# ═══════════════════════════════════════════════════════════════════
# Append-Only Replication / Sync Events (Phase 7)
# ═══════════════════════════════════════════════════════════════════

class AuditEvent(Base):
    """Immutable sequence log used for P2P/LAN replication and syncing."""
    __tablename__ = "audit_events"

    id = Column(String(50), primary_key=True)
    entity_id = Column(String(50), index=True)
    entity_type = Column(String(50), index=True)
    action = Column(String(20))     # CREATE, UPDATE, DELETE
    payload = Column(JSON)          # The JSON blob of the row
    node_id = Column(String(50))    # Who authored the change
    timestamp = Column(DateTime(timezone=True), index=True)

# ═══════════════════════════════════════════════════════════════════
# COPS (Offence) Delete/Temp Tables
# ═══════════════════════════════════════════════════════════════════

class CopsMasterDeleted(Base):
    """Tracks deleted offence cases. SELECT * FROM cops_master → here before delete."""
    __tablename__ = "cops_master_deleted"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    location_code = Column(String(20))
    booked_by = Column(String(200))
    pax_name = Column(String(200))
    pax_nationality = Column(String(100))
    passport_no = Column(String(50))
    passport_date = Column(Date)
    pax_address1 = Column(String(300))
    pax_address2 = Column(String(300))
    pax_address3 = Column(String(300))
    pax_date_of_birth = Column(Date)
    pax_status = Column(String(50))
    residence_at = Column(String(200))
    country_of_departure = Column(String(200))
    flight_no = Column(String(20))
    flight_date = Column(Date)
    total_items = Column(Integer)
    total_items_value = Column(Float)
    dutiable_value = Column(Float)
    redeemed_value = Column(Float)
    re_export_value = Column(Float)
    confiscated_value = Column(Float)
    total_duty_amount = Column(Float)
    rf_amount = Column(Float)
    pp_amount = Column(Float)
    ref_amount = Column(Float)
    br_amount = Column(Float)
    wh_amount = Column(Float)
    other_amount = Column(Float)
    total_payable = Column(Float)
    br_no_str = Column(String(50))
    br_no_num = Column(Float)
    br_date_str = Column(String(60))
    br_amount_str = Column(String(50))
    adjudication_date = Column(Date)
    adj_offr_name = Column(String(200))
    adj_offr_designation = Column(String(200))
    adjn_offr_remarks = Column(Text)
    adjn_offr_remarks1 = Column(Text)
    online_adjn = Column(String(5))
    os_printed = Column(String(5))
    os_category = Column(String(50))
    online_os = Column(String(5))
    unique_no = Column(Integer)
    entry_deleted = Column(String(5))
    bkup_taken = Column(String(5))
    detained_by = Column(String(200))
    seal_no = Column(String(50))
    nationality = Column(String(100))
    seizure_date = Column(Date)
    pax_name_modified_by_vig = Column(String(200))
    pax_image_filename = Column(String(200))
    total_fa_value = Column(Float)
    dr_no = Column(String(20))
    dr_year = Column(Integer)
    total_drs = Column(Integer)
    previous_os_details = Column(Text)
    previous_visits = Column(Text)
    father_name = Column(String(200))
    old_passport_no = Column(String(50))
    total_pkgs = Column(Integer)
    supdt_remarks2 = Column(String(200))
    closure_ind = Column(String(5))


class CopsItemsDeleted(Base):
    """Tracks deleted offence items."""
    __tablename__ = "cops_items_deleted"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    location_code = Column(String(20))
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    items_fa = Column(Float)
    items_duty = Column(Float)
    items_duty_type = Column(String(50))
    items_category = Column(String(50))
    items_release_category = Column(String(50))
    items_sub_category = Column(String(50))
    items_dr_no = Column(Integer)
    items_dr_year = Column(Integer)
    unique_no = Column(Integer)
    entry_deleted = Column(String(5))
    bkup_taken = Column(String(5))


class CopsMasterTemp(Base):
    """Temp staging during batch operations."""
    __tablename__ = "cops_master_temp"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    location_code = Column(String(20))
    booked_by = Column(String(200))
    pax_name = Column(String(200))
    pax_nationality = Column(String(100))
    passport_no = Column(String(50))
    passport_date = Column(Date)
    pax_address1 = Column(String(300))
    pax_address2 = Column(String(300))
    pax_address3 = Column(String(300))
    pax_date_of_birth = Column(Date)
    pax_status = Column(String(50))
    residence_at = Column(String(200))
    country_of_departure = Column(String(200))
    flight_no = Column(String(20))
    flight_date = Column(Date)
    total_items = Column(Integer)
    total_items_value = Column(Float)
    dutiable_value = Column(Float)
    redeemed_value = Column(Float)
    re_export_value = Column(Float)
    confiscated_value = Column(Float)
    total_duty_amount = Column(Float)
    rf_amount = Column(Float)
    pp_amount = Column(Float)
    ref_amount = Column(Float)
    br_amount = Column(Float)
    wh_amount = Column(Float)
    other_amount = Column(Float)
    total_payable = Column(Float)
    br_no_str = Column(String(50))
    br_no_num = Column(Float)
    br_date_str = Column(String(60))
    br_amount_str = Column(String(50))
    adjudication_date = Column(Date)
    adj_offr_name = Column(String(200))
    adj_offr_designation = Column(String(200))
    adjn_offr_remarks = Column(Text)
    adjn_offr_remarks1 = Column(Text)
    online_adjn = Column(String(5))
    os_printed = Column(String(5))
    os_category = Column(String(50))
    online_os = Column(String(5))
    unique_no = Column(Integer)
    entry_deleted = Column(String(5))
    bkup_taken = Column(String(5))
    detained_by = Column(String(200))
    seal_no = Column(String(50))
    nationality = Column(String(100))
    seizure_date = Column(Date)
    pax_name_modified_by_vig = Column(String(200))
    pax_image_filename = Column(String(200))
    total_fa_value = Column(Float)
    dr_no = Column(String(20))
    dr_year = Column(Integer)
    total_drs = Column(Integer)
    previous_os_details = Column(Text)
    previous_visits = Column(Text)
    father_name = Column(String(200))
    old_passport_no = Column(String(50))
    total_pkgs = Column(Integer)
    supdt_remarks2 = Column(String(200))
    closure_ind = Column(String(5))


class CopsItemsTemp(Base):
    """Temp staging for items during batch ops."""
    __tablename__ = "cops_items_temp"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    location_code = Column(String(20))
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    items_fa = Column(Float)
    items_duty = Column(Float)
    items_duty_type = Column(String(50))
    items_category = Column(String(50))
    items_release_category = Column(String(50))
    items_sub_category = Column(String(50))
    items_dr_no = Column(Integer)
    items_dr_year = Column(Integer)
    unique_no = Column(Integer)
    entry_deleted = Column(String(5))
    bkup_taken = Column(String(5))


# ═══════════════════════════════════════════════════════════════════
# OS Delete Table
# ═══════════════════════════════════════════════════════════════════

class OsMasterDeleted(Base):
    """Tracks deleted OS registrations."""
    __tablename__ = "os_master_deleted"

    id = Column(Integer, primary_key=True, autoincrement=True)
    osdate = Column(Date)
    osnumber = Column(Integer)
    location_code = Column(String(20))


class ItemTransDeleted(Base):
    """Tracks deleted item transactions."""
    __tablename__ = "item_trans_deleted"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_osdate = Column(Date)
    item_os_no = Column(Integer)
    item_lcode = Column(String(20))
    item_no = Column(Integer)
    item_qty = Column(Float)
    item_uqc = Column(String(20))
    item_value = Column(Float)


# ═══════════════════════════════════════════════════════════════════
# B.R. Archive/Tracking Tables
# ═══════════════════════════════════════════════════════════════════

class OldBrMaster(Base):
    """Archives old B.R. data before deletion."""
    __tablename__ = "old_br_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_no = Column(Integer, index=True)
    br_date = Column(Date)
    br_shift = Column(String(20))
    br_type = Column(String(20))
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    flight_no = Column(String(20))
    flight_date = Column(Date)
    total_duty_amount = Column(Float)
    br_amount = Column(Float)
    batch_date = Column(Date)
    batch_shift = Column(String(20))
    dc_code = Column(String(20))
    unique_no = Column(Integer)
    location_code = Column(String(20))
    login_id = Column(String(50))
    entry_deleted = Column(String(5))
    test_field = Column(String(200))    # Extra field in legacy


class OldBrItems(Base):
    """Archives old B.R. items before deletion."""
    __tablename__ = "old_br_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_no = Column(Integer, index=True)
    br_date = Column(Date)
    br_shift = Column(String(20))
    br_type = Column(String(20))
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    items_duty = Column(Float)
    unique_no = Column(Integer)
    location_code = Column(String(20))
    login_id = Column(String(50))
    test_field = Column(String(200))    # Extra field in legacy


class ModifiedMasterBrNos(Base):
    """Tracks B.R. number changes on master."""
    __tablename__ = "modified_master_br_nos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_date = Column(Date)
    batch_shift = Column(String(20))
    br_no = Column(Integer)
    br_date = Column(Date)
    br_type = Column(String(20))
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    new_br_no = Column(Integer)


class ModifiedItemBrNos(Base):
    """Tracks B.R. number changes on items."""
    __tablename__ = "modified_item_br_nos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_date = Column(Date)
    batch_shift = Column(String(20))
    br_no = Column(Integer)
    br_date = Column(Date)
    br_type = Column(String(20))
    items_sno = Column(Integer)
    items_desc = Column(Text)
    new_br_no = Column(Integer)


class DupBRsDeletedInTfr(Base):
    """Records duplicate B.R. removals during transfers."""
    __tablename__ = "dup_brs_deleted_in_tfr"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_date = Column(Date)
    batch_shift = Column(String(20))
    br_nos = Column(Text)


class TypeChangedBrs(Base):
    """Tracks B.R. type changes."""
    __tablename__ = "type_changed_brs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_no = Column(Integer, index=True)
    br_date = Column(Date)
    old_br_type = Column(String(20))
    new_br_type = Column(String(20))
    changed_date = Column(Date)
    changed_by = Column(String(50))


# ═══════════════════════════════════════════════════════════════════
# D.R. Update Tracking
# ═══════════════════════════════════════════════════════════════════

class DrUpdateFromBr(Base):
    """
    Tracks D.R. updates triggered by B.R.
    INSERT INTO dr_update_from_br(sl_no, dr_no, dr_date, br_type, br_no,
                                   br_date, auto_update_remarks)
    """
    __tablename__ = "dr_update_from_br"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sl_no = Column(Integer)
    dr_no = Column(Integer)
    dr_date = Column(Date)
    br_type = Column(String(20))
    br_no = Column(Integer)
    br_date = Column(Date)
    auto_update_remarks = Column(Text)


# ═══════════════════════════════════════════════════════════════════
# Unresolved Offence Staging
# ═══════════════════════════════════════════════════════════════════

class UosMaster(Base):
    """Unresolved offence case staging."""
    __tablename__ = "uos_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    location_code = Column(String(20))
    booked_by = Column(String(200))
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    flight_no = Column(String(20))
    total_items_value = Column(Float)
    total_duty_amount = Column(Float)
    unique_no = Column(Integer)
    entry_deleted = Column(String(5))
    bkup_taken = Column(String(5))


class UosItems(Base):
    """Unresolved offence item staging."""
    __tablename__ = "uos_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    location_code = Column(String(20))
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    items_fa = Column(Float)
    items_duty = Column(Float)
    items_duty_type = Column(String(50))
    items_category = Column(String(50))
    items_release_category = Column(String(50))
    items_sub_category = Column(String(50))
    items_dr_no = Column(Integer)
    items_dr_year = Column(Integer)
    unique_no = Column(Integer)
    entry_deleted = Column(String(5))
    bkup_taken = Column(String(5))


# ═══════════════════════════════════════════════════════════════════
# Valuation Copies
# ═══════════════════════════════════════════════════════════════════

class ValuationMaster(Base):
    """Valuation copy from DR — SELECT * FROM dr_master."""
    __tablename__ = "valuation_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dr_no = Column(Integer, index=True)
    dr_date = Column(Date)
    dr_year = Column(Integer)
    dr_type = Column(String(20))
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    total_items_value = Column(Float)
    unique_no = Column(Integer)
    location_code = Column(String(20))


class ValuationItems(Base):
    """Valuation copy from DR items."""
    __tablename__ = "valuation_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dr_no = Column(Integer, index=True)
    dr_date = Column(Date)
    dr_type = Column(String(20))
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    items_fa = Column(Float)
    items_release_category = Column(String(50))
    unique_no = Column(Integer)
    location_code = Column(String(20))


# ═══════════════════════════════════════════════════════════════════
# Miscellaneous Tracking Tables
# ═══════════════════════════════════════════════════════════════════

class ShortCollectionMaster(Base):
    """Short collection tracking (duty rate 38.50% cases)."""
    __tablename__ = "short_collection_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_no = Column(Integer)
    br_date = Column(Date)
    br_type = Column(String(20))
    short_amount = Column(Float)
    remarks = Column(Text)


class DriMaster(Base):
    """DRI (Directorate of Revenue Intelligence) records."""
    __tablename__ = "dri_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dr_no = Column(Integer, index=True)
    dr_date = Column(Date)
    dr_type = Column(String(20))
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    total_items_value = Column(Float)
    unique_no = Column(Integer)
    location_code = Column(String(20))


class FltManifests(Base):
    """Flight manifest data."""
    __tablename__ = "flt_manifests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_no = Column(String(20), index=True)
    flight_date = Column(Date)
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    nationality = Column(String(100))
    seat_no = Column(String(20))


class BrPrintGaps(Base):
    """Tracks gaps in B.R. number sequences."""
    __tablename__ = "br_print_gaps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_type = Column(String(20))
    gap_from = Column(Integer)
    gap_to = Column(Integer)
    batch_date = Column(Date)
    batch_shift = Column(String(20))
    remarks = Column(Text)


# ═══════════════════════════════════════════════════════════════════
# Reconciliation Remark Tables (6 tables)
# ═══════════════════════════════════════════════════════════════════

class OsItemCompareRemarks(Base):
    __tablename__ = "os_item_compare_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20))
    os_date = Column(Date)
    remark_type = Column(String(100))
    remarks = Column(Text)


class ValItemsReconsRemarks(Base):
    __tablename__ = "val_items_recons_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_no = Column(String(50))
    ref_date = Column(Date)
    remark_type = Column(String(100))
    remarks = Column(Text)


class ValMasterReconsRemarks(Base):
    __tablename__ = "val_master_recons_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_no = Column(String(50))
    ref_date = Column(Date)
    remark_type = Column(String(100))
    remarks = Column(Text)


class ValuablesItemsReconsRemarks(Base):
    __tablename__ = "valuables_items_recons_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_no = Column(String(50))
    ref_date = Column(Date)
    remark_type = Column(String(100))
    remarks = Column(Text)


class WhItemsReconsRemarks(Base):
    __tablename__ = "wh_items_recons_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_no = Column(String(50))
    ref_date = Column(Date)
    remark_type = Column(String(100))
    remarks = Column(Text)


class WhMasterReconsRemarks(Base):
    __tablename__ = "wh_master_recons_remarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_no = Column(String(50))
    ref_date = Column(Date)
    remark_type = Column(String(100))
    remarks = Column(Text)
