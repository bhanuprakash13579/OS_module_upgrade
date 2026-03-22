from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base


class LegalStatute(Base):
    __tablename__ = "legal_statutes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    is_prohibited = Column(Boolean, nullable=False, default=False)
    supdt_goods_clause = Column(Text, nullable=False, default="")
    adjn_goods_clause = Column(Text, nullable=False, default="")
    legal_reference = Column(Text, nullable=False, default="")
