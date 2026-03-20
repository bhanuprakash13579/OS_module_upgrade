"""
Warehouse Models.
Tables: wh_master, wh_items, wh_release, wh_location_change,
        valuables_master, valuables_items
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text
from app.database import Base


class WhMaster(Base):
    """General Warehouse — Master."""
    __tablename__ = "wh_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, nullable=False, index=True)
    wh_date = Column(Date, nullable=False)
    dr_type = Column(String(20))           # Bagg / AIU / MHB
    dr_no = Column(Integer)
    os_no = Column(String(20))
    passport_no = Column(String(50), index=True)
    pax_name = Column(String(200))
    closure_remarks = Column(Text)
    storage_location = Column(String(200))
    storage_rack_no = Column(String(50))
    storage_row_no = Column(String(50))
    unique_no = Column(Integer)
    location_code = Column(String(20))


class WhItems(Base):
    """General Warehouse — Items with qty tracking."""
    __tablename__ = "wh_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, nullable=False, index=True)
    wh_date = Column(Date)
    dr_type = Column(String(20))
    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    items_value = Column(Float, default=0.0)
    warehoused_qty = Column(Float, default=0.0)
    balance_qty = Column(Float, default=0.0)
    released_qty = Column(Float, default=0.0)
    unique_no = Column(Integer)
    location_code = Column(String(20))


class WhRelease(Base):
    """Warehouse Releases — partial/full."""
    __tablename__ = "wh_release"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, nullable=False, index=True)
    wh_date = Column(Date)
    wh_release_no = Column(Integer)
    release_date = Column(Date)
    released_qty = Column(Float, default=0.0)
    items_sno = Column(Integer)
    unique_no = Column(Integer)


class WhLocationChange(Base):
    """Tracks movements within the warehouse."""
    __tablename__ = "wh_location_change"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, index=True)
    wh_date = Column(Date)
    old_location = Column(String(200))
    new_location = Column(String(200))
    old_rack_no = Column(String(50))
    new_rack_no = Column(String(50))
    old_row_no = Column(String(50))
    new_row_no = Column(String(50))
    change_date = Column(Date)
    changed_by = Column(String(50))
    unique_no = Column(Integer)
    location_code = Column(String(20))


class ValuablesMaster(Base):
    """Valuable Goods Warehouse — same structure as wh_master."""
    __tablename__ = "valuables_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, nullable=False, index=True)
    wh_date = Column(Date, nullable=False)
    dr_type = Column(String(20))
    dr_no = Column(Integer)
    os_no = Column(String(20))
    passport_no = Column(String(50), index=True)
    pax_name = Column(String(200))
    closure_remarks = Column(Text)
    storage_location = Column(String(200))
    storage_rack_no = Column(String(50))
    storage_row_no = Column(String(50))
    unique_no = Column(Integer)
    location_code = Column(String(20))


class ValuablesItems(Base):
    """Valuable Goods Warehouse — Items."""
    __tablename__ = "valuables_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, nullable=False, index=True)
    wh_date = Column(Date)
    dr_type = Column(String(20))
    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    items_value = Column(Float, default=0.0)
    warehoused_qty = Column(Float, default=0.0)
    balance_qty = Column(Float, default=0.0)
    released_qty = Column(Float, default=0.0)
    unique_no = Column(Integer)
    location_code = Column(String(20))
