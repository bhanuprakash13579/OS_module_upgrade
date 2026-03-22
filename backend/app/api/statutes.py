from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.statutes import LegalStatute

router = APIRouter(prefix="/statutes", tags=["LegalStatutes"])


class StatuteResponse(BaseModel):
    id: int
    keyword: str
    display_name: str
    is_prohibited: bool
    supdt_goods_clause: str
    adjn_goods_clause: str
    legal_reference: str

    class Config:
        orm_mode = True


class StatuteUpdate(BaseModel):
    display_name: Optional[str] = None
    is_prohibited: Optional[bool] = None
    supdt_goods_clause: Optional[str] = None
    adjn_goods_clause: Optional[str] = None
    legal_reference: Optional[str] = None


class StatuteCreate(BaseModel):
    keyword: str
    display_name: str
    is_prohibited: bool = False
    supdt_goods_clause: str = ""
    adjn_goods_clause: str = ""
    legal_reference: str = ""


@router.get("", response_model=List[StatuteResponse])
def get_all_statutes(db: Session = Depends(get_db)):
    return db.query(LegalStatute).all()


@router.get("/{keyword}", response_model=StatuteResponse)
def get_statute(keyword: str, db: Session = Depends(get_db)):
    statute = db.query(LegalStatute).filter(LegalStatute.keyword == keyword).first()
    if not statute:
        raise HTTPException(status_code=404, detail="Statute not found")
    return statute


@router.post("", response_model=StatuteResponse, status_code=status.HTTP_201_CREATED)
def create_statute(statute_in: StatuteCreate, db: Session = Depends(get_db)):
    existing = db.query(LegalStatute).filter(LegalStatute.keyword == statute_in.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    new_statute = LegalStatute(**statute_in.dict())
    db.add(new_statute)
    db.commit()
    db.refresh(new_statute)
    return new_statute


@router.put("/{keyword}", response_model=StatuteResponse)
def update_statute(keyword: str, update_in: StatuteUpdate, db: Session = Depends(get_db)):
    statute = db.query(LegalStatute).filter(LegalStatute.keyword == keyword).first()
    if not statute:
        raise HTTPException(status_code=404, detail="Statute not found")
    if update_in.display_name is not None:
        statute.display_name = update_in.display_name
    if update_in.is_prohibited is not None:
        statute.is_prohibited = update_in.is_prohibited
    if update_in.supdt_goods_clause is not None:
        statute.supdt_goods_clause = update_in.supdt_goods_clause
    if update_in.adjn_goods_clause is not None:
        statute.adjn_goods_clause = update_in.adjn_goods_clause
    if update_in.legal_reference is not None:
        statute.legal_reference = update_in.legal_reference
    db.commit()
    db.refresh(statute)
    return statute


@router.delete("/{keyword}", status_code=status.HTTP_204_NO_CONTENT)
def delete_statute(keyword: str, db: Session = Depends(get_db)):
    statute = db.query(LegalStatute).filter(LegalStatute.keyword == keyword).first()
    if not statute:
        raise HTTPException(status_code=404, detail="Statute not found")
    db.delete(statute)
    db.commit()
    return None
