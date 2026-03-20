"""
MHB (Mahazar/Harbor) Models.
Tables: mahazar_master, mahazar_items, mhb_master, mhb_items
"""
from sqlalchemy import Column, String, Float, Date, Integer, Text
from app.database import Base


class MahazarMaster(Base):
    """Mahazar / Forwarding Memo — Master."""
    __tablename__ = "mahazar_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    system_reference_no = Column(String(50))
    detaining_date = Column(Date)
    dr_type = Column(String(20))
    location_code = Column(String(20))
    detained_by = Column(String(200))
    seal_no = Column(String(50))
    closure_ind = Column(String(5))
    closure_remarks = Column(Text)
    warehouse_no = Column(String(50))
    fm_printed = Column(String(5), default="N")
    unique_no = Column(Integer)


class MahazarItems(Base):
    """Mahazar — Items."""
    __tablename__ = "mahazar_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    os_no = Column(String(20), index=True)
    system_reference_no = Column(String(50))
    dr_type = Column(String(20))
    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    items_value = Column(Float, default=0.0)
    receipt_by_who = Column(String(5))
    item_closure_remarks = Column(Text)
    unique_no = Column(Integer)


class MhbMaster(Base):
    """MHB Receipt — Master."""
    __tablename__ = "mhb_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mhb_no = Column(Integer, nullable=False, index=True)
    mhb_year = Column(Integer)
    dr_no = Column(Integer)
    dr_date = Column(Date)
    aoc_no = Column(String(50))                # AOC tag number
    passport_no = Column(String(50), index=True)
    pax_name = Column(String(200))
    closure_ind = Column(String(5))
    closure_remarks = Column(Text)
    wh_no = Column(Integer)
    unique_no = Column(Integer)
    location_code = Column(String(20))


class MhbItems(Base):
    """MHB Receipt — Items."""
    __tablename__ = "mhb_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mhb_no = Column(Integer, nullable=False, index=True)
    dr_no = Column(Integer)
    aoc_no = Column(String(50))
    items_sno = Column(Integer, nullable=False)
    items_desc = Column(Text)
    items_qty = Column(Float, default=0.0)
    items_uqc = Column(String(20))
    items_value = Column(Float, default=0.0)
    receipt_by_who = Column(String(5))
    unique_no = Column(Integer)
