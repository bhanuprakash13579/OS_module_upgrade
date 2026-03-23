import time
import requests
import threading
import logging
from typing import Optional
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.audit import AuditEvent
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SyncWorker:
    """
    Background worker that runs on SDO Client machines.
    It periodically polls the discovered COPS Primary Server to exchange AuditEvents.
    """
    def __init__(self, primary_url: str, node_id: str, poll_interval: int = 5):
        self.primary_url = primary_url
        self.node_id = node_id
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def get_last_sync_timestamp(self, db: Session) -> str:
        # Get the timestamp of the latest event we've seen from the server
        latest = db.query(AuditEvent).filter(AuditEvent.node_id != self.node_id).order_by(AuditEvent.timestamp.desc()).first()
        if latest:
            return latest.timestamp.isoformat()
        return "1970-01-01T00:00:00+00:00"

    def get_unsynced_local_events(self, db: Session):
        # In a real payload we'd track a "synced_to_server" flag on AuditEvent.
        # For demonstration of the Conflict-Free architecture, we select local node events.
        return db.query(AuditEvent).filter(AuditEvent.node_id == self.node_id).all()

    def sync_iteration(self):
        db = SessionLocal()
        try:
            # 1. PUSH local changes to Server
            local_events = self.get_unsynced_local_events(db)
            if local_events:
                payload = [
                    {
                        "id": e.id,
                        "entity_id": e.entity_id,
                        "entity_type": e.entity_type,
                        "action": e.action,
                        "payload": e.payload,
                        "node_id": e.node_id,
                        "timestamp": e.timestamp.isoformat()
                    } for e in local_events
                ]
                try:
                    res = requests.post(f"{self.primary_url}/api/sync/push", json=payload, timeout=5)
                    if res.status_code == 200:
                        logger.info(f"Pushed {len(local_events)} events to Primary Server.")
                        # (Here we would mark them as synced)
                except Exception as e:
                    logger.debug(f"Push to server failed (expected if offline): {e}")

            # 2. PULL remote changes from Server
            last_sync = self.get_last_sync_timestamp(db)
            try:
                res = requests.get(f"{self.primary_url}/api/sync/pull?last_sync={last_sync}", timeout=5)
                if res.status_code == 200:
                    remote_events = res.json()
                    new_events = 0
                    # Bulk-check which IDs already exist — one query instead of one per event
                    incoming_ids = [evt["id"] for evt in remote_events]
                    existing_ids = {
                        row[0] for row in
                        db.query(AuditEvent.id).filter(AuditEvent.id.in_(incoming_ids)).all()
                    } if incoming_ids else set()
                    for evt in remote_events:
                        if evt["id"] not in existing_ids:
                            new_evt = AuditEvent(
                                id=evt["id"],
                                entity_id=evt["entity_id"],
                                entity_type=evt["entity_type"],
                                action=evt["action"],
                                payload=evt["payload"],
                                node_id=evt["node_id"],
                                timestamp=datetime.fromisoformat(evt["timestamp"])
                            )
                            db.add(new_evt)
                            new_events += 1
                    if new_events > 0:
                        db.commit()
                        logger.info(f"Pulled {new_events} new events from Primary Server.")
            except Exception as e:
                logger.debug(f"Pull from server failed (expected if offline): {e}")

        finally:
            db.close()

    def _run(self):
        logger.info(f"SyncWorker started against {self.primary_url}")
        while not self._stop_event.is_set():
            self.sync_iteration()
            time.sleep(self.poll_interval)

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        logger.info("SyncWorker stopped.")
