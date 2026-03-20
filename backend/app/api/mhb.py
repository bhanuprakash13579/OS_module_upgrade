from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.auth import User
from app.services.auth import get_current_active_user
from app.models.mhb import MhbMaster
import app.schemas.mhb as schemas

router = APIRouter()

@router.post("/", response_model=schemas.MhbMasterOut)
def create_mhb(data: schemas.MhbCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    max_no = db.query(func.max(MhbMaster.mhb_no)).filter(MhbMaster.mhb_year == date.today().year).scalar()
    new_no = (max_no or 0) + 1
    
    obj = MhbMaster(
        mhb_no=new_no,
        mhb_date=date.today(),
        mhb_year=date.today().year,
        login_id=current_user.user_id,
        closure_ind="N",
        **data.model_dump()
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
