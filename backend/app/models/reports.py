"""
Report Data Staging Models.
Tables: os_rpt_master/items, wh_gnl_rpt_master/items, wh_val_rpt_master/items
These tables stage data before report generation.
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text
from app.database import Base


class OsRptMaster(Base):
    """O.S. Report data staging — master."""
    __tablename__ = "os_rpt_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    os_year = Column(Integer)
    pax_name = Column(String(200))
    passport_no = Column(String(50))
    flight_no = Column(String(20))
    flight_date = Column(Date)
    total_items_value = Column(Float)
    total_duty_amount = Column(Float)
    rf_amount = Column(Float)
    pp_amount = Column(Float)
    ref_amount = Column(Float)
    br_amount = Column(Float)
    adjudication_date = Column(Date)
    adj_offr_name = Column(String(200))
    online_adjn = Column(String(5))
    location_code = Column(String(20))


class OsRptItems(Base):
    """O.S. Report data staging — items."""
    __tablename__ = "os_rpt_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    os_date = Column(Date)
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    items_duty = Column(Float)
    items_category = Column(String(50))
    items_release_category = Column(String(50))
    location_code = Column(String(20))


class WhGnlRptMaster(Base):
    """General Warehouse report staging — master."""
    __tablename__ = "wh_gnl_rpt_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, index=True)
    wh_date = Column(Date)
    dr_type = Column(String(20))
    dr_no = Column(Integer)
    passport_no = Column(String(50))
    pax_name = Column(String(200))
    closure_remarks = Column(Text)
    storage_location = Column(String(200))
    location_code = Column(String(20))


class WhGnlRptItems(Base):
    """General Warehouse report staging — items."""
    __tablename__ = "wh_gnl_rpt_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, index=True)
    wh_date = Column(Date)
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    warehoused_qty = Column(Float)
    balance_qty = Column(Float)
    released_qty = Column(Float)
    location_code = Column(String(20))


class WhValRptMaster(Base):
    """Valuables Warehouse report staging — master."""
    __tablename__ = "wh_val_rpt_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, index=True)
    wh_date = Column(Date)
    dr_type = Column(String(20))
    dr_no = Column(Integer)
    passport_no = Column(String(50))
    pax_name = Column(String(200))
    closure_remarks = Column(Text)
    storage_location = Column(String(200))
    location_code = Column(String(20))


class WhValRptItems(Base):
    """Valuables Warehouse report staging — items."""
    __tablename__ = "wh_val_rpt_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wh_no = Column(Integer, index=True)
    wh_date = Column(Date)
    items_sno = Column(Integer)
    items_desc = Column(Text)
    items_qty = Column(Float)
    items_uqc = Column(String(20))
    items_value = Column(Float)
    warehoused_qty = Column(Float)
    balance_qty = Column(Float)
    released_qty = Column(Float)
    location_code = Column(String(20))
