from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.audit import AuditEvent
from ..models.auth import User
from ..services.auth import get_current_user
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
def pull_events(last_sync: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    SDO Clients hit this endpoint to pull all `AuditEvent`s that occurred 
    since their last known sync timestamp.
    """
    try:
        dt = datetime.fromisoformat(last_sync)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO timestamp format")

    events = db.query(AuditEvent).filter(AuditEvent.timestamp > dt).order_by(AuditEvent.timestamp.asc()).limit(1000).all()
    
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
def push_events(events: List[SyncEventResponse], db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    SDO Clients hit this endpoint to push their locally-generated 
    append-only events to the Primary Server.
    """
    # Note: In a real conflict-free engine, we would verify signatures and blindly append
    # or handle the logical merge operations here.
    
    if not events:
        return {"status": "success", "events_merged": 0}

    # Bulk-fetch all existing IDs in a single query (idempotency check without N+1)
    incoming_ids = [evt.id for evt in events]
    existing_ids = {
        row.id
        for row in db.query(AuditEvent.id).filter(AuditEvent.id.in_(incoming_ids)).all()
    }

    saved = 0
    for evt in events:
        if evt.id not in existing_ids:
            db.add(AuditEvent(
                id=evt.id,
                entity_id=evt.entity_id,
                entity_type=evt.entity_type,
                action=evt.action,
                payload=evt.payload,
                node_id=evt.node_id,
                timestamp=evt.timestamp,
            ))
            saved += 1

    db.commit()
    return {"status": "success", "events_merged": saved}
