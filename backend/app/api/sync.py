from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.audit import AuditEvent
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/sync", tags=["sync"])

class SyncPayload(BaseModel):
    last_sync_timestamp: str

class SyncEventResponse(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    action: str
    payload: Dict[str, Any]
    node_id: str
    timestamp: datetime

@router.get("/pull", response_model=List[SyncEventResponse])
def pull_events(last_sync: str, db: Session = Depends(get_db)):
    """
    SDO Clients hit this endpoint to pull all `AuditEvent`s that occurred 
    since their last known sync timestamp.
    """
    try:
        dt = datetime.fromisoformat(last_sync)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO timestamp format")

    events = db.query(AuditEvent).filter(AuditEvent.timestamp > dt).order_by(AuditEvent.timestamp.asc()).all()
    
    return [
        SyncEventResponse(
            id=e.id,
            entity_id=e.entity_id,
            entity_type=e.entity_type,
            action=e.action,
            payload=e.payload,
            node_id=e.node_id,
            timestamp=e.timestamp
        ) for e in events
    ]

@router.post("/push")
def push_events(events: List[SyncEventResponse], db: Session = Depends(get_db)):
    """
    SDO Clients hit this endpoint to push their locally-generated 
    append-only events to the Primary Server.
    """
    # Note: In a real conflict-free engine, we would verify signatures and blindly append
    # or handle the logical merge operations here.
    
    saved = 0
    for evt in events:
        # Check if already exists (idempotency)
        existing = db.query(AuditEvent).filter(AuditEvent.id == evt.id).first()
        if not existing:
            new_evt = AuditEvent(
                id=evt.id,
                entity_id=evt.entity_id,
                entity_type=evt.entity_type,
                action=evt.action,
                payload=evt.payload,
                node_id=evt.node_id,
                timestamp=evt.timestamp
            )
            db.add(new_evt)
            saved += 1
            
    db.commit()
    return {"status": "success", "events_merged": saved}
