"""
Master Data Models — ALL 9 master tables.
Tables: dc_master, airlines_mast, arrival_flight_master, airport_master,
        nationality_master, port_master, item_cat_master, duty_rate_master,
        br_no_limits
"""
from sqlalchemy import Column, String, Float, Date, Integer
from app.database import Base


class DcMaster(Base):
    """Deputy/Assistant Commissioners."""
    __tablename__ = "dc_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dc_code = Column(String(20), unique=True, nullable=False, index=True)
    dc_name = Column(String(200), nullable=False)
    dc_status = Column(String(20), default="Active")  # Active / Closed


class AirlinesMast(Base):
    """Airlines Master."""
    __tablename__ = "airlines_mast"

    id = Column(Integer, primary_key=True, autoincrement=True)
    airline_name = Column(String(200), nullable=False)
    airline_code = Column(String(20), unique=True, nullable=False, index=True)


class ArrivalFlightMaster(Base):
    """Flight Numbers linked to airlines."""
    __tablename__ = "arrival_flight_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_no = Column(String(20), nullable=False, index=True)
    airline_code = Column(String(20), nullable=False)  # FK ref to airlines_mast


class AirportMaster(Base):
    """Airport status tracking."""
    __tablename__ = "airport_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    airport_name = Column(String(200))
    airport_status = Column(String(20), default="Active")  # Active / Closed


class NationalityMaster(Base):
    """Nationality lookup. Server-only add capability."""
    __tablename__ = "nationality_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nationality = Column(String(100), unique=True, nullable=False)


class PortMaster(Base):
    """Ports of departure."""
    __tablename__ = "port_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    port_of_departure = Column(String(200), unique=True, nullable=False)


class ItemCatMaster(Base):
    """
    Item Categories with duty rates.
    Deactivate: UPDATE item_cat_master SET active_ind='C' WHERE category_desc='...'
    """
    __tablename__ = "item_cat_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_code = Column(String(20), unique=True, nullable=False, index=True)
    category_desc = Column(String(200), nullable=False)
    active_ind = Column(String(5), default="A")  # A=Active, C=Closed
    dri_cus_10_desc = Column(String(200))
    dri_cus_10_sno = Column(String(20))
    dri_cus_11_desc = Column(String(200))
    dri_cus_11_sno = Column(String(20))
    bcd_adv_rate = Column(Float, default=0.0)     # Basic Customs Duty ad-valorem rate
    cvd_adv_rate = Column(Float, default=0.0)     # Countervailing duty ad-valorem rate
    bcd_specific_rate = Column(Float, default=0.0)
    bcd_specific_uqc = Column(String(20))          # Unit of quantity code
    cvd_specific_rate = Column(Float, default=0.0)
    cvd_specific_uqc = Column(String(20))


class DutyRateMaster(Base):
    """
    Duty rates with date validity ranges.
    Deactivate: UPDATE duty_rate_master SET active_ind='C', to_date=CDATE('...')
    """
    __tablename__ = "duty_rate_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    duty_category = Column(String(50), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date)
    active_ind = Column(String(5), default="A")  # A=Active, C=Closed
    bcd_rate = Column(Float, default=0.0)
    cvd_rate = Column(Float, default=0.0)


class BrNoLimits(Base):
    """
    B.R. Number Series limits per type.
    Controls which BR number ranges each type can use.
    """
    __tablename__ = "br_no_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    br_type = Column(String(20), nullable=False)
    br_series_from = Column(Integer, nullable=False)
    br_series_to = Column(Integer, nullable=False)
