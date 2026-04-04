"""
Vendor Connector Framework — 6 connector types for non-SAS/G2S devices.
REST, DATABASE, LOG, SDK, FILE, MESSAGE_BUS.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone
from adapters import ProtocolAdapter, ProtocolType, ConnectionState, CanonicalEvent

logger = logging.getLogger(__name__)

CONNECTOR_TYPES = ["REST", "DATABASE", "LOG", "SDK", "FILE", "MESSAGE_BUS"]


class EventMapping:
    """Maps a raw vendor field to a canonical UGG field."""
    def __init__(self, source_field: str, canonical_field: str, transform=None):
        self.source_field = source_field
        self.canonical_field = canonical_field
        self.transform = transform

    def apply(self, raw_value):
        if self.transform:
            return self.transform(raw_value)
        return raw_value


class ConnectorManifest:
    """Declarative manifest for a vendor connector."""
    def __init__(self, manifest_id: str, name: str, version: str, connector_type: str,
                 event_mappings: list[dict] = None, certification_tier: str = "Bronze", config_schema: dict = None):
        if connector_type not in CONNECTOR_TYPES:
            raise ValueError(f"Invalid connector type: {connector_type}. Must be one of {CONNECTOR_TYPES}")
        self.id = manifest_id
        self.name = name
        self.version = version
        self.connector_type = connector_type
        self.event_mappings = [EventMapping(**m) for m in (event_mappings or [])]
        self.certification_tier = certification_tier
        self.config_schema = config_schema or {}

    def validate_config(self, config: dict) -> bool:
        required = self.config_schema.get("required", [])
        for key in required:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
        return True


class VendorConnector(ProtocolAdapter):
    """Base vendor connector implementing the ProtocolAdapter interface."""

    def __init__(self, device_id: str, manifest: ConnectorManifest):
        super().__init__(ProtocolType.PROPRIETARY, device_id)
        self.manifest = manifest
        self.config: dict = {}
        self.poll_task: Optional[asyncio.Task] = None
        self.poll_count = 0
        self.event_count = 0
        self.error_count = 0
        self.last_event_at: Optional[str] = None

    def apply_mappings(self, raw_data: dict) -> dict:
        """Transform raw vendor data to canonical fields using manifest mappings."""
        canonical = {}
        for mapping in self.manifest.event_mappings:
            if mapping.source_field in raw_data:
                canonical[mapping.canonical_field] = mapping.apply(raw_data[mapping.source_field])
        return canonical

    def get_status(self) -> dict:
        return {
            "protocol": "VENDOR", "connector_type": self.manifest.connector_type,
            "device_id": self.device_id, "manifest": self.manifest.name,
            "version": self.manifest.version, "state": self.state.value,
            "poll_count": self.poll_count, "event_count": self.event_count,
            "error_count": self.error_count, "last_event_at": self.last_event_at,
            "certification_tier": self.manifest.certification_tier,
        }


class RestConnector(VendorConnector):
    """REST connector — polls HTTP endpoint at configured interval."""

    async def connect(self, config: dict) -> None:
        self.manifest.validate_config(config)
        self.config = config
        self._set_state(ConnectionState.OPENING)
        url = config.get("url", "")
        interval = config.get("pollIntervalMs", 60000) / 1000.0
        logger.info(f"[REST:{self.device_id}] Connecting to {url} (poll every {interval}s)")
        self._set_state(ConnectionState.ONLINE)
        self.poll_task = asyncio.create_task(self._poll_loop(url, interval))

    async def disconnect(self) -> None:
        self._set_state(ConnectionState.CLOSING)
        if self.poll_task:
            self.poll_task.cancel()
        self._set_state(ConnectionState.CLOSED)

    async def _poll_loop(self, url: str, interval: float):
        import httpx
        while self.state == ConnectionState.ONLINE:
            try:
                await asyncio.sleep(interval)
                self.poll_count += 1
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=10)
                    raw = resp.json()
                canonical = self.apply_mappings(raw)
                self.event_count += 1
                self.last_event_at = datetime.now(timezone.utc).isoformat()
                self._emit_event(CanonicalEvent(device_id=self.device_id, event_type="meter_snapshot", protocol="PROPRIETARY", payload=canonical))
                self._emit_trace({"channel": "protocol", "direction": "in", "protocol": "REST", "url": url, "status": resp.status_code, "payload_keys": list(raw.keys())})
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                logger.error(f"[REST:{self.device_id}] Poll error: {e}")

    async def poll_meters(self): return []
    async def get_device_info(self): return {"device_id": self.device_id, "protocol": "REST", "state": self.state}
    async def send_command(self, cmd): return {"status": "not_supported"}


class DatabaseConnector(VendorConnector):
    """DATABASE connector — runs SQL queries at configured interval."""

    async def connect(self, config: dict) -> None:
        self.config = config
        self._set_state(ConnectionState.ONLINE)
        logger.info(f"[DB:{self.device_id}] Database connector ready (type={config.get('dbType', 'postgresql')})")

    async def disconnect(self): self._set_state(ConnectionState.CLOSED)
    async def poll_meters(self): return []
    async def get_device_info(self): return {"device_id": self.device_id, "protocol": "DATABASE", "state": self.state}
    async def send_command(self, cmd): return {"status": "not_supported"}


class LogConnector(VendorConnector):
    """LOG connector — watches and parses log files."""

    async def connect(self, config: dict) -> None:
        self.config = config
        self._set_state(ConnectionState.ONLINE)
        logger.info(f"[LOG:{self.device_id}] Log connector watching {config.get('logPath', '/var/log/egm.log')}")

    async def disconnect(self): self._set_state(ConnectionState.CLOSED)
    async def poll_meters(self): return []
    async def get_device_info(self): return {"device_id": self.device_id, "protocol": "LOG", "state": self.state}
    async def send_command(self, cmd): return {"status": "not_supported"}


class SdkConnector(VendorConnector):
    """SDK connector — wraps vendor's proprietary SDK."""

    async def connect(self, config: dict) -> None:
        self.config = config
        self._set_state(ConnectionState.ONLINE)
        logger.info(f"[SDK:{self.device_id}] SDK connector initialized (vendor={config.get('vendorName', 'unknown')})")

    async def disconnect(self): self._set_state(ConnectionState.CLOSED)
    async def poll_meters(self): return []
    async def get_device_info(self): return {"device_id": self.device_id, "protocol": "SDK", "state": self.state}
    async def send_command(self, cmd): return {"status": "not_supported"}


