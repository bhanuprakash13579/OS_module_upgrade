"""
Network security models.
Table: allowed_devices — admin-managed IP/MAC whitelist for LAN access control.
"""
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, Date
from app.database import Base


class AllowedDevice(Base):
    """
    IP/MAC whitelist for Production mode LAN access control.
    Enforcement is by IP address (MAC is stored for admin identification only).
    127.0.0.1 and ::1 (the master terminal) are always allowed regardless of this table.
    """
    __tablename__ = "allowed_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(200), nullable=False)          # "Counter 1 - Immigration"
    ip_address = Column(String(50), nullable=True)       # enforced; nullable for DHCP
    mac_address = Column(String(50), nullable=True)      # display only (L2, not enforceable at L3)
    hostname = Column(String(200), nullable=True)        # display only
    added_by = Column(String(100), default="sysadmin")
    added_on = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
