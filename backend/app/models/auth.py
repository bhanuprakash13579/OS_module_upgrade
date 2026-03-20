"""
Authentication & User Management Models.
Tables: users, ip_addrs_table
"""
from sqlalchemy import Column, String, Date, Integer
from app.database import Base


class User(Base):
    """
    Legacy table: users
    INSERT INTO Users(user_Name, user_desig, User_ID, User_Pwd,
                      created_by, created_on, user_status, user_role)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(100), nullable=False)
    user_desig = Column(String(100))            # Designation
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    user_pwd = Column(String(255), nullable=False)  # bcrypt hash
    created_by = Column(String(50))
    created_on = Column(Date)
    user_status = Column(String(20), default="ACTIVE")  # ACTIVE / CLOSED
    user_role = Column(String(20), nullable=False)       # SDO | DC | AC
    closed_on = Column(Date)


class IpAddrsTable(Base):
    """
    Legacy table: ip_addrs_table
    Tracks LAN node IP addresses.
    """
    __tablename__ = "ip_addrs_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(50))
    status = Column(String(20), default="Active")  # Active / Closed
