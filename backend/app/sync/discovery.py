import socket
import logging
from typing import Optional
from zeroconf import ServiceInfo, Zeroconf

logger = logging.getLogger(__name__)

class MDNSPublisher:
    """
    Publishes this FastAPI server instance on the local network via mDNS.
    This allows COPS-SDO client machines to automatically find the COPS-SERVER.
    """
    def __init__(self, port: int = 8000, service_type: str = "_cops._tcp.local."):
        self.port = port
        self.service_type = service_type
        self.service_name = f"COPS-SERVER.{self.service_type}"
        self.zeroconf: Optional[Zeroconf] = None
        self.info: Optional[ServiceInfo] = None

    def get_local_ip(self) -> str:
        """Determines the local LAN IP address of this machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def register(self):
        """Starts the mDNS advertiser broadcast."""
        try:
            ip_address = self.get_local_ip()
            hostname = socket.gethostname() + ".local."
            
            self.zeroconf = Zeroconf()
            self.info = ServiceInfo(
                self.service_type,
                self.service_name,
                addresses=[socket.inet_aton(ip_address)],
                port=self.port,
                properties={'version': '1.0', 'role': 'SERVER'},
                server=hostname
            )
            
            self.zeroconf.register_service(self.info)
            logger.info(f"mDNS Publisher started: {self.service_name} at {ip_address}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start mDNS publisher: {str(e)}")

    def unregister(self):
        """Stops the mDNS broadcast."""
        if self.zeroconf and self.info:
            self.zeroconf.unregister_service(self.info)
            self.zeroconf.close()
            logger.info("mDNS Publisher stopped.")
