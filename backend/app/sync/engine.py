import sys
import logging
from .discovery import MDNSPublisher
from .worker import SyncWorker

logger = logging.getLogger(__name__)

# Global variable to hold our mDNS publisher or client worker instance
publisher = None
client_worker = None

def init_sync_engine(port: int = 8000, is_primary: bool = True):
    """
    Initializes the LAN Replication Engine.
    If this node is the Primary Server, it broadcasts its presence via mDNS.
    If this node is an SDO Client, it begins scanning for the Primary Server.
    """
    global publisher
    
    if is_primary:
        logger.info("Initializing LAN Sync Engine as PRIMARY SERVER...")
        try:
            publisher = MDNSPublisher(port=port)
            publisher.register()
            logger.info("Server is now discoverable by SDO clients on the LAN.")
        except Exception as e:
            logger.error(f"Failed to initialize Sync Engine Publisher: {e}")
    else:
        logger.info("Initializing LAN Sync Engine as SDO CLIENT...")
        logger.info("Scanning local network for COPS Primary Server...")
        # In a full Zeroconf implementation, we would register a Listener here
        # that looks for "_cops._tcp.local.". For now, we assume discovery happens
        # and hardcode the primary URL resolving from the Local DNS.
        
        global client_worker
        primary_url = "http://cops-server.local:8000"
        node_id = "SDO-NODE-01"
        client_worker = SyncWorker(primary_url=primary_url, node_id=node_id)
        client_worker.start()
        logger.info(f"SDO Client Worker started polling {primary_url}")

def teardown_sync_engine():
    """
    Gracefully shuts down the mDNS broadcast and sync workers.
    """
    global publisher, client_worker
    logger.info("Shutting down LAN Sync Engine...")
    if publisher:
        publisher.unregister()
        publisher = None
    if client_worker:
        client_worker.stop()
        client_worker = None