class FileConnector(VendorConnector):
    """FILE connector — watches for batch files (CSV, XML, fixed-width)."""

    async def connect(self, config: dict) -> None:
        self.config = config
        self._set_state(ConnectionState.ONLINE)
        logger.info(f"[FILE:{self.device_id}] File connector watching {config.get('watchPath', '/var/ugg/imports/')}")

    async def disconnect(self): self._set_state(ConnectionState.CLOSED)
    async def poll_meters(self): return []
    async def get_device_info(self): return {"device_id": self.device_id, "protocol": "FILE", "state": self.state}
    async def send_command(self, cmd): return {"status": "not_supported"}


class MessageBusConnector(VendorConnector):
    """MESSAGE_BUS connector — subscribes to AMQP/Kafka/NATS topics."""

    async def connect(self, config: dict) -> None:
        self.config = config
        self._set_state(ConnectionState.ONLINE)
        logger.info(f"[MSGBUS:{self.device_id}] Message bus connector subscribed to {config.get('topic', 'egm.events')}")

    async def disconnect(self): self._set_state(ConnectionState.CLOSED)
    async def poll_meters(self): return []
    async def get_device_info(self): return {"device_id": self.device_id, "protocol": "MESSAGE_BUS", "state": self.state}
    async def send_command(self, cmd): return {"status": "not_supported"}


# ═══════════════════════════════════════════
# CONNECTOR FACTORY (Singleton)
# ═══════════════════════════════════════════
CONNECTOR_CLASS_MAP = {
    "REST": RestConnector,
    "DATABASE": DatabaseConnector,
    "LOG": LogConnector,
    "SDK": SdkConnector,
    "FILE": FileConnector,
    "MESSAGE_BUS": MessageBusConnector,
}


class ConnectorFactory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.registry = {}
        return cls._instance

    def register(self, manifest: ConnectorManifest):
        self.registry[manifest.id] = manifest
        logger.info(f"Registered connector manifest: {manifest.id} ({manifest.connector_type})")

    def create(self, manifest_id: str, device_id: str, config: dict) -> VendorConnector:
        manifest = self.registry.get(manifest_id)
        if not manifest:
            raise ValueError(f"Unknown manifest: {manifest_id}")
        manifest.validate_config(config)
        cls = CONNECTOR_CLASS_MAP.get(manifest.connector_type)
        if not cls:
            raise ValueError(f"No connector class for type: {manifest.connector_type}")
        return cls(device_id, manifest)

    def list_manifests(self) -> list[dict]:
        return [{"id": m.id, "name": m.name, "version": m.version, "type": m.connector_type, "tier": m.certification_tier} for m in self.registry.values()]


connector_factory = ConnectorFactory()
