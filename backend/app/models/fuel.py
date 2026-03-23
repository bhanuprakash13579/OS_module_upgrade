"""
Fuel Duty Receipt Model.
Table: fuel_master (24 columns)
"""
from sqlalchemy import Column, String, Float, Date, Integer
from app.database import Base


class FuelMaster(Base):
    """
    Fuel Duty Receipts. 24 columns.
    Note: entry_deleted can be 'D' (special fuel delete) or 'Y' (standard).
    """
    __tablename__ = "fuel_master"

    id = Column(Integer, primary_key=True, autoincrement=True)

    br_no = Column(Integer, nullable=False, index=True)
    br_date = Column(Date, nullable=False)
    br_type = Column(String(20), default="Fuel")

    airlines_name = Column(String(200))
    aircraft_no = Column(String(50))
    fuel_charges_paid = Column(Float, default=0.0)

    total_duty_amount = Column(Float, default=0.0)
    rf_amount = Column(Float, default=0.0)
    pp_amount = Column(Float, default=0.0)
    ref_amount = Column(Float, default=0.0)
    wh_amount = Column(Float, default=0.0)
    other_amount = Column(Float, default=0.0)
    br_amount = Column(Float, default=0.0)

    challan_no = Column(String(50))
    bank_date = Column(Date)
    bank_shift = Column(String(20))
    batch_date = Column(Date)
    batch_shift = Column(String(20))

    unique_no = Column(Integer)
    location_code = Column(String(20))
    login_id = Column(String(50))
    entry_deleted = Column(String(5), default="N", index=True)  # N / Y / D
    br_printed = Column(String(5), default="N")
    assessable_value = Column(Float, default=0.0)
