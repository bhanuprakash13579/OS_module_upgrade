"""
Revenue & Challan Models.
Tables: revenue, rev_challans, challan_master
"""
from sqlalchemy import Column, String, Float, Date, Integer
from app.database import Base


class Revenue(Base):
    """
    Revenue tracking — 11 duty categories.
    Validation: Break-up must tally with total.
    """
    __tablename__ = "revenue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rev_date = Column(Date, nullable=False, index=True)
    baggage_duty = Column(Float, default=0.0)
    addl_duty = Column(Float, default=0.0)
    sadcess_duty = Column(Float, default=0.0)
    gold_duty = Column(Float, default=0.0)
    silver_duty = Column(Float, default=0.0)
    rf_amount = Column(Float, default=0.0)
    ref_amount = Column(Float, default=0.0)
    pp_amount = Column(Float, default=0.0)
    misc_amount = Column(Float, default=0.0)
    total_duty = Column(Float, default=0.0)


class RevChallans(Base):
    """Revenue Challans."""
    __tablename__ = "rev_challans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rev_date = Column(Date, nullable=False, index=True)
    challan_no = Column(String(50))


class ChallanMaster(Base):
    """
    Challan Master — SDO-specific.
    INSERT INTO challan_master(batch_date, batch_shift, sdo_code, sdo_name,
                                challan_no, challan_amount)
    """
    __tablename__ = "challan_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_date = Column(Date)
    batch_shift = Column(String(20))
    sdo_code = Column(String(50))
    sdo_name = Column(String(200))
    challan_no = Column(String(50))
    challan_amount = Column(Float, default=0.0)
